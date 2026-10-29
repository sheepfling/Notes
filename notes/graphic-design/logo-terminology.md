# Logo & Visual Identity Terminology

> Type: reference
> Status: needs-review
> Updated: 2026-10-29
> Tags: graphic-design, logo

### A Practical Guide to Marks, Wordmarks, Lockups, and Brand Assets

Logo terminology is frequently used inconsistently, even among designers.
This guide establishes a practical vocabulary for creating, discussing,
organizing, and maintaining visual identities.

## 1. Core Terminology

| Term                 | Definition                                                                                       | Examples                      |
| -------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------- |
| **Logo**             | General term for a brand's identifying graphic, whether text, symbol, or both.                   | Nike, Apple, Google           |
| **Logomark**         | A standalone graphical symbol representing a brand, typically without text.                      | Apple silhouette, Nike swoosh |
| **Wordmark**         | A brand name rendered in distinctive typography.                                                 | Google, Coca-Cola, FedEx      |
| **Logotype**         | A typographic logo; generally synonymous with *wordmark*.                                        | Disney, Canon                 |
| **Lettermark**       | A logo formed from initials or abbreviated letters.                                              | IBM, NASA, HBO                |
| **Monogram**         | Two or more letters combined or interwoven into a unified symbol.                                | Chanel CC, Louis Vuitton LV   |
| **Combination Mark** | A logo incorporating both a graphical symbol and typography.                                     | Adidas, Burger King           |
| **Emblem**           | A logo whose text and graphical elements form an integrated badge, crest, or seal.               | Harley-Davidson, Starbucks    |
| **Brandmark**        | Often synonymous with *logomark*; sometimes used more broadly for a brand's identifying graphic. | Nike swoosh                   |
| **Lockup**           | A prescribed arrangement of identity elements, including positioning, proportions, and spacing.  | Symbol left of wordmark       |

> **Key distinction:** A logo identifies the brand. A lockup specifies
> how its constituent elements appear together.

## 2. Types of Logomarks

Logomarks can be classified by their visual construction.

| Type               | Description                                           | Example      |
| ------------------ | ----------------------------------------------------- | ------------ |
| **Pictorial Mark** | Depicts a recognizable object or figure.              | Apple        |
| **Abstract Mark**  | Uses nonrepresentational geometry or shapes.          | Nike, Pepsi  |
| **Mascot Mark**    | Uses an illustrated character as the identity.        | Michelin Man |
| **Monogram**       | Combines letters into a distinctive graphical symbol. | Chanel CC    |

These categories are descriptive rather than mutually exclusive.
A monogram, for example, can also function as an abstract symbol.

## 3. Commonly Confused Terms

### Logo vs. Logomark

**Logo** is the umbrella term.

**Logomark** refers specifically to the graphical symbol.

The Nike swoosh is both a logo and a logomark.

### Wordmark vs. Logotype

These terms are effectively interchangeable in contemporary branding.

- **Wordmark** emphasizes the brand name rendered as a visual identity.
- **Logotype** emphasizes its typographic construction.

For consistency, prefer **wordmark** in asset documentation.

### Lettermark vs. Monogram

Both use letters rather than a complete brand name.

- **Lettermark:** Letters remain individually recognizable (IBM).
- **Monogram:** Letters are combined, overlapped, or interwoven (Chanel CC).

A monogram can be considered a specialized lettermark.

### Combination Mark vs. Lockup

These describe different properties.

- **Combination mark:** What elements constitute the logo.
- **Lockup:** How those elements are arranged.

A single combination mark may have multiple approved lockups.

For example:

- Horizontal: symbol beside wordmark.
- Vertical: symbol above wordmark.
- Stacked: typography arranged across multiple lines.
- Endorsed: product identity accompanied by a parent-brand identity.

## 4. Logo Variants & Applications

A complete identity usually requires more than one configuration.

| Term                   | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| **Primary Logo**       | Preferred representation of the identity.                  |
| **Secondary Logo**     | Approved alternative configuration.                        |
| **Responsive Logo**    | Simplified versions optimized for different display sizes. |
| **Submark**            | Simplified or subsidiary brand identifier.                 |
| **App Icon**           | Application-specific graphical identity.                   |
| **Favicon**            | Small icon identifying a website or browser tab.           |
| **Monochrome Variant** | Single-color reproduction.                                 |
| **Reversed Variant**   | Version intended for dark or contrasting backgrounds.      |
| **Dynamic Logo**       | Identity designed to vary within defined visual rules.     |

