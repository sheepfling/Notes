# Typography & Font Terminology

> Type: reference
> Status: needs-review
> Updated: 2026-10-29
> Tags: graphic-design, typography

### A Practical Guide to Typefaces, Fonts, Letterforms, and Typesetting

Typography terminology mixes centuries of printing tradition with
modern digital font technology.

Consequently, terms such as *font*, *typeface*, *family*, *style*,
and *weight* are frequently used interchangeably, despite describing
different concepts.

This guide establishes a practical vocabulary for discussing,
selecting, designing, implementing, and maintaining typography.

---

## 1. Core Terminology

| Term             | Definition                                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| **Typography**   | The art and practice of arranging type to make written language readable, legible, and visually effective. |
| **Typeface**     | A coordinated visual design for a collection of characters and glyphs.                                     |
| **Font**         | A specific implementation of a typeface, historically at a particular size and style.                      |
| **Type Family**  | A collection of related typefaces or styles sharing a common design.                                       |
| **Font Family**  | The grouping of related fonts under a shared family name, particularly in software and CSS.                |
| **Font Face**    | A particular member of a font family, such as Regular, Bold, or Italic.                                    |
| **Style**        | A variation in the appearance of a typeface, such as Roman, Italic, or Oblique.                            |
| **Weight**       | The relative thickness of a typeface's strokes, such as Light, Regular, or Bold.                           |
| **Width**        | The relative horizontal proportions of characters, such as Condensed or Expanded.                          |
| **Point Size**   | The nominal size of type, traditionally measured in typographic points.                                    |
| **Glyph**        | A particular visual representation used to render a character or character sequence.                       |
| **Character**    | An abstract unit of text, such as the letter A or the numeral 7.                                           |
| **Letterform**   | The visual shape or construction of a letter.                                                              |
| **Typesetting**  | The process of arranging text into lines, paragraphs, and pages.                                           |
| **Font Foundry** | A company or individual producing and distributing typefaces and fonts.                                    |

> **Key distinction:** A typeface is a design. A font is an
> implementation of that design.

---

## 2. Typeface vs. Font

This is the foundational distinction.

### Typeface

A **typeface** is the underlying visual design.

Examples:

- Helvetica
- Garamond
- Futura
- Baskerville
- Eurostile
- Inter

Each represents a recognizable typographic design with characteristic
letterforms, proportions, spacing, and construction.

### Font

A **font** is a usable implementation of a typeface.

Historically, a font was a physical collection of printing type in
one size and style.

For example:

- Garamond Regular, 12 pt
- Garamond Italic, 12 pt
- Garamond Bold, 18 pt

Each would require a separate assortment of physical type.

In digital typography, fonts are typically software resources
containing glyph outlines, metrics, and layout information.

Examples:

- `Inter-Regular.ttf`
- `Inter-Bold.ttf`
- `Inter-Italic.otf`

Modern scalable fonts are not generally restricted to a particular
point size.

### Practical distinction

| Concept   | Example                |
| --------- | ---------------------- |
| Typeface  | Inter                  |
| Family    | Inter                  |
| Face      | Inter Bold Italic      |
| Font file | `Inter-BoldItalic.ttf` |
| Size      | 14 pt                  |

In everyday conversation, *font* is frequently used to mean
*typeface*. This is widely understood.

However, technical documentation benefits from distinguishing them.

**Preferred usage:**

- "We selected the Inter typeface."
- "The interface uses the Inter font family."
- "The heading uses the Bold face."
- "The application loads the corresponding font file."

---

## 3. Family, Face, Style, and Weight

These terms describe different dimensions of a type system.

Consider a hypothetical family:

```text
Example Sans
│
├── Light
│   ├── Roman
│   └── Italic
│
├── Regular
│   ├── Roman
│   └── Italic
│
├── Medium
│   ├── Roman
│   └── Italic
│
├── Semibold
│   ├── Roman
│   └── Italic
│
└── Bold
    ├── Roman
    └── Italic
```

### Family

The broader collection of related typographic designs.

Example: `Example Sans`

### Face

A particular combination of typographic attributes within the family.

Example: `Example Sans Bold Italic`

### Weight

The relative thickness of the strokes.

Examples:

- Thin
- Light
- Regular
- Medium
- Semibold
- Bold
- Black

