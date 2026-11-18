# Keeping useful research in Notes

> Type: how-to
> Status: current
> Updated: 2026-11-11
> Tags: research, writing, documentation

Use this repository as a durable home for research that is safe to share
publicly. A short note with an answer, its limits, and a few good sources is
usually more useful than a copied conversation or a large raw dump.

## Capture the reusable part

1. Put the note in `notes/<topic>/` and use a descriptive, lowercase,
   hyphenated filename. Use an existing subject before adding a new one.
2. Follow the metadata format in [the repository README](../../README.md).
   Use `needs-review` when the answer still needs verification. A status label
   describes the note's reliability; it does not make its contents private.
3. Open with the question and the answer. Include assumptions, evidence,
   practical steps, and limitations where they change how someone would use
   the result.
4. Link primary sources near the claims they support. Date observations that
   could change. Separate what was tested from what a source reports or what
   is inferred.
5. Retain small, reusable examples when they help reproduce the finding.
   Follow the repository's existing experiment and test conventions rather
   than storing generated reports or raw output by default.
6. Add the note to the appropriate subject in the README index. Link related
   notes rather than making parallel copies.

A blog-style explanation can live beside shorter references in the same topic
folder. There is no need for a separate blogging system just to retain it.

## Check privacy before saving

Treat every file in this public repository as potentially publishable,
including material in `inbox/` and notes marked `needs-review`.

Keep out private conversations, internal work documents, non-public project
names or URLs, personal contact information, customer or employee details,
credentials, tokens, and screenshots containing account data. Prefer a public
source and a generic example that demonstrates the same idea.

If a useful conclusion depends on private material, keep that source outside
this repository. Write a public-safe version only when it can stand on its
own without disclosing the private context. If that is unclear, leave it out
until reviewed. An ignored file or an unpushed branch is not a reliable place
to store secrets.

## Review before publishing

- Read the entire diff, including filenames, comments, links, example values,
  and any supporting assets.
- Check factual claims, source dates, and the limits of any experiments.
- Run the relevant example or tests, and check relative links from the note's
  actual location.
- Keep drafting and publication separate. Saving a note locally is not an
  instruction to push, open a public pull request, or deploy a website.

Use the existing repository and index first. A generated site can be a later
presentation layer if reading or discovery becomes awkward; it does not need
to become a second source of truth.
