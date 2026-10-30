# Repository guidance

Follow the organization and note metadata conventions in [README.md](README.md).
Keep notes concise and durable; explicit user instructions take precedence over
the defaults below.

## Experiment notes

Use a reference note with a clear spine, as relevant:

1. Question, scope, and the result or decision.
2. Inputs, assumptions, implementations, and the boundaries being compared.
3. Method and environment: versions, hardware, sample protocol, and enough
   detail to repeat the work and interpret the result.
4. Results and verification, including the units, correctness checks, and
   uncertainty or limitations that affect the conclusion.
5. A concise reproduction procedure and links to retained source evidence,
   when available.

Preserve fair comparisons and distinguish measured results from inference.
Keep the final summary in Markdown. By default, do not commit raw result dumps,
captured stdout, generated reports, superseded experiments, or large one-off
scripts. Retain or link supporting evidence outside the repository when useful,
and say when it is unavailable. Keep runnable experiment or verification scripts
needed to regenerate results; prefer a small, reusable harness with shared code
and clear dependencies over duplicated or report-generating scripts. Include
additional artifacts when the user explicitly requests them or they are necessary
for the task.

## Tests for notes and experiments

Keep Markdown in its subject folder, maintained Python implementation under the
root `src/` tree, and canonical Python tests under `tests/`. Group related code
and tests by subject or project, make the code importable, and add package
markers when useful. Use pytest for Python tests. Preserve existing documented
script and import entry points when moving implementations, and do not discover
the same test twice through compatibility wrappers. Document dependencies and
repository-root commands to reproduce the experiment and run its tests. Keep
generated artifacts under the ignored `artifacts/` directory or a temporary
test directory, not beside source files.

The quaternion benchmark is a separately pinned reproduction: keep its source,
tests, and recorded dependencies together unless its reproduction is deliberately
updated and revalidated.

For each executable article or collection, document its dependencies and
repository-root run and test commands next to its note. Specify output paths
and any overwrite or platform limitations. Do not run historical or
cross-project maintenance scripts automatically as part of article discovery.