### Style

The form or posture of the letters.

Examples:

- Roman / Upright
- Italic
- Oblique

### Width

The relative horizontal proportions of the characters.

Examples:

- Ultra Condensed
- Condensed
- Normal
- Expanded

Not every family supports every combination.

### Superfamilies

A **type superfamily** groups related families designed to work together.

For example:

```text
Example
├── Example Serif
├── Example Sans
└── Example Mono
```

The families may share proportions, construction principles, or
other design characteristics.

---

## 4. Roman vs. Italic vs. Oblique

These distinctions are particularly important.

### Roman (Upright)

The standard, upright design of a typeface.

Roman does not necessarily mean Regular weight.

A Bold Roman face is still upright.

### Italic

A separately designed style, often incorporating different
letterforms rather than merely slanting upright characters.

For example, lowercase `a` may change from a double-storey to
a single-storey construction.

### Oblique

A slanted style generally preserving the underlying construction
of the upright letters.

A properly designed oblique face may include optical corrections
and is not necessarily a mechanically slanted copy.

### Faux Italic

An artificial slant applied by software when a proper italic or
oblique face is unavailable.

Likewise, **faux bold** artificially increases stroke thickness.

Both can produce inferior results compared with properly designed faces.

> **Italic is a design variation; oblique primarily describes
> slanted construction.**

---

## 5. Font Weight Terminology

Digital typography commonly uses numerical weight values.

| Weight                    | Common CSS Value |
| ------------------------- | ---------------: |
| Thin                      | 100              |
| Extra Light / Ultra Light | 200              |
| Light                     | 300              |
| Regular / Normal          | 400              |
| Medium                    | 500              |
| Semibold / Demi Bold      | 600              |
| Bold                      | 700              |
| Extra Bold / Ultra Bold   | 800              |
| Black / Heavy             | 900              |

These are conventional CSS weight mappings, not measurements
of actual stroke thickness.

A `700` weight in one family may appear lighter than a `600`
weight in another.

Some fonts also support intermediate or extended numeric values.

**Important:** Weight names are not completely standardized across
foundries.

---

## 6. Typeface Classifications

Typefaces are commonly classified according to the construction
and appearance of their letterforms.

### Serif

Letters incorporate small terminal strokes or projections.

Common subcategories:

| Classification      | Characteristics                                             |
| ------------------- | ----------------------------------------------------------- |
| **Old Style**       | Humanist influence, moderate contrast, often angled stress. |
| **Transitional**    | Greater contrast and more regular construction.             |
| **Didone / Modern** | Strong stroke contrast and thin, often unbracketed serifs.  |
| **Slab Serif**      | Heavy, block-like serifs.                                   |

Examples include Garamond, Baskerville, Bodoni, and Rockwell.

### Sans Serif

Letterforms generally lack conventional serifs.

Common subcategories:

| Classification    | Characteristics                                                            |
| ----------------- | -------------------------------------------------------------------------- |
| **Grotesque**     | Early sans-serif designs, often with irregular or distinctive proportions. |
| **Neo-Grotesque** | More systematic, comparatively neutral construction.                       |
| **Geometric**     | Forms influenced by circles, squares, and geometric construction.          |
| **Humanist**      | Forms influenced by handwriting and traditional letter construction.       |

Examples include Akzidenz-Grotesk, Helvetica, Futura, and Frutiger.

### Other Classifications

| Classification       | Description                                                                         |
| -------------------- | ----------------------------------------------------------------------------------- |
| **Monospaced**       | Characters generally occupy equal horizontal advances.                              |
| **Script**           | Letterforms inspired by handwriting or connected writing.                           |
| **Blackletter**      | Dense, angular forms associated with historical manuscript traditions.              |
| **Display**          | Designed primarily for prominent use at larger sizes.                               |
| **Handwritten**      | Emulates informal handwriting.                                                      |
| **Decorative**       | Emphasizes expressive or ornamental letterform design.                              |
| **Symbol / Dingbat** | Contains pictograms, symbols, or ornaments rather than conventional text alphabets. |

Classification systems vary, and categories can overlap.

For example, a typeface can be both geometric and sans serif.

---

## 7. Display vs. Text Typefaces

Typefaces may be optimized for different applications.

### Display

Designed primarily for larger sizes, such as:

