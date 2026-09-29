#!/usr/bin/env python3

from pathlib import Path
import argparse
import errno
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.tex"
TEMPLATES = ROOT / "templates"

# Explicit suffixes keep deletion from removing unrelated files with the same stem.
LATEX_OUTPUT_SUFFIXES = (
    ".aux", ".log", ".out", ".toc", ".lof", ".lot", ".fls", ".fdb_latexmk",
    ".synctex", ".synctex.gz", ".synctex(busy)", ".synctex.gz(busy)",
    ".bbl", ".blg", ".bcf", ".run.xml", ".idx", ".ind", ".ilg",
    ".acn", ".acr", ".alg", ".glg", ".glo", ".gls", ".nav", ".snm", ".vrb",
    ".pdf", ".dvi", ".xdv",
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def natural_key(text: str):
    """Sort 2 before 10, chapter_2 before chapter_10, etc."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", text)
    ]


def chapter_number(path: Path) -> int:
    match = re.fullmatch(r"chapter_(\d+)", path.name)

    if not match:
        raise ValueError(f"Invalid chapter directory: {path}")

    return int(match.group(1))


def latex_path(path: Path) -> str:
    """Convert a repository path to a LaTeX-friendly path."""
    path = path.relative_to(ROOT).with_suffix("")
    return path.as_posix()


# ---------------------------------------------------------------------------
# Discover solutions
# ---------------------------------------------------------------------------

def discover_exercises():
    """
    Expected layouts:

        chapter_1/1.4/2/a.tex
        chapter_1/1.4/2/b.tex
        chapter_1/R/7/f.tex

    Returns roughly:

        {
            1: {
                ("normal", "1.4", "2"): [...],
                ("rudin", "R", "7"): [...]
            }
        }
    """

    chapters = {}

    chapter_dirs = sorted(
        ROOT.glob("chapter_*"),
        key=lambda p: natural_key(p.name),
    )

    for chapter_dir in chapter_dirs:
        if not chapter_dir.is_dir():
            continue

        try:
            chapter = chapter_number(chapter_dir)
        except ValueError:
            continue

        exercises = {}

        for tex in chapter_dir.rglob("*.tex"):
            relative = tex.relative_to(chapter_dir)

            # Expected:
            #
            #   section / exercise / part.tex
            #
            if len(relative.parts) != 3:
                print(
                    f"warning: ignoring unexpected path: "
                    f"{tex.relative_to(ROOT)}",
                    file=sys.stderr,
                )
                continue

            section, exercise, filename = relative.parts
            part = Path(filename).stem

            if section == "R":
                key = ("rudin", section, exercise)
            else:
                key = ("normal", section, exercise)

            exercises.setdefault(key, []).append((part, tex))

        for key in exercises:
            exercises[key].sort(
                key=lambda item: natural_key(item[0])
            )

        chapters[chapter] = exercises

    return chapters


def exercise_sort_key(item):
    (kind, section, exercise), _ = item

    # Put supplementary exercises before Rudin exercises.
    kind_order = 0 if kind == "normal" else 1

    return (
        kind_order,
        natural_key(section),
        natural_key(exercise),
    )


# ---------------------------------------------------------------------------
# Generate main.tex
# ---------------------------------------------------------------------------

def generate_main():
    chapters = discover_exercises()

    lines = [
        r"\documentclass[11pt]{article}",
        "",
        r"\usepackage{subfiles}",
        r"\usepackage{amsmath,amssymb,amsthm}",
        r"\usepackage{geometry}",
        r"\geometry{margin=1in}",
        "",
        r"\newtheorem{lemma}{Lemma}",
        "",
        r"\newcommand{\R}{\mathbb{R}}",
        r"\newcommand{\Q}{\mathbb{Q}}",
        r"\newcommand{\C}{\mathbb{C}}",
        r"\newcommand{\N}{\mathbb{N}}",
        r"\newcommand{\Z}{\mathbb{Z}}",
        "",
        r"\title{Rudin Exercise Solutions}",
        r"\author{}",
        r"\date{}",
        "",
        r"\begin{document}",
        "",
        r"\maketitle",
        r"\tableofcontents",
        r"\newpage",
        "",
    ]

    for chapter in sorted(chapters):
        exercises = chapters[chapter]

        if not exercises:
            continue

        lines.append(rf"\section{{Chapter {chapter}}}")
        lines.append("")

        for (kind, section, exercise), parts in sorted(
            exercises.items(),
            key=exercise_sort_key,
        ):
            if kind == "rudin":
                title = f"Rudin Exercise {chapter}:R{exercise}"
            else:
                title = f"Exercise {section}:{exercise}"

            lines.append(rf"\subsection{{{title}}}")
            lines.append("")

            for part, tex in parts:
                lines.append(rf"\subsubsection*{{({part})}}")
                lines.append(rf"\subfile{{{latex_path(tex)}}}")
                lines.append("")

    lines.extend([
        r"\end{document}",
        "",
    ])

    MAIN.write_text("\n".join(lines), encoding="utf-8")

    print(f"generated: {MAIN.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Create a new solution
# ---------------------------------------------------------------------------

def create_solution(
    chapter: int,
    section: str,
    exercise: str,
    part: str,
    compile_after: bool = False,
    template_file: str = "solution.tex",
):
    """
    Examples:

        python3 generator.py new 1 1.4 2 e

    creates:

        chapter_1/1.4/2/e.tex


        python3 generator.py new 1 R 7 h

    creates:

        chapter_1/R/7/h.tex
    """

    if chapter < 1:
        print("error: chapter must be positive", file=sys.stderr)
        sys.exit(1)

    # Allow either `a` or `a.tex`.
    part = Path(part).stem

    target = (
        ROOT
        / f"chapter_{chapter}"
        / section
        / exercise
        / f"{part}.tex"
    )

    if target.exists():
        print(
            f"error: file already exists: {target.relative_to(ROOT)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Compute path from the new .tex file back to main.tex.
    relative_main = Path(
        os.path.relpath(MAIN, start=target.parent)
    ).as_posix()

    if section == "R":
        description = f"Rudin Exercise {chapter}:R{exercise}({part})"
    else:
        description = f"Exercise {section}:{exercise}({part})"

    template_path = Path(template_file)
    if not template_path.is_absolute():
        template_path = TEMPLATES / template_path

    try:
        template = template_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read solution template {template_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    contents = template.replace("@@MAIN_TEX@@", relative_main).replace(
        "@@DESCRIPTION@@", description
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents, encoding="utf-8")

    print(f"created: {target.relative_to(ROOT)}")

    # Keep main.tex synchronized automatically.
    generate_main()

    if compile_after:
        try:
            subprocess.run(
                [sys.executable, str(ROOT / "build.py"), "one", str(target)],
                cwd=ROOT,
                check=True,
            )
        except OSError as exc:
            print(f"error: cannot run build.py: {exc}", file=sys.stderr)
            sys.exit(1)
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)


# ---------------------------------------------------------------------------
# Delete a solution
# ---------------------------------------------------------------------------

def delete_solution(chapter: int, section: str, exercise: str, part: str):
    """Delete one solution and its generated files, then regenerate main.tex."""
    try:
        if chapter < 1:
            raise ValueError("chapter must be positive")

        if part.endswith(".tex"):
            part = part[:-4]

        for name, value in (("section", section), ("exercise", exercise), ("part", part)):
            if (
                not value
                or value in (".", "..")
                or any(char in value for char in ("/", "\\", "\0"))
            ):
                raise ValueError(f"{name} must be a single nonempty path component")

        target = ROOT / f"chapter_{chapter}" / section / exercise / f"{part}.tex"

        # Reject symlinks in the source and its parent directories.
        for path in (target, *target.parents):
            if path == ROOT:
                break
            if path.is_symlink():
                raise ValueError(f"refusing symlinked solution path: {path.relative_to(ROOT)}")

        if not target.is_file():
            raise ValueError(
                f"solution file is missing or not a regular file: {target.relative_to(ROOT)}"
            )

        output_directory = target.parent / "output"
        if output_directory.is_symlink():
            raise ValueError(
                f"refusing symlinked output directory: {output_directory.relative_to(ROOT)}"
            )
        if output_directory.exists() and not output_directory.is_dir():
            raise ValueError(
                f"output path is not a directory: {output_directory.relative_to(ROOT)}"
            )

        target.unlink()
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"deleted: {target.relative_to(ROOT)}")
    failed = False

    # Also clean artifacts from builds made before the output/ layout was added.
    for output_source in (output_directory / target.name, target):
        for suffix in LATEX_OUTPUT_SUFFIXES:
            output = output_source.with_suffix(suffix)
            try:
                output.unlink()
            except FileNotFoundError:
                continue
            except OSError as exc:
                print(f"error: cannot delete {output.relative_to(ROOT)}: {exc}", file=sys.stderr)
                failed = True
            else:
                print(f"deleted: {output.relative_to(ROOT)}")

    try:
        output_directory.rmdir()
    except FileNotFoundError:
        pass
    except OSError as exc:
        if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
            print(
                f"error: cannot remove directory {output_directory.relative_to(ROOT)}: {exc}",
                file=sys.stderr,
            )
            failed = True
    else:
        print(f"deleted: {output_directory.relative_to(ROOT)}/")

    directory = target.parent
    while directory != ROOT:
        try:
            directory.rmdir()
        except OSError as exc:
            if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                print(
                    f"error: cannot remove directory {directory.relative_to(ROOT)}: {exc}",
                    file=sys.stderr,
                )
                failed = True
            break
        print(f"deleted: {directory.relative_to(ROOT)}/")
        directory = directory.parent

    # The source is gone, so refresh main.tex even if some outputs remain.
    try:
        generate_main()
    except OSError as exc:
        print(f"error: cannot regenerate main.tex: {exc}", file=sys.stderr)
        failed = True

    if failed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate and manage Rudin exercise solutions."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # generate
    subparsers.add_parser(
        "generate",
        help="Generate main.tex without compiling",
    )

    # new
    new = subparsers.add_parser(
        "new",
        help="Create a new exercise solution",
    )

    new.add_argument(
        "chapter",
        type=int,
        help="Chapter number",
    )

    new.add_argument(
        "section",
        help="Section, e.g. 1.4 or R",
    )

    new.add_argument(
        "exercise",
        help="Exercise number, e.g. 2 or 7",
    )

    new.add_argument(
        "part",
        help="Exercise part, e.g. a, b, c",
    )

    new.add_argument(
        "-c",
        "--compile",
        action="store_true",
        help="Compile the newly created file immediately",
    )

    new.add_argument(
        "--template",
        metavar="FILE",
        default="solution.tex",
        help="Template path relative to templates/ or an absolute path (default: solution.tex)",
    )

    # delete
    delete = subparsers.add_parser(
        "delete",
        help="Delete a solution part and its generated files",
        description="Delete a solution part, its generated files, and regenerate main.tex.",
        epilog="Example: python3 generator.py delete 1 1.4 2 d",
    )
    delete.add_argument("chapter", type=int, help="Chapter number")
    delete.add_argument("section", help="Section, e.g. 1.4 or R")
    delete.add_argument("exercise", help="Exercise number, e.g. 2 or 7")
    delete.add_argument("part", help="Exercise part, e.g. d or d.tex")

    args = parser.parse_args()

    if args.command == "generate":
        generate_main()

    elif args.command == "new":
        create_solution(
            chapter=args.chapter,
            section=args.section,
            exercise=args.exercise,
            part=args.part,
            compile_after=args.compile,
            template_file=args.template,
        )

    elif args.command == "delete":
        delete_solution(
            chapter=args.chapter,
            section=args.section,
            exercise=args.exercise,
            part=args.part,
        )


if __name__ == "__main__":
    main()
