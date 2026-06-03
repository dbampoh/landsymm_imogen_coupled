# Pandoc render setup (GMD manuscript)

Converts the working Markdown to **PDF/LaTeX** and **Word (.docx)** for submission
and supervisor review. Run pandoc **from inside `paper/`** (image paths are
file-relative), or pass `--resource-path=paper`.

## Prerequisites
- `pandoc` (>= 3.x recommended) and, for PDF, a LaTeX engine (`xelatex`/`lualatex`).
- The figure-width Lua filter: `tools/pandoc/set_figure_width.lua` (in this folder).
- Citations: `paper/references.bib` + a **Copernicus CSL** style file
  (`copernicus.csl`, fetch from the citation-style-language/styles repo) — needed
  once the in-text citations have been converted to `[@key]` form (Phase-4 task B).

## What is automated vs. manual
- **Automated:** figure sizing (Lua filter), bibliography formatting (`--citeproc`
  + CSL), section structure, tables, equations.
- **Still manual after render:** fine figure placement, occasional wide-table
  fitting, and the Copernicus `copernicus.cls` template wrapping for final
  submission (GMD provides the LaTeX template; paste the body in, or use
  `--template`). Markdown→docx is robust; Markdown→LaTeX/PDF is good but expect a
  short cleanup pass.

## Commands

### Word (.docx) — best for supervisor review / tracked changes
```bash
cd paper
pandoc manuscript_working.md \
  --lua-filter=../tools/pandoc/set_figure_width.lua \
  --citeproc --bibliography=references.bib --csl=copernicus.csl \
  --number-sections \
  -o manuscript_working.docx
```
(Add `--reference-doc=custom-reference.docx` to control docx styling.)

### PDF (via LaTeX)
```bash
cd paper
pandoc manuscript_working.md \
  --lua-filter=../tools/pandoc/set_figure_width.lua \
  --citeproc --bibliography=references.bib --csl=copernicus.csl \
  --number-sections --pdf-engine=xelatex \
  -o manuscript_working.pdf
```

### Standalone LaTeX (to paste into the Copernicus template)
```bash
cd paper
pandoc manuscript_working.md \
  --lua-filter=../tools/pandoc/set_figure_width.lua \
  --citeproc --bibliography=references.bib --csl=copernicus.csl \
  --number-sections -t latex -o manuscript_working.tex
```

The supplement renders the same way (`supplement_working.md`).

## Notes
- **Figure widths** are applied by the Lua filter, NOT inline in the Markdown
  (keeps the preview clean). Tune sizes in `set_figure_width.lua`.
- Until citations are keyed to `[@key]`, omit `--citeproc/--bibliography/--csl`;
  the current manuscript uses prose "(Author, year)" + a manual reference list,
  which renders as-is.
- Run from `paper/` so `_media/...` image paths resolve.