- Headlines
- Posters
- Wordmarks
- Signage
- Editorial titles

Display designs may employ finer details, tighter spacing,
greater contrast, or more expressive forms.

### Text

Designed for sustained reading at relatively small sizes.

Common priorities include:

- Legibility
- Robust letterform differentiation
- Consistent rhythm
- Comfortable spacing
- Predictable rendering

### Optical Size

**Optical sizing** adjusts a type design according to its intended
rendered size.

A small optical size may use:

- Wider spacing
- Larger counters
- Sturdier details
- Reduced stroke contrast

A large optical size may employ finer details and tighter proportions.

Modern variable fonts may expose optical size as the `opsz` axis.

**Optical size is not the same as point size.**

Point size determines nominal scale; optical size controls the
design's adaptation to that scale.

---

## 8. Letterform Anatomy

Understanding letterform anatomy helps describe precisely
what makes two typefaces different.

| Term                | Definition                                                                     |
| ------------------- | ------------------------------------------------------------------------------ |
| **Baseline**        | Imaginary line on which most characters rest.                                  |
| **X-height**        | Height of the lowercase `x`, often used to characterize lowercase proportions. |
| **Cap Height**      | Height of typical flat-topped capital letters.                                 |
| **Ascender**        | Portion of a lowercase letter extending above the x-height.                    |
| **Descender**       | Portion extending below the baseline.                                          |
| **Stem**            | Principal structural stroke of a letter.                                       |
| **Crossbar**        | Horizontal stroke connecting parts of a letter.                                |
| **Counter**         | Enclosed or partially enclosed interior space of a letter.                     |
| **Aperture**        | Opening in a partially enclosed letterform.                                    |
| **Bowl**            | Curved stroke enclosing or partially enclosing a counter.                      |
| **Terminal**        | End of a stroke.                                                               |
| **Serif**           | Small finishing stroke or projection.                                          |
| **Shoulder**        | Curved stroke extending from a stem.                                           |
| **Spine**           | Principal curved stroke of an `S`.                                             |
| **Eye**             | Enclosed counter of a lowercase `e`.                                           |
| **Ear**             | Small projecting stroke, notably on some lowercase `g` forms.                  |
| **Stress**          | Direction of the apparent thick-to-thin stroke relationship.                   |
| **Stroke Contrast** | Difference between thick and thin strokes.                                     |
| **Overshoot**       | Slight extension of curved or pointed forms beyond alignment lines.            |

### Double-Storey vs. Single-Storey

The lowercase letters `a` and `g` are particularly useful
when comparing typefaces.

A **double-storey** lowercase `a` generally contains two
distinct structural portions.

A **single-storey** lowercase `a` has a simpler construction.

These differences can substantially affect a typeface's
appearance and character.

### Optical Compensation

Letterforms are not always geometrically exact.

For example:

- Circular letters may extend beyond cap-height and baseline guides.
- Horizontal strokes may be thinner than vertical strokes.
- Spacing may be intentionally asymmetrical.
- Identically measured forms may be adjusted to appear equal.

These adjustments account for human visual perception.

> **Geometric equality does not guarantee optical equality.**

---

## 9. Kerning, Tracking, Leading, and Spacing

These terms describe distinct aspects of typesetting.

### Kerning

Adjustment of spacing between particular glyph pairs.

For example:

```text
AV
To
WA
```

The shapes of adjacent letters may require spacing adjustments
to appear visually balanced.

Kerning is primarily concerned with specific pair relationships,
although modern layout systems can use more complex positioning.

### Tracking

Uniform or systematic adjustment of spacing across a sequence
of characters.

Also called **letterspacing**.

Tracking affects the overall density of the text.

### Leading

The vertical spacing between successive baselines of text.

Historically, the term referred to strips of lead inserted
between lines of metal type.

In modern software, **line height** is commonly used to describe
the corresponding layout dimension.

The terms are often used interchangeably, although their historical
and implementation-specific meanings can differ.

### Word Spacing

Horizontal space between words.

### Sidebearings

Spacing built into a glyph's metrics on its left and right sides.

Sidebearings establish the default spacing behavior before
additional adjustments such as kerning.

### Comparison

