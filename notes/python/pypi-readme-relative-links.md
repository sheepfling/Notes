# Why README links break on PyPI

> Type: reference
> Status: needs-review
> Updated: 2026-11-11
> Tags: python, packaging, markdown, documentation

A README can look right on GitHub and still send readers to a 404 on PyPI.
The usual culprit is an ordinary link to another file in the repository:

```markdown
[Installation guide](docs/install.md)
```

On GitHub, that link has the repository and its current revision around it.
On PyPI, the README is rendered as the package description on a different
website. The repository context has not come along for the ride.

The practical fix is to give the published description usable destinations.
For a small project, absolute links may be enough. For a README that should
keep working across branches and tags, keep relative links in the source and
rewrite them while building the package. In either case, check the description
inside the distribution artifacts before releasing them.

## The file moved, but the links did not

Packaging tools commonly read `README.md` into the package's metadata. Modern
projects express this with `project.readme`; setuptools also calls the result
`long_description`. PyPI renders that description. It does not turn the rest
of the repository into a documentation website.

At a page such as `https://pypi.org/project/example/`, an unchanged
`docs/install.md` URL resolves under that page. A leading slash makes the
problem different, not better: `/docs/install.md` means a path at the root of
**pypi.org**. Neither URL identifies a file in the GitHub repository.

Adding a source-code URL to the package metadata is useful, but it does not
establish a repository-relative base URL for every link in the description.
Likewise, putting documentation files in the source distribution does not
make PyPI serve those files at the paths used by the README.

