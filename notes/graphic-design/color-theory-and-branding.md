# Color Theory & Branding Terminology

> Type: reference
> Status: needs-review
> Updated: 2026-10-30
> Tags: branding, color, graphic-design

## A Practical Guide to Color, Harmony, Contrast, and Visual Identity

Color is one of the most recognizable components of visual identity.

Effective color selection involves more than choosing attractive hues.
A successful palette must balance visual harmony, contrast,
recognizability, accessibility, and reproducibility.

This guide establishes a practical vocabulary for understanding,
selecting, evaluating, and maintaining color systems in graphic design
and branding.

### Illustrative color-family examples

These CSS named-color values are examples, not unique definitions of broad
color families. Chips throughout this guide are illustrative examples, not
unique definitions; actual shades, mixtures, and appearances depend on context.

| Color family   | CSS color       | Hex value |
| -------------- | --------------- | --------- |
| Red            | red             | ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000` |
| Orange         | orange          | ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500` |
| Yellow         | yellow          | ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00` |
| Green          | green           | ![#008000](https://placehold.co/15x15/008000/008000.png) `#008000` |
| Cyan           | cyan            | ![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png) `#00FFFF` |
| Blue           | blue            | ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF` |
| Violet         | violet          | ![#EE82EE](https://placehold.co/15x15/EE82EE/EE82EE.png) `#EE82EE` |
| Magenta        | magenta         | ![#FF00FF](https://placehold.co/15x15/FF00FF/FF00FF.png) `#FF00FF` |
| Teal           | teal            | ![#008080](https://placehold.co/15x15/008080/008080.png) `#008080` |
| Black          | black           | ![#000000](https://placehold.co/15x15/000000/000000.png) `#000000` |
| White          | white           | ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF` |
| Gray           | gray            | ![#808080](https://placehold.co/15x15/808080/808080.png) `#808080` |
| Blue-green     | darkcyan        | ![#008B8B](https://placehold.co/15x15/008B8B/008B8B.png) `#008B8B` |
| Yellow-green   | yellowgreen     | ![#9ACD32](https://placehold.co/15x15/9ACD32/9ACD32.png) `#9ACD32` |
| Reddish violet | mediumvioletred | ![#C71585](https://placehold.co/15x15/C71585/C71585.png) `#C71585` |
| Bluish violet  | blueviolet      | ![#8A2BE2](https://placehold.co/15x15/8A2BE2/8A2BE2.png) `#8A2BE2` |
| Warm off-white | floralwhite     | ![#FFFAF0](https://placehold.co/15x15/FFFAF0/FFFAF0.png) `#FFFAF0` |
| Cool charcoal  | darkslategray   | ![#2F4F4F](https://placehold.co/15x15/2F4F4F/2F4F4F.png) `#2F4F4F` |

---

## 1. Core Terminology

| Term              | Definition                                                                                                 |
| ----------------- | ---------------------------------------------------------------------------------------------------------- |
| **Color**         | A visual perception produced by light and the human visual system.                                         |
| **Hue**           | The attribute identifying a color as red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000`, orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`, yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`, green ![#008000](https://placehold.co/15x15/008000/008000.png) `#008000`, blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`, etc.                                |
| **Saturation**    | The degree of colorfulness relative to a reference, with its precise meaning depending on the color model. |
| **Chroma**        | The colorfulness of a color relative to a similarly illuminated neutral reference.                         |
| **Lightness**     | How light or dark a color appears relative to a reference white ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`.                                           |
| **Value**         | A traditional art term describing the relative lightness or darkness of a color.                           |
| **Brightness**    | The perceived intensity of light; also used differently in various digital color models.                   |
| **Luminance**     | A physical, photometrically weighted measure of light intensity per unit area in a given direction.        |
| **Tint**          | A color mixed with white ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`, in traditional color terminology.                                                |
| **Shade**         | A color mixed with black ![#000000](https://placehold.co/15x15/000000/000000.png) `#000000`.                                                                                  |
| **Tone**          | A color modified with gray ![#808080](https://placehold.co/15x15/808080/808080.png) `#808080` or otherwise reduced in purity.                                                 |
| **Contrast**      | A perceptible difference between colors or visual elements.                                                |
| **Palette**       | A selected collection of colors used together.                                                             |
| **Color Harmony** | A relationship between colors perceived as visually coherent or pleasing.                                  |
| **Color Gamut**   | The range of colors representable by a device or color space.                                              |
| **Color Space**   | A defined system for representing colors numerically.                                                      |
| **Color Profile** | Data describing a device's or color space's color reproduction characteristics.                            |

> **Key distinction:** Hue determines the general color family.
> Lightness determines how light or dark it appears. Chroma or
> saturation describes its colorfulness, according to the model used.

These properties interact, but they are not interchangeable.

---

## 2. Hue, Saturation, Chroma, and Lightness

Consider several versions of orange
![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`:

- Bright, vivid orange ![#FF4500](https://placehold.co/15x15/FF4500/FF4500.png)
  `#FF4500`.
- Dark, muted orange ![#8B5A2B](https://placehold.co/15x15/8B5A2B/8B5A2B.png)
  `#8B5A2B`.
- Pale, pastel orange ![#FFDAB9](https://placehold.co/15x15/FFDAB9/FFDAB9.png)
  `#FFDAB9`.
- Deep, saturated orange
  ![#CC3300](https://placehold.co/15x15/CC3300/CC3300.png) `#CC3300`.

All may belong to the same general hue family, yet have
substantially different visual characteristics.

### Hue

Hue describes a color's position around a color wheel.

Common hue families include:

```text
Red → Orange → Yellow → Green → Cyan → Blue → Violet → Magenta
```

Illustrative chips: Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png)
`#FF0000`, Orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png)
`#FFA500`, Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png)
`#FFFF00`, Green ![#008000](https://placehold.co/15x15/008000/008000.png)
`#008000`, Cyan ![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png)
`#00FFFF`, Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png)
`#0000FF`, Violet ![#EE82EE](https://placehold.co/15x15/EE82EE/EE82EE.png)
`#EE82EE`, Magenta ![#FF00FF](https://placehold.co/15x15/FF00FF/FF00FF.png)
`#FF00FF`.

The exact positions of these colors depend on the color model.

### Saturation

Saturation describes the strength or purity of a color
within a particular color model.

A highly saturated color generally appears more colorful,
while a desaturated color appears closer to gray
![#808080](https://placehold.co/15x15/808080/808080.png) `#808080`.

However, saturation is not an absolute perceptual measurement.

For example, equal HSL saturation percentages do not guarantee
that two colors appear equally vivid.

### Chroma

Chroma measures colorfulness relative to a neutral reference
at comparable lightness.

It is particularly useful when constructing harmonious palettes
in perceptual color spaces such as OKLCH.

### Lightness

Lightness describes the perceived position of a color
between dark and light.

It strongly influences:

- Contrast.
- Visual hierarchy.
- Readability.
- Perceived weight.
- Background compatibility.

### Practical Distinction

| Property   | Primary Question                                     |
| ---------- | ---------------------------------------------------- |
| Hue        | What color family is this?                           |
| Saturation | How saturated is it within this color model?         |
| Chroma     | How colorful is it relative to a comparable neutral? |
| Lightness  | How light or dark does it appear?                    |

**Important:** A color can be highly saturated without appearing
particularly bright.

A deep, saturated blue ![#00008B](https://placehold.co/15x15/00008B/00008B.png)
`#00008B` may appear considerably darker than
a vivid yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png)
`#FFFF00`.

---

## 3. Color Models: RGB, CMYK, and RYB

Different color models describe different ways of combining
or representing color.

### RGB — Additive Color

RGB describes color through combinations of:

- Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000`
- Green ![#00FF00](https://placehold.co/15x15/00FF00/00FF00.png) `#00FF00`
- Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`

It is an additive model associated with light-emitting displays.

Conceptually, using illustrative full-intensity sRGB chips:

- Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000` +
  Green ![#00FF00](https://placehold.co/15x15/00FF00/00FF00.png) `#00FF00` =
  Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`
- Green ![#00FF00](https://placehold.co/15x15/00FF00/00FF00.png) `#00FF00` +
  Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF` =
  Cyan ![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png) `#00FFFF`
- Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF` +
  Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000` =
  Magenta ![#FF00FF](https://placehold.co/15x15/FF00FF/FF00FF.png) `#FF00FF`
- Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000` +
  Green ![#00FF00](https://placehold.co/15x15/00FF00/00FF00.png) `#00FF00` +
  Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF` =
  White ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`

These relationships assume suitable additive primaries.

RGB is commonly used for:

- Screens.
- Websites.
- Applications.
- Digital graphics.
- Electronic presentations.

**RGB is a color model, not a complete color space.**

For example, sRGB and Display P3 use different defined primaries
and represent different ranges of colors.

### CMYK — Subtractive Color

CMYK describes color through combinations of printing colorants:

- Cyan ![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png) `#00FFFF`
- Magenta ![#FF00FF](https://placehold.co/15x15/FF00FF/FF00FF.png) `#FF00FF`
- Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`
- Key (Black ![#000000](https://placehold.co/15x15/000000/000000.png) `#000000`)

It is primarily associated with process printing.

Conceptually, inks absorb portions of the incident light
rather than producing light directly.

CMYK reproduction depends on:

- Ink formulation.
- Paper.
- Printing process.
- Press characteristics.
- Color profiles.

A particular CMYK percentage combination does not necessarily
produce the same appearance on every printing system.

### RYB — Traditional Artist's Color Model

RYB uses:

- Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000`
- Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`
- Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`

This model is common in traditional art education and painting.

It is useful as a historical and conceptual framework for
discussing pigment mixing and color relationships.

However, RYB is not a precise physical model of color
and should not be confused with digital RGB or printing CMYK.

### Comparison

| Model | Primary Application       | Mixing Principle          |
| ----- | ------------------------- | ------------------------- |
| RGB   | Digital displays          | Additive                  |
| CMYK  | Process printing          | Subtractive               |
| RYB   | Traditional art education | Simplified pigment mixing |

**Practical rule:** Design digital palettes in a defined digital
color space. Evaluate printed reproduction separately.

---

## 4. Understanding the Color Wheel

A color wheel arranges hues in a circular sequence.

Its primary purpose is to visualize relationships between colors.

Traditional wheels often use RYB relationships, while digital
tools frequently use HSL, HSV, or perceptual color spaces.

The chosen wheel matters.

A 180-degree separation in one color model does not necessarily
produce the same pair of colors in another.

### Primary, Secondary, and Tertiary Colors

In traditional RYB terminology:

**Primary:**

- Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000`
- Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`
- Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`

**Secondary:**

- Orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`
- Green ![#008000](https://placehold.co/15x15/008000/008000.png) `#008000`
- Violet ![#EE82EE](https://placehold.co/15x15/EE82EE/EE82EE.png) `#EE82EE`

**Tertiary:**

Mixtures between neighboring primary and secondary colors.

Digital RGB uses different primaries and secondary colors.

These classifications are model-dependent, not universal
properties of individual hues.

---

## 5. Color Harmony

Color harmony refers to relationships among colors
that create an intentional visual composition.

Common harmony schemes are constructed using positions
around a color wheel.

These schemes provide useful starting points, not guarantees
of attractive or effective palettes.

### Monochromatic

A palette derived primarily from one hue.

The following illustrative chips approximate their stated values at 8-bit sRGB
precision. Variation comes from changes in:

- Lightness.
  - Low → high, with the same HSL hue and saturation:
    ![Low lightness](https://placehold.co/15x15/804000/804000.png)
    ![Medium lightness](https://placehold.co/15x15/FF8000/FF8000.png)
    ![High lightness](https://placehold.co/15x15/FFBF80/FFBF80.png)
- Chroma.
  - Low → high, with the same OKLCH lightness and hue:
    ![Low chroma](https://placehold.co/15x15/AE9A8D/AE9A8D.png)
    ![Medium chroma](https://placehold.co/15x15/C6916E/C6916E.png)
    ![High chroma](https://placehold.co/15x15/DC8748/DC8748.png)
- Saturation.
  - Low → high, with the same HSL hue and lightness:
    ![Low saturation](https://placehold.co/15x15/808080/808080.png)
    ![Medium saturation](https://placehold.co/15x15/BF8040/BF8040.png)
    ![High saturation](https://placehold.co/15x15/FF8000/FF8000.png)
- Opacity.
  - Low → high, composited over white:
    ![Low opacity on white](https://placehold.co/15x15/FFDFBF/FFDFBF.png)
    ![Medium opacity on white](https://placehold.co/15x15/FFBF80/FFBF80.png)
    ![Full opacity](https://placehold.co/15x15/FF8000/FF8000.png)

**Advantages:**

- Strong coherence.
- Simple hierarchy.
- Consistent identity.

**Challenges:**

- Limited categorical differentiation.
- Potentially insufficient contrast.

### Analogous

Colors located near one another on a color wheel.

Example:

```text
Blue → Cyan → Teal
```

Illustrative chips: Blue
![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`, Cyan
![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png) `#00FFFF`, Teal
![#008080](https://placehold.co/15x15/008080/008080.png) `#008080`.

**Advantages:**

- Natural visual continuity.
- Relatively easy coordination.
- Cohesive atmosphere.

**Challenges:**

- Colors may become difficult to distinguish.
- A separate accent may be needed.

### Complementary

Two colors located approximately opposite one another
on a chosen color wheel.

Example in a traditional artist's wheel:

```text
Blue ↔ Orange
```

Illustrative chips: Blue
![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`, Orange
![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`.

**Advantages:**

- Strong visual differentiation.
- Useful accent relationships.
- Potentially striking brand identity.

**Challenges:**

- Equal visual emphasis can create competition.
- High saturation in both colors may feel aggressive.

### Split-Complementary

One primary hue combined with hues on either side
of its approximate complement.

This can preserve visual contrast while allowing
more nuanced relationships.

Illustrative HSL example (hues 0°, 150°, and 210°):

- Split-complementary:
  ![Red, hue 0°](https://placehold.co/15x15/FF0000/FF0000.png)
  ![Spring green, hue 150°](https://placehold.co/15x15/00FF80/00FF80.png)
  ![Azure, hue 210°](https://placehold.co/15x15/0080FF/0080FF.png)

### Triadic

Three hues distributed approximately evenly
around a color wheel.

```text
120° separation in an evenly parameterized hue wheel
```

Triadic palettes offer variety but require careful
control of saturation, lightness, and visual emphasis.

Illustrative HSL example (hues 0°, 120°, and 240°):

- Triadic:
  ![Red, hue 0°](https://placehold.co/15x15/FF0000/FF0000.png)
  ![Green, hue 120°](https://placehold.co/15x15/00FF00/00FF00.png)
  ![Blue, hue 240°](https://placehold.co/15x15/0000FF/0000FF.png)

### Tetradic

Four hues commonly arranged as two complementary pairs.

A tetradic scheme is often represented as a rectangle
or square on the color wheel.

The square arrangement uses approximately 90-degree intervals.

Illustrative HSL examples:

- Rectangle, hues 0°, 60°, 180°, and 240°:
  ![Red, hue 0°](https://placehold.co/15x15/FF0000/FF0000.png)
  ![Yellow, hue 60°](https://placehold.co/15x15/FFFF00/FFFF00.png)
  ![Cyan, hue 180°](https://placehold.co/15x15/00FFFF/00FFFF.png)
  ![Blue, hue 240°](https://placehold.co/15x15/0000FF/0000FF.png)
- Square, hues 0°, 90°, 180°, and 270°:
  ![Red, hue 0°](https://placehold.co/15x15/FF0000/FF0000.png)
  ![Chartreuse, hue 90°](https://placehold.co/15x15/80FF00/80FF00.png)
  ![Cyan, hue 180°](https://placehold.co/15x15/00FFFF/00FFFF.png)
  ![Violet, hue 270°](https://placehold.co/15x15/8000FF/8000FF.png)

### Hexadic

Six hues distributed around a color wheel.

In a regular six-hue arrangement:

```text
360° / 6 = 60°
```

Illustrative HSL examples, each spaced by 60°:

- Starting at hue 0°:
  ![Red, hue 0°](https://placehold.co/15x15/FF0000/FF0000.png)
  ![Yellow, hue 60°](https://placehold.co/15x15/FFFF00/FFFF00.png)
  ![Green, hue 120°](https://placehold.co/15x15/00FF00/00FF00.png)
  ![Cyan, hue 180°](https://placehold.co/15x15/00FFFF/00FFFF.png)
  ![Blue, hue 240°](https://placehold.co/15x15/0000FF/0000FF.png)
  ![Magenta, hue 300°](https://placehold.co/15x15/FF00FF/FF00FF.png)
- Starting at hue 30°:
  ![Orange, hue 30°](https://placehold.co/15x15/FF8000/FF8000.png)
  ![Chartreuse, hue 90°](https://placehold.co/15x15/80FF00/80FF00.png)
  ![Spring green, hue 150°](https://placehold.co/15x15/00FF80/00FF80.png)
  ![Azure, hue 210°](https://placehold.co/15x15/0080FF/0080FF.png)
  ![Violet, hue 270°](https://placehold.co/15x15/8000FF/8000FF.png)
  ![Rose, hue 330°](https://placehold.co/15x15/FF0080/FF0080.png)

Hexadic palettes provide substantial variety and may be useful
for multi-product identities, data visualization, or complex
design systems.

However, six equally spaced hues are not automatically
equally vivid, harmonious, or perceptually distinct.

### Harmony Summary

| Scheme              | Typical Hue Count | General Character    |
| ------------------- | ----------------: | -------------------- |
| Monochromatic       | 1                 | Cohesive, restrained |
| Analogous           | 2–5               | Related, continuous  |
| Complementary       | 2                 | Contrasting          |
| Split-Complementary | 3                 | Contrasting, nuanced |
| Triadic             | 3                 | Varied, balanced     |
| Tetradic            | 4                 | Flexible, complex    |
| Hexadic             | 6                 | Diverse, systematic  |

Hue count refers to the conceptual arrangement, not the total
number of colors in a finished palette.

A monochromatic palette may contain dozens of swatches.

---

## 6. Hue Harmony vs. Perceptual Harmony

This is an important distinction in contemporary design.

Two palettes can follow exactly the same hue geometry
yet appear dramatically different.

Consider a triadic palette with three evenly spaced hues.

Mathematically, the hues may be separated by equal angles.

Perceptually, however:

- Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00` may
  appear much brighter than blue
  ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`.
- Orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500` may
  attract more attention than violet
  ![#EE82EE](https://placehold.co/15x15/EE82EE/EE82EE.png) `#EE82EE`.
- Some hues may tolerate greater chroma than others.
- Different colors may have substantially different contrast.

### Geometric Harmony

Describes mathematical relationships between hue angles.

### Perceptual Harmony

Describes how colors actually appear together.

Perceptual harmony depends on:

- Lightness.
- Chroma.
- Contrast.
- Relative area.
- Surrounding colors.
- Viewing conditions.

**Equal hue spacing does not imply equal perceptual spacing.**

This is especially important when building palettes containing
five, six, or more distinct colors.

---

## 7. Color Temperature

Colors are often described as warm or cool.

### Warm Colors

Commonly associated with:

- Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000`.
- Orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`.
- Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`.

### Cool Colors

Commonly associated with:

- Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`.
- Cyan ![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png) `#00FFFF`.
- Blue-green ![#008B8B](https://placehold.co/15x15/008B8B/008B8B.png) `#008B8B`.

However, perceived warmth is contextual.

A reddish violet ![#C71585](https://placehold.co/15x15/C71585/C71585.png)
`#C71585` may appear warmer than a bluish violet
![#8A2BE2](https://placehold.co/15x15/8A2BE2/8A2BE2.png) `#8A2BE2`.

A yellow-green ![#9ACD32](https://placehold.co/15x15/9ACD32/9ACD32.png)
`#9ACD32` may appear warmer than a blue-green
![#008B8B](https://placehold.co/15x15/008B8B/008B8B.png) `#008B8B`.

Color temperature in graphic design is a relative visual
description, not necessarily a literal measurement
of physical color temperature.

### Branding Applications

Warm colors are often used to create impressions of:

- Energy.
- Activity.
- Urgency.
- Approachability.

Cool colors are often used to create impressions of:

- Precision.
- Calm.
- Stability.
- Technical sophistication.

These associations are contextual and culturally influenced.

They should not be treated as universal psychological laws.

---

## 8. Contrast and Visual Hierarchy

Contrast allows visual elements to be distinguished.

It is fundamental to both accessibility and composition.

### Lightness Contrast

Differences between light and dark colors.

For text and interfaces, lightness or luminance-related
contrast is usually especially important.

### Hue Contrast

Differences in color family.

For example:

```text
Orange vs. Blue
```

Illustrative chips: Orange
![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`, Blue
![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`.

Strong hue contrast does not guarantee sufficient
text readability.

### Chroma Contrast

Differences in colorfulness.

For example:

```text
Vivid Orange vs. Muted Orange
```

Illustrative chips: vivid orange
![#FF4500](https://placehold.co/15x15/FF4500/FF4500.png) `#FF4500`; muted orange
![#C78A62](https://placehold.co/15x15/C78A62/C78A62.png) `#C78A62`.

### Simultaneous Contrast

A color can appear different depending on its surroundings.

The same gray ![#808080](https://placehold.co/15x15/808080/808080.png) `#808080`
may appear lighter against black
![#000000](https://placehold.co/15x15/000000/000000.png) `#000000`
and darker against white
![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`.

Nearby colors can also influence perceived hue
and saturation.

### Contrast Summary

| Contrast Type | Typical Design Application        |
| ------------- | --------------------------------- |
| Lightness     | Text, interfaces, hierarchy       |
| Hue           | Category differentiation, accents |
| Chroma        | Emphasis, visual restraint        |
| Warm–Cool     | Mood, separation                  |
| Simultaneous  | Contextual color evaluation       |

**Practical rule:** Do not rely on hue contrast alone
when legibility is important.

---

## 9. Accessible Color Design

Brand colors should remain usable across interfaces,
documents, diagrams, and different viewing conditions.

### WCAG Contrast Ratios

WCAG 2.2 Level AA establishes the following commonly
applicable minimum contrast ratios:

| Content                                     | Minimum Contrast |
| ------------------------------------------- | ---------------: |
| Normal text                                 | 4.5:1            |
| Large text                                  | 3:1              |
| Essential graphical elements                | 3:1              |
| Required visual indicators of UI components | 3:1              |

Large text is generally defined as at least 18 pt regular
or 14 pt bold, or an equivalent size.

These are minimums, not ideal design targets.

The requirements include specific exceptions.
For example, text forming part of a logo or brand name
is exempt from the WCAG text-contrast requirement.

Nevertheless, a visually inaccessible logo is still
a practical branding problem.

### Contrast Is Pairwise

A color is not inherently accessible.

Accessibility depends on the relationship between
the foreground and background colors.

For example, an orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png)
`#FFA500` suitable for a large icon
on a dark background may fail as small text on white
![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`.

### Color Vision Deficiency

Some viewers cannot reliably distinguish certain
color combinations.

Common difficulties include discrimination among
particular reds and greens.

Therefore:

- Do not use color as the only indicator of meaning.
- Combine color with labels, shapes, or patterns.
- Test important palettes under simulated color vision deficiencies.
- Verify actual contrast rather than relying on appearance alone.

For example:

```text
Poor:
Red = Error
Green = Success

Better:
Red + Error Icon + "Failed"
Green + Checkmark + "Passed"
```

Illustrative chips: Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png)
`#FF0000`, Green ![#008000](https://placehold.co/15x15/008000/008000.png)
`#008000`.

Accessibility should be evaluated in the actual design,
not merely by inspecting the palette.

---

## 10. Color Psychology and Brand Associations

Colors can evoke associations, but their meanings are
not universally fixed.

Common branding associations include:

| Color       | Common Associations               |
| ----------- | --------------------------------- |
| Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png) `#FF0000`         | Energy, urgency, intensity        |
| Orange ![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`      | Activity, warmth, enthusiasm      |
| Yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png) `#FFFF00`      | Optimism, attention, brightness   |
| Green ![#008000](https://placehold.co/15x15/008000/008000.png) `#008000`       | Nature, growth, health            |
| Cyan ![#00FFFF](https://placehold.co/15x15/00FFFF/00FFFF.png) `#00FFFF` / Teal ![#008080](https://placehold.co/15x15/008080/008080.png) `#008080` | Technology, clarity, freshness    |
| Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`        | Stability, trust, professionalism |
| Violet ![#EE82EE](https://placehold.co/15x15/EE82EE/EE82EE.png) `#EE82EE`      | Imagination, distinction, luxury  |
| Magenta ![#FF00FF](https://placehold.co/15x15/FF00FF/FF00FF.png) `#FF00FF`     | Creativity, expressiveness        |
| Black ![#000000](https://placehold.co/15x15/000000/000000.png) `#000000`       | Authority, sophistication         |
| White ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`       | Simplicity, cleanliness           |
| Gray ![#808080](https://placehold.co/15x15/808080/808080.png) `#808080`        | Neutrality, restraint             |

These are common conventions, not scientific guarantees.

A color's meaning can change with:

- Culture.
- Industry.
- Saturation and lightness.
- Typography.
- Composition.
- Historical associations.
- Competitor identities.

**A distinctive, consistently used color can become more
valuable than a theoretically appropriate color.**

---

## 11. Constructing a Brand Palette

A brand palette is more than a collection of attractive colors.

Each color should have an intentional role.

### Primary Color

The main identifying color associated with the brand.

It often appears in:

- Logos.
- Major headings.
- Key graphical elements.
- Important branded surfaces.

### Secondary Colors

Supporting colors that expand the visual vocabulary.

They may be used in:

- Product differentiation.
- Illustrations.
- Supporting graphics.
- Section identities.

### Accent Colors

Colors used selectively to attract attention or create emphasis.

An accent color does not necessarily need to be highly saturated.

Its effectiveness depends on contrast with the surrounding composition.

### Neutral Colors

Colors used for structure rather than strong brand expression.

Common examples:

- White ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`.
- Black ![#000000](https://placehold.co/15x15/000000/000000.png) `#000000`.
- Gray ![#808080](https://placehold.co/15x15/808080/808080.png) `#808080`.
- Warm off-white ![#FFFAF0](https://placehold.co/15x15/FFFAF0/FFFAF0.png)
  `#FFFAF0`.
- Cool charcoal ![#2F4F4F](https://placehold.co/15x15/2F4F4F/2F4F4F.png)
  `#2F4F4F`.

Neutrals are especially important for typography,
backgrounds, separators, and layout hierarchy.

### Semantic Colors

Colors assigned specific meanings in an interface.

Examples:

- Success.
- Warning.
- Error.
- Information.

Semantic colors should not automatically be identical
to the brand's decorative colors.

### Recommended Hierarchy

```text
BRAND COLOR SYSTEM
│
├── Identity Colors
│   ├── Primary
│   ├── Secondary
│   └── Accent
│
├── Neutral Colors
│   ├── Background
│   ├── Surface
│   ├── Border
│   └── Text
│
├── Semantic Colors
│   ├── Success
│   ├── Warning
│   ├── Error
│   └── Information
│
└── Data Visualization Colors
    ├── Categorical
    ├── Sequential
    └── Diverging
```

---

## 12. Color Proportion and Visual Weight

A palette should not necessarily use its constituent colors
in equal proportions.

A traditional design heuristic is the **60–30–10 rule**:

- 60% dominant color.
- 30% supporting color.
- 10% accent color.

This can be useful when constructing simple compositions.

However, these proportions are not a law of color theory.

A six-color palette does not require six equal areas.

### Visual Weight

Different colors attract different amounts of attention.

Visual weight is affected by:

- Saturation.
- Lightness.
- Contrast.
- Area.
- Placement.
- Surrounding colors.

For example, a small vivid orange
![#FF4500](https://placehold.co/15x15/FF4500/FF4500.png) `#FF4500` element may
compete
with a much larger muted blue
![#708090](https://placehold.co/15x15/708090/708090.png) `#708090` element.

This means that color proportions should be adjusted
according to perceived emphasis, not merely numerical area.

**Equal area does not guarantee equal visual weight.**

---

## 13. Tints, Shades, and Tonal Scales

A single brand color often needs multiple variations.

### Tint

A lighter version of a color, traditionally produced
by mixing it with white ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png)
`#FFFFFF`.

### Shade

A darker version, traditionally produced
by mixing it with black ![#000000](https://placehold.co/15x15/000000/000000.png)
`#000000`.

### Tone

A modified or muted version of a color,
traditionally produced by adding gray
![#808080](https://placehold.co/15x15/808080/808080.png) `#808080`.

In digital color systems, these effects may instead
be constructed using controlled changes in lightness
and chroma.

### Tonal Scales

A tonal scale provides multiple lightness levels
for a single color family.

Example:

```text
Orange
├── 50    Very Light
├── 100
├── 200
├── 300
├── 400
├── 500   Base
├── 600
├── 700
├── 800
└── 900   Very Dark
```

Illustrative chips: Orange
![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`.

The numerical labels are conventions,
not universal measurements of lightness.

A carefully constructed scale should be evaluated
for perceptual consistency and contrast.

Simply interpolating between a color and white
![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF` or black
![#000000](https://placehold.co/15x15/000000/000000.png) `#000000`
in ordinary RGB may produce undesirable shifts.

---

## 14. Light Mode vs. Dark Mode

Light and dark interfaces often require different
color adjustments.

Simply inverting the background is rarely sufficient.

### Light Mode

Common characteristics:

- Light surfaces.
- Dark text.
- Moderate accent saturation.
- Strong control of lightness contrast.

Highly saturated colors can feel visually intense
against white ![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png) `#FFFFFF`
backgrounds.

### Dark Mode

Common characteristics:

- Dark surfaces.
- Light text.
- Carefully controlled chroma.
- Avoidance of excessive visual glare.

Some colors need reduced chroma or adjusted lightness
to remain comfortable against dark backgrounds.

### Brand Consistency

The same brand hue can be expressed through different
lightness and chroma values.

For example:

```text
Brand Orange
│
├── Light Mode Variant
│   ├── Appropriate contrast
│   └── Controlled chroma
│
└── Dark Mode Variant
    ├── Appropriate contrast
    └── Adjusted lightness / chroma
```

Illustrative chips: Orange
![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`.

These variants need not have identical numerical color values.

The goal is consistent perceived identity,
not necessarily identical RGB values.

---

## 15. Digital Color Representations

Several systems are commonly used to describe digital colors.

### Hexadecimal RGB

Example:

```text
#FF8000
```

Orange example: ![#FF8000](https://placehold.co/15x15/FF8000/FF8000.png)
`#FF8000`.

This represents:

```text
Red   = 255
Green = 128
Blue  = 0
```

Illustrative chips: Red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png)
`#FF0000`, Green ![#008000](https://placehold.co/15x15/008000/008000.png)
`#008000`, Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png)
`#0000FF`.

Six-digit hexadecimal color notation ordinarily expresses
sRGB channel values in web contexts.

### HSL

HSL stands for:

- Hue.
- Saturation.
- Lightness.

Example:

```css
color: hsl(30 100% 50%);
```

Orange example: ![#FF8000](https://placehold.co/15x15/FF8000/FF8000.png)
`hsl(30 100% 50%)`, equivalent to `#FF8000` in sRGB.

HSL is intuitive for manipulating hues,
but its lightness and saturation are not perceptually uniform.

Two colors with identical HSL lightness values
can appear dramatically different in brightness.

### HSV / HSB

HSV stands for:

- Hue.
- Saturation.
- Value.

HSB commonly refers to:

- Hue.
- Saturation.
- Brightness.

These models are widely used in graphical color pickers.

Their value or brightness coordinates should not be confused
with standardized perceptual lightness.

### CIELAB

CIELAB describes colors through:

- L*: Lightness.
- a*: Green ![#008000](https://placehold.co/15x15/008000/008000.png)
  `#008000`–red ![#FF0000](https://placehold.co/15x15/FF0000/FF0000.png)
  `#FF0000` opponent dimension.
- b*: Blue ![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png)
  `#0000FF`–yellow ![#FFFF00](https://placehold.co/15x15/FFFF00/FFFF00.png)
  `#FFFF00` opponent dimension.

It was developed to provide a more perceptually meaningful
representation of color differences.

### OKLab and OKLCH

OKLab is a newer perceptually oriented color space.

OKLCH expresses colors using:

- L: Perceived lightness.
- C: Chroma.
- H: Hue.

Example:

```css
color: oklch(70% 0.18 55);
```

Orange example: `oklch(70% 0.18 55)`. An illustrative sRGB approximation is
![#F07800](https://placehold.co/15x15/F07800/F07800.png) `#F07800`.

This example is outside the sRGB gamut, so its displayed appearance depends
on the display and browser's gamut mapping.

OKLCH is especially useful for:

- Constructing tonal scales.
- Controlling perceived lightness.
- Adjusting chroma.
- Developing coordinated palettes.
- Comparing colors more consistently.

However, OKLCH is not perfectly perceptually uniform,
and not every coordinate corresponds to a displayable color.

### Comparison

| Representation | Strength                               | Limitation                                       |
| -------------- | -------------------------------------- | ------------------------------------------------ |
| Hex RGB        | Compact, interoperable                 | Difficult to manipulate intuitively              |
| RGB            | Direct channel representation          | Not perceptually uniform                         |
| HSL            | Intuitive hue manipulation             | Lightness and saturation are perceptually uneven |
| HSV / HSB      | Familiar color picker controls         | Not perceptually uniform                         |
| CIELAB         | Perceptually oriented color comparison | More complex                                     |
| OKLCH          | Intuitive perceptual adjustments       | Requires gamut awareness                         |

**Practical recommendation:** Use OKLCH or another perceptual
color space when developing palette relationships, then define
appropriate output values for the intended medium.

---

## 16. Color Difference and Palette Mathematics

Color relationships can be evaluated mathematically.

However, different mathematical measurements answer
different questions.

### Hue Separation

Hue separation measures the angular distance
between two colors on a particular hue wheel.

For hue angles measured in degrees:

```text
ΔH = min(|H1 - H2|, 360° - |H1 - H2|)
```

This produces the smaller angular separation.

Hue separation is useful for examining palette geometry.

It does not directly measure perceived color difference.

### Perceptual Color Difference

Perceptual color spaces allow colors to be compared
using multidimensional distances.

For example, Euclidean distance in OKLab is:

```text
ΔE_OK = sqrt(
    (L1 - L2)² +
    (a1 - a2)² +
    (b1 - b2)²
)
```

Larger distances generally indicate greater perceptual
difference within this model.

However, such measurements are approximations
and should not be treated as universal visibility thresholds.

### Contrast Ratio

WCAG contrast evaluates differences in relative luminance.

It answers a different question from hue separation
or perceptual color distance.

### Comparison

| Measurement               | Primary Purpose                                    |
| ------------------------- | -------------------------------------------------- |
| Hue Separation            | Evaluate relationships around a color wheel        |
| Chroma Difference         | Compare colorfulness                               |
| Lightness Difference      | Compare perceived light/dark characteristics       |
| Perceptual Color Distance | Estimate visual dissimilarity                      |
| WCAG Contrast Ratio       | Evaluate contrast against accessibility thresholds |

A color pair can have substantial hue separation
while remaining inadequate for readable text.

Likewise, two colors with different hues may have
similar perceived lightness.

---

## 17. RGB, Print, and Color Management

A brand color seen on a monitor may not reproduce
identically in print.

### sRGB

A standardized RGB color space widely used
for web graphics and general digital interchange.

### Display P3

A wider-gamut RGB color space supported
by many modern displays.

It can represent some colors unavailable in sRGB.

### CMYK

A printing color model used for process printing.

Its reproducible gamut depends on the printing conditions.

### Spot Colors

Specially specified inks used independently of,
or in addition to, process CMYK inks.

A spot-color specification can improve consistency
for certain brand colors and printing applications.

Pantone is a widely used commercial color specification system.

### ICC Profiles

ICC profiles describe color characteristics
for color spaces and devices.

Color management systems use these profiles
to help translate colors between different conditions.

### Gamut Mapping

When a color cannot be reproduced in a target color space,
it must be mapped or adjusted.

This may change:

- Hue.
- Chroma.
- Lightness.

### Practical Recommendations

- Define a canonical digital color specification.
- Maintain approved print color specifications.
- Use suitable ICC profiles.
- Soft-proof or proof important printed materials.
- Do not assume direct RGB-to-CMYK conversion preserves appearance.
- Do not assume all monitors reproduce colors identically.

**A brand color is a target appearance, not merely a hexadecimal code.**

---

## 18. Color in Data Visualization

Brand palettes are often reused in charts,
but data visualization introduces different requirements.

### Categorical Palettes

Used to distinguish unrelated categories.

Example:

```text
Product A = Orange
Product B = Blue
Product C = Green
Product D = Violet
```

Illustrative chips: Orange
![#FFA500](https://placehold.co/15x15/FFA500/FFA500.png) `#FFA500`, Blue
![#0000FF](https://placehold.co/15x15/0000FF/0000FF.png) `#0000FF`, Green
![#008000](https://placehold.co/15x15/008000/008000.png) `#008000`, Violet
![#EE82EE](https://placehold.co/15x15/EE82EE/EE82EE.png) `#EE82EE`.

Each color should be reasonably distinguishable
from the others in the intended context.

### Sequential Palettes

Used to represent ordered magnitudes.

Example:

```text
Low → Medium → High
```

A sequential palette typically uses a progressive
change in perceived lightness.

### Diverging Palettes

Used to represent values around a meaningful midpoint.

Example:

```text
Negative ← Neutral → Positive
```

The midpoint should be visually distinguishable,
and both sides should communicate comparable progression.

### Brand Identity vs. Data Clarity

A brand's primary colors may not form
an effective categorical or sequential palette.

Therefore, it is reasonable to maintain a dedicated
data visualization palette derived from,
but not identical to, the main brand palette.

---

## 19. Common Color Design Mistakes

| Mistake                                             | Why It Fails                                           |
| --------------------------------------------------- | ------------------------------------------------------ |
| Equal saturation percentages across hues            | Does not produce equal perceived vividness.            |
| Equal hue spacing alone                             | Does not guarantee perceptual harmony.                 |
| Using every palette color equally                   | Creates competing visual priorities.                   |
| Relying only on color for meaning                   | Creates accessibility problems.                        |
| Assuming hue contrast ensures legibility            | Hue differences do not guarantee luminance contrast.   |
| Using one accent value in light and dark modes      | May produce inconsistent emphasis or contrast.         |
| Treating color psychology as universal              | Ignores culture, context, and brand associations.      |
| Converting RGB directly to CMYK without proofing    | Can produce unexpected printed results.                |
| Treating hex codes as complete color specifications | Ignores color spaces, devices, and viewing conditions. |
| Building scales through naive RGB interpolation     | Can create uneven lightness or unexpected hue shifts.  |
| Adding colors without assigning roles               | Weakens consistency and hierarchy.                     |

---

## 20. Recommended Brand Color Specification

A practical brand palette should document more than swatches.

For each color, record:

| Property               | Description                                         |
| ---------------------- | --------------------------------------------------- |
| Name                   | Human-readable identifier                           |
| Role                   | Primary, secondary, accent, neutral, semantic, etc. |
| Digital Value          | Defined RGB/hex value and color space               |
| Perceptual Coordinates | Optional OKLCH or Lab values                        |
| Light Variant          | Approved use on light backgrounds                   |
| Dark Variant           | Approved use on dark backgrounds                    |
| Contrast               | Verified foreground/background combinations         |
| Print Specification    | Approved CMYK or spot-color specification           |
| Restrictions           | Inappropriate backgrounds or combinations           |

### Example Token Naming

```text
color/
├── brand/
│   ├── primary
│   ├── secondary
│   └── accent
│
├── neutral/
│   ├── 50
│   ├── 100
│   ├── ...
│   └── 900
│
├── semantic/
│   ├── success
│   ├── warning
│   ├── error
│   └── information
│
└── chart/
    ├── categorical/
    ├── sequential/
    └── diverging/
```

Separate underlying palette values from semantic usage.

For example:

```css
:root {
    /* Palette tokens */
    --orange-500: #E87524;
    --neutral-950: #141414;

    /* Semantic tokens */
    --brand-primary: var(--orange-500);
    --surface-primary: #FFFFFF;
    --text-primary: var(--neutral-950);
}
```

Example palette colors: orange
![#E87524](https://placehold.co/15x15/E87524/E87524.png)
`#E87524`, dark neutral ![#141414](https://placehold.co/15x15/141414/141414.png)
`#141414`, and white surface
![#FFFFFF](https://placehold.co/15x15/FFFFFF/FFFFFF.png)
`#FFFFFF`.

The example values are illustrative,
not a validated accessible palette.

A dark theme can redefine semantic tokens
without changing the underlying brand identity.

---

## 21. Practical Palette Development Workflow

### Step 1 — Identify the Brand

Determine the desired characteristics of the identity.

Consider:

- Industry.
- Audience.
- Existing recognition.
- Competitor differentiation.
- Intended applications.

### Step 2 — Choose an Anchor Color

Select a primary color representing the identity.

Evaluate it in realistic contexts rather than isolation.

### Step 3 — Explore Hue Relationships

Consider complementary, analogous, triadic,
or more complex relationships.

Treat these as candidate structures, not final answers.

### Step 4 — Harmonize Perceptually

Adjust:

- Lightness.
- Chroma.
- Relative visual weight.

Avoid assuming equal numerical saturation
produces equal visual intensity.

### Step 5 — Establish Hierarchy

Assign each color a purpose.

Determine which colors dominate,
which support, and which provide accents.

### Step 6 — Develop Light and Dark Variants

Evaluate colors against the actual backgrounds
on which they will be used.

### Step 7 — Verify Accessibility

Check contrast and color differentiation.

Test meaningful combinations, not only individual swatches.

### Step 8 — Test Real Applications

Evaluate the palette in:

- Logos.
- Websites.
- Applications.
- Presentations.
- Charts.
- Printed materials.

### Step 9 — Document the System

Record approved values, roles, variants,
and usage restrictions.

---

## 22. Quick Reference

| When referring to...                          | Prefer                          |
| --------------------------------------------- | ------------------------------- |
| The basic color family                        | **Hue**                         |
| Colorfulness within a model such as HSL       | **Saturation**                  |
| Colorfulness relative to a comparable neutral | **Chroma**                      |
| Perceived light/dark appearance               | **Lightness**                   |
| Traditional artistic light/dark description   | **Value**                       |
| Difference between visual elements            | **Contrast**                    |
| Selected group of colors                      | **Palette**                     |
| Relationship among selected hues              | **Color Harmony**               |
| Dominant identity color                       | **Primary Color**               |
| Supporting brand colors                       | **Secondary Colors**            |
| Selective emphasis colors                     | **Accent Colors**               |
| Structural background and text colors         | **Neutrals**                    |
| Colors assigned interface meanings            | **Semantic Colors**             |
| Ordered variations of one color family        | **Tonal Scale**                 |
| Range of reproducible colors                  | **Color Gamut**                 |
| Defined numerical representation of color     | **Color Space**                 |
| Description of reproduction characteristics   | **Color Profile**               |
| Approximate visual difference between colors  | **Perceptual Color Difference** |
| Conversion between device conditions          | **Color Management**            |

---

## 23. Recommended Terminology Hierarchy

```text
COLOR DESIGN
│
├── Color Theory
│   ├── Hue Relationships
│   │   ├── Monochromatic
│   │   ├── Analogous
│   │   ├── Complementary
│   │   ├── Split-Complementary
│   │   ├── Triadic
│   │   ├── Tetradic
│   │   └── Hexadic
│   │
│   ├── Color Properties
│   │   ├── Hue
│   │   ├── Saturation
│   │   ├── Chroma
│   │   └── Lightness
│   │
│   └── Visual Relationships
│       ├── Contrast
│       ├── Harmony
│       ├── Temperature
│       └── Visual Weight
│
├── Color Science
│   ├── Color Models
│   │   ├── RGB
│   │   └── CMYK
│   │
│   ├── Color Spaces
│   │   ├── sRGB
│   │   ├── Display P3
│   │   ├── CIELAB
│   │   └── OKLab / OKLCH
│   │
│   ├── Perceptual Difference
│   └── Color Management
│
└── Brand Color System
    ├── Identity Palette
    ├── Neutral Palette
    ├── Semantic Palette
    ├── Data Visualization Palette
    ├── Light / Dark Variants
    └── Usage Guidelines
```

---

## 24. References

The following resources provide further technical information.

### Color Representation

- [MDN — CSS Color Values](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Colors/Color_values)
- [MDN — OKLCH](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/oklch)
- [CSS Color Module Level 4](https://www.w3.org/TR/css-color-4/)
- [CSS Color Module Level 5](https://www.w3.org/TR/css-color-5/)

### Accessibility

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Understanding Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [Understanding Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast)
- [Understanding Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

### Color Management

- [International Color Consortium](https://www.color.org/)

---

## A Note on Color Theory

Traditional color theory is a useful design framework,
but it should not be mistaken for a complete mathematical
or scientific description of human color perception.

Color wheels, harmony schemes, and psychological associations
are tools for exploring visual relationships.

They do not guarantee successful branding.

Modern perceptual color models offer improved ways
to evaluate lightness, chroma, and color differences,
but they do not eliminate the need for visual judgment.

**Effective brand color systems combine intentional
hue relationships, perceptual balance, sufficient contrast,
consistent application, and reliable reproduction.**