| Term             | Controls                                            |
| ---------------- | --------------------------------------------------- |
| **Kerning**      | Spacing between particular glyph pairs.             |
| **Tracking**     | Spacing across a sequence of characters.            |
| **Leading**      | Baseline-to-baseline vertical spacing.              |
| **Word Spacing** | Space between words.                                |
| **Sidebearings** | Built-in spacing associated with individual glyphs. |

**Rule of thumb:** Use kerning for problematic pairs, tracking for
overall text density, and leading for vertical rhythm.

---

## 10. Point Size, Em, Rem, and Font Metrics

Typography uses several overlapping measurement systems.

### Point (pt)

A traditional typographic unit.

In modern desktop publishing:

```text
1 point = 1/72 inch
```

A nominal 12-point font does not mean its capital letters
are exactly 12 points tall.

### Pica

A traditional unit commonly used in page layout.

```text
1 pica = 12 points
```

### Em

A unit based on the current font size.

In CSS:

```css
font-size: 16px;
letter-spacing: 0.05em;
```

Here, `0.05em` corresponds to `0.8px` at a 16px font size.

### Rem

A CSS unit relative to the root element's font size.

Unlike `em`, it does not scale according to the font size
of each intermediate parent element.

### Em Square

A conceptual coordinate square used in font design.

The **units per em** value establishes the coordinate scale
of the font's outlines and metrics.

Common values include 1000 and 2048 units per em.

### Font Metrics

Measurements used by layout and rendering systems.

Examples include:

- Ascender
- Descender
- Line gap
- Advance width
- Sidebearings
- Bounding boxes

Font metrics influence layout, but do not necessarily
correspond exactly to visible glyph boundaries.

---

## 11. Character vs. Glyph vs. Code Point

These terms are especially important in software development.

### Character

An abstract textual element.

Example: the letter `A`.

### Code Point

A numerical value assigned within a character encoding standard
such as Unicode.

Example:

```text
U+0041 = LATIN CAPITAL LETTER A
```

### Glyph

A visual form used to render one or more characters.

A font may contain multiple glyphs representing the same character,
such as stylistic alternates.

Conversely, a single glyph can represent several characters.

### Grapheme Cluster

A sequence of one or more Unicode code points perceived as
a single user-facing character.

This distinction is important when processing combining marks,
emoji sequences, and complex writing systems.

### Ligature

A glyph representing a combination of characters.

Common examples:

```text
fi
fl
ffi
```

Ligatures may improve visual appearance or be required
for correct shaping in particular scripts.

### Important Distinction

```text
Character / Code Point
          │
          ▼
     Text Shaping
          │
          ▼
      Glyph Selection
          │
          ▼
    Glyph Positioning
          │
          ▼
        Rendering
```

The relationship between characters and glyphs is not
necessarily one-to-one.

Unicode defines encoded characters, not the precise
appearance of their glyphs.

---

## 12. OpenType Features

Modern fonts can contain sophisticated typographic behaviors.

Common OpenType feature tags include:

| Feature                    | Tag           | Purpose                                                |
| -------------------------- | ------------- | ------------------------------------------------------ |
| Standard Ligatures         | `liga`        | Common ligature substitutions.                         |
| Discretionary Ligatures    | `dlig`        | Optional decorative or historical ligatures.           |
| Kerning                    | `kern`        | Glyph positioning adjustments.                         |
| Small Capitals             | `smcp`        | Small capitals substituted for lowercase letters.      |
| Capitals to Small Capitals | `c2sc`        | Small capitals substituted for uppercase letters.      |
| Oldstyle Figures           | `onum`        | Numerals with varying heights and alignments.          |
| Lining Figures             | `lnum`        | Numerals aligned to a common height.                   |
| Tabular Figures            | `tnum`        | Equal-width numerals for tabular alignment.            |
| Proportional Figures       | `pnum`        | Numerals with varying advance widths.                  |
| Fractions                  | `frac`        | Fraction formatting and substitutions.                 |
| Stylistic Alternates       | `salt`        | Alternative glyph designs.                             |
| Stylistic Sets             | `ss01`–`ss20` | Groups of coordinated alternate glyphs.                |
| Swashes                    | `swsh`        | Decorative glyph variations.                           |
| Contextual Alternates      | `calt`        | Glyph substitutions influenced by surrounding context. |

Not every font implements every feature.

