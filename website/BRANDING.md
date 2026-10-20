# Omarchy psX website lettering

The website pairs the canonical **OMARCHY** wordmark with **PSX** rendered in
**Delta Corps Priest 1**, the FIGlet font used by Omarchy's own ASCII renderer.
The font credits **CoSMiC cHiLD**. Both words use one solid theme color and keep
their original proportions; the SVG outlines remain sharp without a web font.

## Assets

- `assets/omarchy-psx.svg` is the combined mark used in the header and masthead.
- `assets/psx.svg` is the standalone PSX lettering.
- `assets/psx.txt` preserves the upstream renderer's PSX output.
- `assets/omarchy-psx-square-tokyo-night.svg` is the square avatar: OMARCHY
  centered above PSX on an opaque Tokyo Night background.
- `assets/favicon.svg` uses the canonical Omarchy O outline on a dark tile.
- `assets/LICENSE-omarchy.txt` preserves the upstream MIT notice unchanged.

The build copies these files to `dist/assets/`, including the license notice.
The combined mark has an accessible name of “Omarchy psX”; the all-capital
artwork follows the original font's glyph construction.

The square avatar uses a 2048-by-2048 canvas and the same outlined glyphs on
both lines. Its Tokyo Night colors come from the pinned Omarchy theme:
background `#1a1b26`, blue `#7aa2f7`, and bright magenta `#bb9af7`. Each line is
centered horizontally, the complete text block is centered vertically, and
the lettering fits within a circular avatar crop. Render the SVG with a
standard SVG renderer to export a square PNG; the SVG embeds the upstream MIT
notice in its metadata.

## Pinned sources and adaptations

Omarchy's canonical `logo.svg` and `LICENSE` are taken from commit
`f0020448ca87329199de7cb12f2015ebc4a3e5e7`. All seven OMARCHY path geometries
are preserved, with theme-aware fill and accessible SVG metadata.

https://github.com/omacom/omarchy/blob/f0020448ca87329199de7cb12f2015ebc4a3e5e7/logo.svg

PSX was rendered using `bin/omarchy-ascii` at commit
`4baae6bf2afb2c07b617100371c07d8b6dea71a5`, whose embedded font is Delta
Corps Priest 1. Full and half block characters are converted into SVG runs
using a 15-by-30-unit terminal cell, retaining horizontal and vertical halves.
The PSX artwork is placed at `(1290, 15)` beside the canonical wordmark,
aligning the main letter bodies without stretching either word.

https://github.com/omacom/omarchy/blob/4baae6bf2afb2c07b617100371c07d8b6dea71a5/bin/omarchy-ascii

Source and destination SHA-256 digests, per-import source identities and the
adaptations are recorded in `../provenance/integration-import.json`. These
artwork inputs do not change the distribution's pinned Omarchy source version.

The combined mark identifies this community port. The manual's legal notice
describes the project's independence from upstream Omarchy and Sony.
