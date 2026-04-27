# Project guidelines

## Scope
These instructions apply to the whole workspace.

## Target
- Target runtime is the LBD public Hadoop cluster via JupyterLab shell.
- Target Python version is 3.12.x.
- Target Hadoop and HDFS client version is 3.3.6.
- Target `mrjob` version is 0.7.4.

## Architecture
- Keep the Task 1 implementation aligned with [Task1/requirements/Requiremnts.md](Task1/requirements/Requiremnts.md) and [Task1/requirements/arch.md](Task1/requirements/arch.md).
- Use `src/settings.py` as the single source for shared constants such as paths, counters, tokenization rules, and defaults.
- Preserve the planned file layout under `Task1/src/` unless a task explicitly requires changing it.

## Task 1 rules
- Implement chi-square feature selection with document-presence semantics, not raw term-frequency semantics.
- Deduplicate terms per review document before emitting term counts.
- Keep the final output format exact: one alphabetical category line with top 75 terms per category, plus one merged alphabetical dictionary line.
- Keep all project paths relative in submitted code and parameterize HDFS input paths.
- Prefer one raw-data scan for counting, aggressive combiner use, compact key/value emissions, and bounded top-k selection.

## Dependencies
- Prefer Python standard library plus `mrjob` only.
- Do not introduce `pandas`, `numpy`, `scipy`, Spark, or heavyweight text-processing libraries unless explicitly requested.

## Code style
- Use instructions in .github/AI code gen ruleset.md
- When sketching or stubbing typed Python functions, use the multiline signature-comment template from the ruleset instead of placeholder docstrings.
- For those typed function blocks, keep the function summary comment above the block and keep only aligned inline comments on arguments and return values.
- In those typed function signature blocks, align all inline comments to the widest signature line plus 4 spaces.
- For general code, use inline comments for expressions and place comments above block structures such as functions, loops, and try blocks.
- Reuse the explicit function names and file mappings already documented in `arch.md`.
- If new functions or files are needed, follow the existing naming conventions and document them in `arch.md`.

## Validation
- Prefer local validation on the provided development shards before assuming cluster runs.
- When adding or changing Python code, keep it compatible with the verified 3.12 target.