The presence of a feature tag does not guarantee that
all characters have corresponding substitutions.

### Small Caps vs. Scaled Capitals

**True small caps** are specially designed letterforms.

Simply shrinking ordinary capitals is not equivalent:
stroke weights and proportions may become inconsistent.

### Tabular vs. Proportional Figures

Tabular numerals occupy equal horizontal advances.

They are especially useful for:

- Financial tables
- Timers
- Dashboards
- Columns of numeric data

Proportional numerals are generally more natural
within continuous text.

---

## 13. Static vs. Variable Fonts

### Static Fonts

Traditional digital fonts generally encode one specific
design instance per font resource.

For example:

```text
ExampleSans-Regular.ttf
ExampleSans-Medium.ttf
ExampleSans-Bold.ttf
```

### Variable Fonts

A **variable font** contains a continuous or discrete design space
that allows supported attributes to vary.

Typical registered axes include:

| Axis         | Tag    | Controls                                  |
| ------------ | ------ | ----------------------------------------- |
| Weight       | `wght` | Stroke weight.                            |
| Width        | `wdth` | Character width proportions.              |
| Slant        | `slnt` | Slant angle.                              |
| Italic       | `ital` | Italic selection or variation.            |
| Optical Size | `opsz` | Optical-size-specific design adaptations. |

Some variable fonts expose additional custom axes.

Examples might include:

- Roundness
- Grade
- Contrast
- Serif construction

### Grade vs. Weight

**Weight** generally changes stroke thickness and may
alter character widths or spacing.

**Grade** changes stroke thickness while aiming to preserve
advance widths and text layout.

Grade is useful when increasing or decreasing visual emphasis
without causing text reflow.

It is not a universally available font axis.

### Named Instances

A variable font can expose predefined configurations,
such as Regular, Medium, and Bold.

These are called **named instances**.

> **Variable fonts are not merely collections of static font
> files bundled together.** They encode relationships between
> compatible designs within a variation space.

---

## 14. Font File Formats

A typeface design may be distributed in several technical formats.

| Format               | Extension | Description                                                               |
| -------------------- | --------- | ------------------------------------------------------------------------- |
| TrueType             | `.ttf`    | Common scalable font format, conventionally using TrueType outlines.      |
| OpenType             | `.otf`    | Common extension for OpenType fonts, often using CFF/PostScript outlines. |
| Web Open Font Format | `.woff`   | Compressed font packaging intended for web delivery.                      |
| WOFF2                | `.woff2`  | More efficient compressed web font packaging.                             |
| TrueType Collection  | `.ttc`    | Collection containing multiple font resources, potentially sharing data.  |

### Important Technical Distinction

**OpenType** is a font format and layout technology,
not simply the `.otf` extension.

A `.ttf` file can also contain an OpenType font with
advanced OpenType layout features.

The distinction between `.ttf` and `.otf` is not simply
"old versus new."

### Web Fonts

Web fonts are font resources loaded for use by a website
or web application.

WOFF2 is commonly preferred for modern web delivery
because of its compression efficiency.

### Font Licensing

The ability to install a font does not necessarily grant
permission to redistribute, embed, modify, or sublicense it.

Relevant permissions may differ for:

- Desktop use
- Web embedding
- Application bundling
- Document embedding
- Redistribution
- Modification

Always consult the applicable font license.

---

## 15. Typography vs. Typesetting vs. Lettering

These describe related but distinct disciplines.

### Typography

The broader practice of using and arranging type.

Typography includes:

- Typeface selection
- Hierarchy
- Spacing
- Alignment
- Composition
- Legibility
- Visual rhythm

### Typesetting

The process of arranging text into a specific layout.

For example, typesetting a technical manual includes:

- Line breaking
- Paragraph formatting
- Pagination
- Hyphenation
- Figure and caption placement
- Mathematical notation

### Type Design

The creation of typefaces and their underlying systems.

It includes letterform development, spacing, kerning,
glyph coverage, and font production.

### Lettering

The creation of letterforms specifically for a particular
composition or application.

For example, a custom-drawn company wordmark may be lettering
rather than a conventional font selection.

### Calligraphy

The art of producing letterforms through writing,
traditionally using tools such as pens or brushes.

Calligraphy can influence type design and lettering,
but is a distinct practice.

### Comparison

