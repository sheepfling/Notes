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

For a self-contained article, keep its Markdown, article-specific Python and
tests together in a subject folder. Place tests of shared packages or behavior
spanning articles under `tests/<topic>/`. Use pytest for Python tests; make
supporting code importable where needed, adding package markers when useful.
Document dependencies and repository-root commands to reproduce the experiment
and run its tests. Add co-located test directories to pytest discovery. Keep
generated artifacts under the ignored `artifacts/` directory or a temporary
test directory, not beside source files.
