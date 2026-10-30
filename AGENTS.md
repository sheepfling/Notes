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

## Living cross-project guidance

This section is a public reference for work across projects, not an instruction
that automatically overrides another repository's `AGENTS.md`. Apply it when
relevant, subject to the user's current request and the target project's own
instructions, constraints, and established conventions. A project may have a
more specific exception. The Notes-specific instructions in this file continue
to govern work in Notes.

The items below summarize review feedback as working defaults, not universal
laws. Links identify the original context; check that context before extending a
project-specific decision. Suggestions marked as such are useful practices,
not claims that Rick explicitly requested a global rule.

### Types and boundaries

- Model meaningful data with named types instead of passing opaque dictionaries
  through the application. At a serialization or configuration boundary,
  validate the external representation and convert it to a semantic model;
  serialize from that model explicitly. Dataclasses or Pydantic may suit the
  boundary depending on validation needs. See the requests for [a semantic
  serialized result](https://github.com/sheepfling/Notes/pull/3#discussion_r4419724352)
  and [validated configuration](https://github.com/sheepfling/snakemd-stubs/pull/1#discussion_r4418886452).
- Give distinct records meaningful fields and types, rather than hiding the
  domain behind generic containers. Annotate public interfaces and useful
  internal boundaries. See [per-function records](https://github.com/sheepfling/Notes/pull/3#discussion_r4419731738)
  and [annotations](https://github.com/sheepfling/Notes/pull/3#discussion_r4419712881).
- Make units and conventions explicit in numeric inputs, outputs, and results;
  an otherwise correct number is hard to use if its unit is ambiguous. See the
  [return-unit feedback](https://github.com/sheepfling/Notes/pull/1#discussion_r4419758151).

### Packages, tools, and CI

- Prefer importable packages and portable module entry points when code is
  shared or run from multiple locations. Avoid depending on a particular
  checkout location or ad hoc path manipulation. See the request for [portable
  scripts](https://github.com/sheepfling/mdutils-stubs/pull/1#discussion_r4242364915)
  and the [module command preference](https://github.com/sheepfling/mdutils-stubs/pull/1#discussion_r4243574657).
- Keep provider configuration thin when practical. One suggested approach is
  to put reusable checks in a local runner and have CI invoke the same entry
  point. Consolidate development
  dependency definitions when doing so reduces drift. See [thin CI](https://github.com/sheepfling/snakemd-stubs/pull/1#discussion_r4418876608)
  and [dependency consolidation](https://github.com/sheepfling/mdutils-stubs/pull/1#discussion_r4407107911).
- Consider established libraries when they fit the problem, while checking
  semantics, dependencies, and evidence relevant to the task. The request to use
  a [Markdown assembly package](https://github.com/sheepfling/Notes/pull/3#discussion_r4419725812)
  arose in a specific implementation; it is not a blanket dependency mandate.
- Use accurate language identifiers in fenced examples, including `shell` for
  shell commands. See [Notes feedback](https://github.com/sheepfling/Notes/pull/1#discussion_r4419760709).

### Tests and evidence

- Suggested testing practice: exercise observable behavior and important
  boundaries, including representative inputs and failure cases. For typing
  work, include typed variables; literals alone can be contextually typed and
  conceal a gap. This is a review suggestion from [mdutils-stubs](https://github.com/sheepfling/mdutils-stubs/pull/1#discussion_r4419816005),
  not a global test matrix.
- Keep reproducible proof or verification code when it is needed to support a
  result. Share a small harness and dependencies where possible; distinguish the
  source from generated reports, captured output, and superseded results. See
  [runnable scripts](https://github.com/sheepfling/Notes/pull/3#discussion_r4418959362)
  and [shared code](https://github.com/sheepfling/Notes/pull/3#discussion_r4418790313).
- Report what actually ran and where. A configured language mode, local smoke
  test, or workflow definition is not evidence that a particular runtime or
  hosted job passed. State unavailable evidence and material limitations. See
  the [runtime and hosted-check discussion](https://github.com/sheepfling/snakemd-stubs/pull/1#discussion_r4418816315)
  and the review suggestion about [retrievable benchmark evidence](https://github.com/sheepfling/Notes/pull/3#discussion_r4419599692).
- Suggested review practice: inspect individual threads, reviews, and
  general comments; address or explain each applicable point; and verify thread
  state and the checks for the actual head. A reply in one thread does not
  establish that every related thread is resolved. The evolving [Notes guide
  review](https://github.com/sheepfling/Notes/pull/2#discussion_r4419896563)
  illustrates why the final state matters.

### Project-specific decisions

- **Notes:** Preserve the experiment guidance above. For Notes blog tests, use
  pytest and a `tests/` directory, with package markers where needed, as requested
  in [the review](https://github.com/sheepfling/Notes/pull/1#discussion_r4419902800)
  and its [package-marker follow-up](https://github.com/sheepfling/Notes/pull/1#discussion_r4419904929).
  Favor discoverable navigation and searchable tags when organizing a growing
  collection; see [navigation](https://github.com/sheepfling/Notes/pull/1#discussion_r4418947349)
  and [tag search](https://github.com/sheepfling/Notes/pull/2#discussion_r4418917799).
  Keep Markdown readable in plain text as well as rendered form; see the
  [table feedback](https://github.com/sheepfling/Notes/pull/2#discussion_r4418920056).
- **mdutils-stubs and snakemd-stubs:** For those stub playtests, Rick requested
  ty, mypy, and pyright; this is not a default for every Python project. See
  [mdutils-stubs](https://github.com/sheepfling/mdutils-stubs/pull/1#issuecomment-6513809349)
  and [snakemd-stubs](https://github.com/sheepfling/snakemd-stubs/pull/1#issuecomment-6513810921).
  Surface mismatches with upstream libraries when useful for upstream fixes:
  [review](https://github.com/sheepfling/mdutils-stubs/pull/1#discussion_r4418983271).
- **Alphus:** Treat it as experimental and separate from Notes development
  dependencies and required CI. This is not a prohibition on experiments in
  other projects. See the [experimental-tool discussion](https://github.com/sheepfling/mdutils-stubs/pull/1#discussion_r4418976420)
  and [CI discussion](https://github.com/sheepfling/snakemd-stubs/pull/1#discussion_r4418899341).

### Maintaining this guidance

When a durable lesson emerges, update the relevant section instead of appending
an unfiltered transcript. Record the actionable rule, its scope or exception,
and a public source link when available. Label an inference or proposal as such;
do not promote a one-off implementation choice into a global requirement. If
new evidence changes a rule, revise or remove the old text so future readers see
one current explanation. Keep temporary task status in its issue or PR. This is
a public repository: do not add credentials, private project material, machine
specifics, or raw private memory.
