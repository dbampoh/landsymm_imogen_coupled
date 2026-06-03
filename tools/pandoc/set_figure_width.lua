--[[
  set_figure_width.lua  --  pandoc Lua filter

  Purpose
  -------
  The working Markdown (paper/manuscript_working.md, paper/supplement_working.md)
  deliberately carries NO inline {width=...} image attributes, because generic
  CommonMark/GFM previewers render that attribute syntax as literal text next to
  the figure. This filter re-applies a sensible rendered width to every figure
  AT RENDER TIME (LaTeX/PDF and docx), so the source stays clean while the output
  is correctly sized.

  Behaviour
  ---------
  - Any image lacking an explicit width is given DEFAULT_WIDTH.
  - The OVERRIDES table preserves the originally intended per-figure widths
    (recorded in paper/PAPER_REVAMP_PLAN_AND_LOG.md): Taylor diagram 5.0in,
    end-of-century bias maps 6.0in; everything else defaults to 6.5in
    (~full Copernicus single-column text width).
  - Match is by substring of the image path, so it is robust to the _media/ prefix.

  Usage
  -----
    pandoc paper/manuscript_working.md \
      --lua-filter=tools/pandoc/set_figure_width.lua  ... (see tools/pandoc/README.md)

  Tune DEFAULT_WIDTH / OVERRIDES here rather than editing the Markdown.
]]

local DEFAULT_WIDTH = "6.5in"

local OVERRIDES = {
  ["fig5_taylor_tas"]                  = "5.0in",
  ["fig6_biasmap_ssp126_eoc"]          = "6.0in",
  ["fig6_climate_biasmaps_ssp585_eoc"] = "6.0in",
  ["image173"]                         = "6.5in",  -- framework schematic (Fig. 1)
}

function Image(img)
  if img.attributes.width == nil or img.attributes.width == "" then
    local w = DEFAULT_WIDTH
    for key, width in pairs(OVERRIDES) do
      if img.src:find(key, 1, true) then
        w = width
        break
      end
    end
    img.attributes.width = w
  end
  return img
end