| Discipline      | Primary Concern                                     |
| --------------- | --------------------------------------------------- |
| **Typography**  | Effective visual arrangement of type.               |
| **Typesetting** | Composition of text into a layout.                  |
| **Type Design** | Creation of reusable systems of letterforms.        |
| **Lettering**   | Creation of letterforms for a specific composition. |
| **Calligraphy** | Creation of letterforms through the act of writing. |

A custom logo wordmark may involve lettering, type design,
typography, or a combination of all three.

---

## 16. Legibility vs. Readability

These terms are closely related but not identical.

### Legibility

How easily individual characters and letterforms
can be distinguished and recognized.

Influenced by:

- Character differentiation
- Stroke contrast
- Apertures
- Size
- Rendering quality

### Readability

How comfortably a reader can process extended passages
of text.

Influenced by:

- Typeface selection
- Line length
- Leading
- Spacing
- Hierarchy
- Paragraph structure
- Contrast and presentation

A highly distinctive display typeface may be legible
in a short headline but uncomfortable for extended reading.

> **Legibility concerns recognizing letters; readability
> concerns comfortably reading text.**

Both depend on context and should not be treated
as absolute properties of a typeface.

---

## 17. Font Rendering Terminology

Several technical processes occur between selecting a font
and displaying text.

| Term                   | Definition                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Shaping**            | Converting character sequences into positioned glyph sequences according to script, language, and font rules. |
| **Rasterization**      | Converting glyph outlines into pixels.                                                                        |
| **Hinting**            | Instructions or adjustments intended to improve glyph appearance at particular pixel sizes.                   |
| **Antialiasing**       | Techniques for smoothing the appearance of rasterized edges.                                                  |
| **Subpixel Rendering** | Rendering techniques that exploit display subpixel geometry.                                                  |
| **Fallback Font**      | A font used when the preferred font cannot render required characters.                                        |
| **Font Stack**         | Ordered list of preferred font families for rendering.                                                        |
| **Font Subsetting**    | Producing a reduced font containing only selected glyphs or character coverage.                               |
| **Font Embedding**     | Including font data within a document or application resource.                                                |

### Font Fallback

Fallback is especially important for multilingual text,
symbols, mathematical notation, and emoji.

Different fonts can have substantially different metrics,
so fallback can affect both appearance and layout.

### Hinting vs. Antialiasing

Hinting attempts to improve how glyph geometry aligns
with the pixel grid.

Antialiasing reduces the appearance of jagged edges.

These are distinct operations, although both influence
the appearance of rendered text.

---

## 18. Typography in CSS

A practical example:

```css
.heading {
    font-family: "Inter", sans-serif;
    font-size: 2rem;
    font-weight: 700;
    font-style: normal;

    line-height: 1.2;
    letter-spacing: -0.02em;

    font-kerning: normal;
    font-optical-sizing: auto;
}
```

### Property Terminology

| CSS Property              | Typographic Concept                              |
| ------------------------- | ------------------------------------------------ |
| `font-family`             | Family selection and fallback.                   |
| `font-size`               | Nominal type size.                               |
| `font-weight`             | Weight selection.                                |
| `font-style`              | Upright, italic, or oblique selection.           |
| `font-stretch`            | Width-related face selection.                    |
| `line-height`             | Line box height and vertical text rhythm.        |
| `letter-spacing`          | Tracking.                                        |
| `word-spacing`            | Interword spacing adjustments.                   |
| `font-kerning`            | Kerning behavior.                                |
| `font-optical-sizing`     | Automatic optical-size selection when supported. |
| `font-feature-settings`   | Low-level OpenType feature controls.             |
| `font-variation-settings` | Low-level variable-font axis controls.           |

CSS property behavior is determined by the CSS specifications
and available font resources.

For example, `font-weight: 700` requests a bold weight,
but the actual result depends on the available faces
and browser font-matching behavior.

---

## 19. Recommended Asset Organization

A practical directory structure for managing typography
within a visual identity system:

```text
brand/
├── typography/
│   │
│   ├── fonts/
│   │   ├── desktop/
│   │   └── web/
│   │
│   ├── specimens/
│   │   ├── headings/
│   │   ├── body/
│   │   └── numerals/
│   │
│   ├── guidelines/
│   │   ├── families.md
│   │   ├── type-scale.md
│   │   ├── weights.md
│   │   ├── spacing.md
│   │   └── licensing.md
│   │
│   └── examples/
│       ├── css/
│       └── print/
│
└── logo/
    ├── wordmark.svg
    └── lockup-horizontal.svg
```

