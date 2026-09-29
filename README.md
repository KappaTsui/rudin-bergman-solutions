# Rudin Exercise Solutions

My solutions to exercises from Walter Rudin's *Principles of Mathematical Analysis* and George M. Bergman's supplementary exercises.

The solutions are written in LaTeX and organized by chapter, section, exercise, and part.

Use `python3 generator.py` with `new`, `delete`, or `generate` to manage solutions and regenerate `main.tex`; new solutions default to `templates/solution.tex`, with `--template lemma.tex` available for numbered lemmas and proofs. Compile with `python3 build.py all` or `python3 build.py one <file>` (requires `latexmk` and `pdflatex`). Main-document output goes to `build/`, and individual solution output goes to the adjacent `output/` directory. Run either script with `--help` for usage.

## References

- Walter Rudin, *Principles of Mathematical Analysis*, 3rd ed.
- George M. Bergman, *Supplements to the Exercises in Chapters 1–7 of Walter Rudin's Principles of Mathematical Analysis, Third Edition*. [Available online](https://math.berkeley.edu/~gbergman/ug.hndts/#Rudin).

## Disclaimer

These are my personal solutions written while studying real analysis. They may contain mistakes.

The repository is not affiliated with Walter Rudin, George M. Bergman, their publishers, or the University of California, Berkeley.

Exercise statements and other material originating from the referenced works remain the property of their respective authors and copyright holders.

## License

My original solutions and notes in this repository are licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

This license does not apply to material reproduced or quoted from the referenced books or exercise collections.
