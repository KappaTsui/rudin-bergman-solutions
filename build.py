#!/usr/bin/env python3

from pathlib import Path
import argparse
import subprocess
import sys

import generator

ROOT = generator.ROOT
MAIN = generator.MAIN
BUILD = ROOT / "build"


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------

def run_latexmk(target: Path):
    target = target.resolve()
    output_directory = BUILD if target == MAIN else target.parent / "output"
    try:
        if output_directory.is_symlink():
            raise ValueError(f"refusing symlinked output directory: {output_directory}")
        output_directory.mkdir(parents=True, exist_ok=True)
    except (ValueError, OSError) as exc:
        print(f"error: cannot prepare output directory {output_directory}: {exc}", file=sys.stderr)
        sys.exit(1)

    command = [
        "latexmk",
        "-cd",
        "-pdf",
        "-interaction=nonstopmode",
        "-file-line-error",
        f"-outdir={output_directory}",
        str(target),
    ]

    try:
        subprocess.run(
            command,
            cwd=ROOT,
            check=True,
        )

    except FileNotFoundError:
        print(
            "error: latexmk is not installed or not in PATH",
            file=sys.stderr,
        )
        sys.exit(1)

    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


def compile_all():
    generator.generate_main()
    run_latexmk(MAIN)


def compile_one(name: str):
    path = Path(name)

    if path.suffix != ".tex":
        path = path.with_suffix(".tex")

    if not path.is_absolute():
        path = ROOT / path

    path = path.resolve()

    if not path.exists():
        print(
            f"error: file does not exist: {path}",
            file=sys.stderr,
        )
        sys.exit(1)

    run_latexmk(path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compile Rudin exercise solutions.",
        epilog="Use generator.py to generate main.tex or add/delete solutions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "all",
        help="Generate main.tex and compile the complete document into build/",
    )
    one = subparsers.add_parser("one", help="Compile one LaTeX source")
    one.add_argument("file", help="Example: chapter_1/1.4/2/a.tex or main.tex")

    args = parser.parse_args()
    if args.command == "all":
        compile_all()
    elif args.command == "one":
        compile_one(args.file)


if __name__ == "__main__":
    main()