### Important: App Icon vs. Logomark

An app icon is not necessarily a logomark placed inside a rounded square.

Small-format applications may require:

- Simplified geometry.
- Increased stroke weights.
- Reduced internal detail.
- Adjusted proportions and spacing.
- Modified contrast.

The objective is visual recognition at the intended display size,
not necessarily pixel-perfect reproduction of the original symbol.

## 5. Supporting Identity Terminology

| Term                   | Definition                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------- |
| **Visual Identity**    | The complete visual language of a brand, including logos, colors, typography, and graphics.         |
| **Brand Identity**     | The broader system expressing a brand's identity, including visual and potentially verbal elements. |
| **Logo System**        | The collection of approved logo elements, variants, and configurations.                             |
| **Brand Architecture** | The organizational relationship between parent brands, subbrands, and products.                     |
| **Signature**          | Sometimes used to describe a complete arrangement of symbol and typography.                         |
| **Clear Space**        | Minimum unobstructed area surrounding a logo.                                                       |
| **Exclusion Zone**     | Another term for required clear space.                                                              |
| **Minimum Size**       | Smallest approved reproduction size that preserves legibility.                                      |
| **Safe Area**          | Region within an icon or layout where important content should remain.                              |
| **Brand Guidelines**   | Rules governing the consistent use of identity elements.                                            |

## 6. Recommended Asset Organization

A practical file structure for maintaining a logo system:

```text
brand/
├── source/
│   └── editable-master-files/
│
├── logo/
│   ├── symbol.svg
│   ├── wordmark.svg
│   ├── lettermark.svg
│   ├── lockup-horizontal.svg
│   └── lockup-vertical.svg
│
├── variants/
│   ├── monochrome/
│   ├── reversed/
│   └── simplified/
│
├── icons/
│   ├── app/
│   └── favicon/
│
└── guidelines/
    ├── colors.md
    ├── typography.md
    └── usage.md
```

Include only assets applicable to the identity.
A brand does not necessarily need a lettermark, emblem, or multiple lockups.

Preserve editable vector masters separately from exported deliverables.

## 7. Recommended Terminology Hierarchy

```text
VISUAL IDENTITY
│
├── Logo System
│   │
│   ├── Logomark / Symbol
│   │   ├── Pictorial
│   │   ├── Abstract
│   │   ├── Mascot
│   │   └── Monogram
│   │
│   ├── Typographic Marks
│   │   ├── Wordmark / Logotype
│   │   └── Lettermark
│   │
│   └── Combination Marks
│       ├── Horizontal Lockup
│       ├── Vertical Lockup
│       └── Alternate Lockups
│
├── Application Assets
│   ├── App Icons
│   ├── Favicons
│   └── Responsive Variants
│
└── Supporting Identity
    ├── Color Palette
    ├── Typography
    ├── Graphic Elements
    └── Usage Guidelines
```

This hierarchy is organizational, not a strict taxonomy.
For example, a lettermark may also serve as a logomark, and an emblem
may incorporate both graphical and typographic elements.

## 8. Quick Reference

| When referring to...                      | Prefer               |
| ----------------------------------------- | -------------------- |
| The overall identifying graphic           | **Logo**             |
| The graphical symbol alone                | **Logomark**         |
| The complete stylized brand name          | **Wordmark**         |
| Initials used as the identity             | **Lettermark**       |
| Interwoven or combined initials           | **Monogram**         |
| Symbol and typography together            | **Combination Mark** |
| Their specific arrangement                | **Lockup**           |
| A compact application-specific asset      | **App Icon**         |
| The collection of approved configurations | **Logo System**      |
| The complete visual language              | **Visual Identity**  |

---

### A Note on Terminology

Graphic design terminology is not universally standardized.

Terms such as *brandmark*, *logotype*, *signature*, and *submark*
can have different meanings across agencies and design systems.

These definitions represent practical conventions rather than rigid
industry standards.

**Consistency within a design system is more important than
enforcing a universal vocabulary.**