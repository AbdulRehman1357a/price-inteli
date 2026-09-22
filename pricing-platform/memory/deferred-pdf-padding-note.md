---
name: pdf-label-preview-padding
description: Note to match preview padding values to backend pdf_label adapter for consistent rendering.
metadata:
  type: project
---

The backend `pdf_label.py` adapter uses the following padding/spacer values for the shelf label layout:
- `pad = 2 * mm` (outer border padding)
- `gap = 1.5 * mm` (gap between columns)
- `banner_h = 4.5 * mm` (banner height)
- `content_top = h - pad - 3 * mm` (extra 3 mm top padding for bottom banner to prevent name clipping)

The `frontend/src/features/outputs/LabelPreview.jsx` live preview uses approximate SVG equivalents:
- `pad = 4` (approx 2 mm scaled)
- `bannerH = 14` (approx 4.5 mm scaled)
- No explicit `gap` variable in the SVG layout — spacing is handled by fixed x/y coordinates.

When making future changes to `pdf_label.py`, the preview should be updated to match the same relative proportions so that users see a consistent layout. Currently, there is a clipping issue noted by the user that will be addressed in a future session.

**Why:** The preview is a mockup for instant feedback; the actual PDF is generated server-side by `pdf_label.py`. Matching values ensures the preview reflects real output.
**How to apply:** If padding (`pad`, `gap`, `banner_h`, or `content_top`) is modified in `pdf_label.py`, adjust the SVG constants (`pad`, `bannerH`, `unitBoxW`, or position offsets) in `LabelPreview.jsx` accordingly.