This is a recurring packaging problem. A
[2020 readme_renderer proposal](https://github.com/pypa/readme_renderer/issues/163)
asks for configurable resolution of relative links. The
[Slack SDK reported broken README paths and table-of-contents links in 2022](https://github.com/slackapi/python-slack-sdk/issues/1160).
A [2024 packaging-problems discussion](https://github.com/pypa/packaging-problems/issues/752)
shows the root-relative variant explicitly: `/docs/other.md` becomes
`https://pypi.org/docs/other.md`. Its advice is to supply full URLs, either in
the source or when producing the metadata.

## Three reasonable ways to handle it

### Use absolute links in the README

For a short README, the simplest solution is often the best:

```markdown
[Installation guide](https://docs.example.org/install/)
```

A documentation site can provide a stable public destination. An absolute
GitHub link works too, but choose its revision deliberately. A link through
`main` follows the latest documentation, even when someone is reading an old
package release. A release tag or commit keeps the destination tied to that
release, provided the target exists and remains available.

The tradeoff appears when browsing the repository itself. A hardcoded link to
`main` still points to `main` while the reader is looking at a feature branch
or an older tag. Relative links are useful precisely because they preserve
that local context.

### Build a PyPI-specific description

Keep the repository README convenient for repository readers and transform
only the copy that goes into package metadata.

For a project already using Hatchling,
[hatch-fancy-pypi-readme](https://github.com/hynek/hatch-fancy-pypi-readme#substitutions)
provides file fragments and regular-expression substitutions. This is a
minimal example for one known link:

```toml
[build-system]
requires = ["hatchling", "hatch-fancy-pypi-readme"]
build-backend = "hatchling.build"

[project]
# Keep the project's other metadata here.
# Remove a static readme key and preserve any other dynamic fields.
dynamic = ["readme"]

[tool.hatch.metadata.hooks.fancy-pypi-readme]
content-type = "text/markdown"

[[tool.hatch.metadata.hooks.fancy-pypi-readme.fragments]]
path = "README.md"

[[tool.hatch.metadata.hooks.fancy-pypi-readme.substitutions]]
pattern = '\]\(docs/install\.md\)'
replacement = '](https://github.com/example/project/blob/v$HFPR_VERSION/docs/install.md)'
```

Replace `example/project` with the real repository. The example assumes tags
are named `v` followed by the package version; adjust it if the release process
uses another convention. A development version may have no corresponding tag.
Confirm the destination before publishing.

The rule above intentionally handles exactly one spelling of one inline
Markdown destination. It does not handle `./docs/install.md`, a reference-style
link, a URL with a fragment, or every other possible Markdown construct.
Even a narrow regex can change matching text inside a code example. Treat
substitutions as transformations of a known document, and review their output.

An existing setuptools project can perform the same transformation while
constructing `long_description`. There is no need to change build backends
solely to fix links. Keep the transformation deterministic, and make sure all
input files and required build dependencies are available when building from
the source distribution, not just from the working checkout.

### Keep the PyPI page short

A separate, small package description is another reasonable choice: explain
what the package does, show installation and a minimal example, then link to
the documentation site and repository with absolute URLs.

This reduces the number of things that have to survive two rendering
contexts. It does create another piece of writing to maintain. Generate it
from shared fragments where that saves duplication, rather than quietly
letting two full READMEs drift apart.

## Anchors need a separate check

These links have different jobs:

```markdown
[Usage](#usage)
[Usage guide](docs/usage.md#quick-start)
```

The first asks for a heading on the current page. The second asks for a
heading in a different document. A blanket rule that treats everything without
`https://` as a repository path can break the first while trying to fix the
second. It can also mishandle `mailto:`, other URI schemes, protocol-relative
URLs, images, reference links, titles, and parentheses in destinations.

Do not infer today's anchor behavior from an old bug report. The
[current readme_renderer GFM implementation](https://github.com/pypa/readme_renderer/blob/main/readme_renderer/markdown.py)
adds a `user-content-` prefix to generated heading IDs and rewrites local
fragment links to match, with special handling for footnotes. That is evidence
about the current source, not a guarantee that every deployed renderer uses
the same version or settings.

Leave same-page fragments out of repository-path rewriting. Then verify that
the rendered target IDs actually exist, especially after trimming sections
out of a PyPI-specific description. Check cross-file fragments at their final
destination too. For images, use a URL that serves image content, rather than
a repository HTML file-view page.

## Test what the package actually contains

Checking the source README alone misses build-time transformations and missing
input files. The useful boundary is the description inside the built wheel
and source distribution.

Run this in the package checkout, with `build` and `twine` installed in the
chosen development environment. These commands build and inspect locally;
they do not upload anything. The shell example is for a POSIX shell:

```sh
artifacts="$(mktemp -d)"
python -m build --outdir "$artifacts"
python -m twine check --strict "$artifacts"/*
```

Using a fresh output directory avoids accidentally inspecting an older build.
The default `python -m build` workflow builds an sdist and then a wheel from
that sdist, which helps expose build inputs missing from the archive.

Next, extract the descriptions for inspection. Run this in the same shell so
`$artifacts` still points at that directory:

```sh
python - "$artifacts" <<'PY'
from email import policy
from email.parser import Parser
from pathlib import Path
import sys
import tarfile
import zipfile

root = Path(sys.argv[1])
packages = sorted(root.glob("*.whl")) + sorted(root.glob("*.tar.gz"))
if not packages:
    raise SystemExit("No wheel or .tar.gz sdist found")

for package in packages:
    if package.suffix == ".whl":
        with zipfile.ZipFile(package) as archive:
            names = [n for n in archive.namelist()
                     if n.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise SystemExit(f"Unexpected wheel metadata: {names}")
            raw = archive.read(names[0])
    else:
        with tarfile.open(package, "r:gz") as archive:
            members = [m for m in archive.getmembers()
                       if m.isfile() and m.name.count("/") == 1
                       and m.name.endswith("/PKG-INFO")]
            if len(members) != 1:
                raise SystemExit("Expected one top-level PKG-INFO")
            stream = archive.extractfile(members[0])
            if stream is None:
                raise SystemExit("Could not read PKG-INFO")
            raw = stream.read()

    metadata = Parser(policy=policy.default).parsestr(raw.decode("utf-8"))
    description = metadata.get_payload()
    if not isinstance(description, str) or not description.strip():
        raise SystemExit(f"Missing description in {package.name}")
    output = root / (package.name + ".description.md")
    output.write_text(description, encoding="utf-8")
    print(package.name, metadata.get("Description-Content-Type"), output)
PY
```

This handles wheel metadata and a conventional `.tar.gz` sdist without
extracting their contents to the filesystem. For this Markdown example, expect
`Description-Content-Type` to identify `text/markdown`. Compare the two
extracted descriptions, inspect the rewritten URLs, and render them with the
renderer used by the release checks.

A successful `twine check` is useful, but it is not proof that every link
resolves or every fragment has a target. Also note that the standalone
hatch-fancy-pypi-readme preview uses placeholder package metadata, including
version `42.0`; inspect the artifacts to verify the real version substitution.

For a CI guard, parse the final description with a Markdown-aware parser and
check link and image destinations. Reject surviving repository-relative paths,
handle fragment-only links separately, and report which destinations failed.
Keep tests for the Markdown forms the project actually uses. Link reachability
and fragment existence are further checks, not consequences of valid syntax.

## The maintenance trap is the next link

The [notebooklm-py report from June 2026](https://github.com/teng-lin/notebooklm-py/issues/1473)
is a useful example. Its description already rewrote several paths to
version-tagged GitHub URLs. Two root-level Markdown links were missing from
the substitution list, so those two remained relative in the built metadata.

That is the weakness of a per-file list: adding a perfectly ordinary README
link can silently create a new packaging defect. A broader transformation may
help, but a check on the final artifact catches omissions regardless of which
transformation produced it.

The rule to keep is simple: **when publishing a document in a new location,
check the links in that location's output.** For a Python package, that means
checking the built description as deliberately as the package code.

## Sources

- [readme_renderer #163: Resolve relative links in long_description](https://github.com/pypa/readme_renderer/issues/163)
- [Slack SDK #1160: Links in README don't render properly on PyPI](https://github.com/slackapi/python-slack-sdk/issues/1160)
- [packaging-problems #752: Broken links on PyPI](https://github.com/pypa/packaging-problems/issues/752)
- [hatch-fancy-pypi-readme substitutions and metadata](https://github.com/hynek/hatch-fancy-pypi-readme#substitutions)
- [notebooklm-py #1473: Missing README substitutions](https://github.com/teng-lin/notebooklm-py/issues/1473)
- [readme_renderer Markdown implementation](https://github.com/pypa/readme_renderer/blob/main/readme_renderer/markdown.py)
