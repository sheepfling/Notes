# Guidance for this note

Keep this note's Markdown, article-specific Python, and tests together in this
folder, following the repository guidance. Keep tests of genuinely shared
packages under the central `tests/` tree. Add package markers only when imports
need them, and document commands from the repository root.

Write generated outputs under the repository's ignored `artifacts/` directory
or a temporary test directory, not into the source tree.
