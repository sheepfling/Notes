# Mixture note intake verification

> Type: reference
> Status: current
> Updated: 2026-11-13
> Tags: mathematics, verification, python

The blog was expanded from the supplied publication-kit draft, with its
assumptions and limitations checked against the accompanying theory and results.
No employer/customer material, credentials, personal contact data, or private
service URLs were found in the retained text and source. This is a content review,
not a claim of an exhaustive automated secret scan.

## Retained material

- The blog and four supplied figures.
- The source package and its dependency declaration.
- The original four pytest modules, relocated to the repository test directory.
- The theory derivation, with note metadata added.

The bundled wheel, raw result dumps, nested ZIP, and social-post repository
placeholder were not added to Notes. Source modules and tests are byte-identical
to the supplied v0.3 source. The packaging test-directory setting was adjusted
for the Notes layout.

## Actual validation

On Linux, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0 and pytest 9.2.0:

- All **303 supplied tests passed** in 1.65 seconds.
- One unrelated installed AnyIO pytest-plugin deprecation warning was emitted.
- Local editable installation succeeded, using preinstalled dependencies and
  disabled build isolation; the CLI help worked outside the checkout.
- The retained source and tests were compared byte-for-byte with the ZIP.
- Local Markdown links were checked.
- The lead figure was visually inspected.
- No fresh lint, strict typing, native Windows run, or figure regeneration is
  claimed.

The tests support the implementation's stated examples and properties. They do
not establish an unrestricted global optimizer or sensory flavor equivalence.
