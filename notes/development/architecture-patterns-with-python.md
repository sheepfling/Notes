# Architecture Patterns with Python

> Type: reference
> Status: needs-review
> Updated: 2026-10-30
> Tags: architecture, python, testing

[Architecture Patterns with Python](https://www.cosmicpython.com/) by Harry
Percival and Bob Gregory explores structuring applications around domain logic
that can be tested without starting infrastructure. This reading note covers
the preface and selected chapters, not an evaluation of the entire book.

## Ideas to examine

- The [preface](https://www.cosmicpython.com/book/preface) frames the goal as
  managing business complexity while keeping core logic testable.
- The [repository pattern](https://www.cosmicpython.com/book/chapter_02_repository)
  provides an abstraction over persistence to separate the domain model from
  storage details. The book illustrates testing that boundary with a fake
  repository as well as integration tests against a real database.
- A service layer coordinates application use cases; the
  [unit of work](https://www.cosmicpython.com/book/chapter_06_uow) groups
  persistence operations within a transaction boundary and coordinates with
  repositories. Tests still need to cover real transaction behavior.
- The [events and message bus chapter](https://www.cosmicpython.com/book/chapter_08_events_and_message_bus)
  uses events to separate responsibilities within a single process; the same
  idea can extend across services.

## Triage and limits

Use this as a source of candidate techniques, not a prescribed architecture.
Before adding a layer, identify the coupling or testing problem it solves and
weigh the extra indirection against the project's size and needs. The book's
examples and the [March 28, 2025 Hacker News discussion](https://news.ycombinator.com/item?id=43501989)
provide perspectives, not measured results for this repository. Evaluate any
proposed use against the actual code, dependencies, and integration tests.