Only store font files where their licenses permit
the intended distribution.

For public repositories, documenting font dependencies
may be preferable to committing proprietary font binaries.

### Recommended Typography Specification

For a brand or product, document:

1. **Primary typeface:** Main identity and interface typography.
2. **Secondary typeface:** Complementary typography, if needed.
3. **Fallback families:** Approved substitutions.
4. **Supported faces:** Weights, styles, and widths.
5. **Type scale:** Approved sizes and hierarchical relationships.
6. **Line heights:** Recommended vertical spacing.
7. **Tracking:** Spacing adjustments for different applications.
8. **Numeral styles:** Lining, oldstyle, tabular, or proportional.
9. **OpenType features:** Required or recommended substitutions.
10. **Licensing:** Permitted use and redistribution.

---

## 20. Quick Reference

| When referring to...                                  | Prefer                     |
| ----------------------------------------------------- | -------------------------- |
| The underlying design of the letters                  | **Typeface**               |
| A software implementation of that design              | **Font**                   |
| A collection of related typographic designs           | **Type Family**            |
| A specific family member                              | **Face**                   |
| Thickness of strokes                                  | **Weight**                 |
| Upright, italic, or slanted construction              | **Style**                  |
| Horizontal proportions                                | **Width**                  |
| A visual representation used to render text           | **Glyph**                  |
| An abstract textual element                           | **Character**              |
| Spacing adjustment between particular glyph pairs     | **Kerning**                |
| Overall intercharacter spacing adjustment             | **Tracking**               |
| Baseline-to-baseline vertical spacing                 | **Leading**                |
| Nominal scale of type                                 | **Point Size / Font Size** |
| Size-dependent design adaptation                      | **Optical Size**           |
| Arrangement and visual treatment of type              | **Typography**             |
| Composition of text into a layout                     | **Typesetting**            |
| Design of reusable letterform systems                 | **Type Design**            |
| Custom-drawn letterforms for a particular application | **Lettering**              |
| Letterforms produced through writing                  | **Calligraphy**            |
| Recognition of individual letterforms                 | **Legibility**             |
| Comfortable processing of extended text               | **Readability**            |

---

## 21. Recommended Terminology Hierarchy

```text
TYPOGRAPHY
│
├── Type Design
│   │
│   ├── Typeface
│   │   └── Type Family
│   │       ├── Faces
│   │       │   ├── Weight
│   │       │   ├── Style
│   │       │   └── Width
│   │       │
│   │       └── Variable Design Space
│   │           ├── Weight Axis
│   │           ├── Width Axis
│   │           ├── Optical Size Axis
│   │           └── Custom Axes
│   │
│   ├── Glyph Design
│   │   ├── Letterform Anatomy
│   │   ├── Proportions
│   │   ├── Spacing
│   │   └── Optical Corrections
│   │
│   └── Font Production
│       ├── Font Files
│       ├── Character Coverage
│       ├── OpenType Layout
│       ├── Metrics
│       └── Hinting
│
├── Typesetting
│   ├── Typeface Selection
│   ├── Hierarchy
│   ├── Sizing
│   ├── Kerning
│   ├── Tracking
│   ├── Leading / Line Height
│   ├── Line Breaking
│   └── Page Composition
│
└── Related Disciplines
    ├── Lettering
    └── Calligraphy
```

This hierarchy describes conceptual relationships rather than
a rigid professional taxonomy.

Type design, lettering, and calligraphy can overlap,
and typography encompasses both type selection and composition.

---

## A Note on Terminology

Typography inherits terminology from metal type, phototypesetting,
desktop publishing, and modern software systems.

Some distinctions have changed over time.

For example, the historical definition of a *font* included a
specific size, whereas modern scalable digital fonts can render
at many sizes.

Similarly, *font family*, *type family*, *face*, and *style*
may have implementation-specific meanings across applications.

These definitions represent practical conventions rather than
an attempt to enforce one universal vocabulary.

**The goal is precision where it matters, without making
ordinary communication unnecessarily complicated.**