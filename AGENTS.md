# AGENTS.md

Guidance for agents working on this repo (通用规范汉字表在线检索 SPA).

## What this is

A single, static, no-build web app that lets users search the **《通用规范汉字表》** (Table of
General Standard Chinese Characters, 8105 字) and view **附表一** — the 规范字 ↔ 繁体字 / 异体字
correspondence table — plus its footnotes. Live at <https://tonggui.digitalhumanities.dev>.

Design mirrors the sibling `../free-fonts` demo page (warm paper palette, CSS custom-property
theming, light/dark, noise texture).

## Files

- `index.html` — the entire app: HTML + CSS + vanilla JS (no framework, no build step).
- `data.js` — `window.GCTABLE = { rows: [...], notesCats: [...] }`, generated from the xlsx.
- `assets/通用规范汉字表.xlsx` — source spreadsheet (tracked). The data source.
- `README.md` — web-app intro, then a divider, then the upstream `cdtym` project's original README.
- The original `assets/` also contained a ~100 MB reference PDF (`通用规范汉字表.pdf`); it is **not**
  tracked and generally absent. Do not try to OCR it.

## Data model (`data.js`)

Each row: `{ s, c, cp, lv, t?, v? }`
- `s` serial (1–8105), `c` 规范字 char, `cp` `"U+XXXX"`, `lv` level 1/2/3.
- `t` = 繁体字 forms `[{ c, cp, g, n? }]` (`g` = correspondence group number, ≥1).
- `v` = 异体字 forms `[{ c, cp, n? }]`.
- `n` (optional footnote) = `{ f: "F#", cat: "繁体另做规范字" | "异体另做规范字" | "异体字" }`.
- `t` / `v` are omitted when empty.

Counts: 8105 rows; **2546** have `t` (繁体); **792** have `v` (异体); 65 rows carry footnotes.
Level split: 序号 1–3500 = 一级 (3500), 3501–6500 = 二级 (3000), 6501–8105 = 三级 (1605).
196 规范字 are astral-plane (cp > U+FFFF) — these stress font coverage.

### Regenerating `data.js` from the xlsx

Requires Python + `openpyxl`. Relevant sheets and rules:
- `字表8105` → serial, char, cp (the base 8105 list).
- `附表一序号编码` → the richest sheet. Per serial, columns come in `(code, char, cp)` triples at
  index groups `(3,4,5) (6,7,8) (9,10,11) (12,13,14) (15,16,17) (18,19,20)`; continuation rows
  (col 0 empty) add more forms to the current serial. **Code grammar:**
  - `s_0` with char `～` = the 规范字 itself is retained (no distinct traditional). Skip it.
  - `s_n` (n ≥ 1) = a **繁体字** correspondence, group `n`.
  - `s_n_m` = an **异体字** (variant `m` of group `n`).
- `附表一附注` → footnotes `F1..F52`. Each row maps a char to a category by which of columns
  4/5/6 is non-empty: `繁体另做规范字 / 异体另做规范字 / 异体字`. **The footnote body text is NOT in
  the xlsx** (it lives only in the official PDF); the app surfaces the category, not the prose.

Merge base + correspondences by serial; attach footnotes to forms by char identity.

## Search semantics

Input is a single char or a codepoint (`U+5E72`, `5e72`, hex, or decimal `24178`). A row matches if
the query hits the 规范字 **or any of its 繁体/异体 forms** (precomputed per-row cp/char sets). This
cross-reference is intentional and important:
- `乾` / `U+4E7E` → 干 (serial 23, whose 繁体 is 乾) **and** 乾 (serial 2215, 繁体另做规范字).
- `甦` → 甦 (serial 7335, a 规范字) **and** 苏 (serial 677, where 甦 is an 异体字).

Empty query → infinite-scroll full table (IntersectionObserver, batches of 80).

## Controls & state

Central `state` object; every committed change funnels through `commit()` = `applyFilters()` +
`refreshUI()` + `syncHashDebounced()`. The search input has a separate `draftQuery`; plain `input`
events must not call `commit()` or clear/rebuild the list, because that makes the page height jump
while users are still editing or composing text. Commit the search only on explicit actions such as
Enter or the clear button. The top **stat chips are buttons** wired to the same filters and stay
visually in sync with the level chips / checkboxes below. State is serialized to the URL hash.
Default display font is **Noto Serif SC** (`--han-font`, `state.font = "noto-serif"`).

## Fonts — the main gotcha

Webfonts come from `free-fonts` (published as `@free-fonts/*` on unpkg, sliced by `unicode-range`)
plus Google Noto SC. `.han` elements use `font-family: var(--han-font), var(--han-fallback)` where
the fallback chain (WenJin Mincho planes + Jigmo + serif) gives broad coverage for rare glyphs.

**The comparison grid ("各字体字形对比") is loading-order sensitive.**

The main table `.han` elements intentionally use the broad fallback chain, but the comparison grid
must **not**. WenJin/Jigmo may already be loaded by the table; if they are present in a grid cell's
fallback chain, the browser can satisfy the glyph immediately with that fallback and never repaint the
cell with the newly downloaded primary slice. This makes "downloaded" fonts look like they did not
render.

Current approach in `loadFontGrid()` / `fontGridHtml()` (keep it this way):
- Non-system grid cells use only `<primary>, serif`. Do not append `FALLBACK`, WenJin, or Jigmo there.
- Do not put a quoted font stack into a double-quoted `style="font-family:..."` attribute. Family names
  like `"LXGW WenKai"` terminate the attribute and break the DOM. Store the stack in `data-font-family`
  and assign `el.style.fontFamily = el.dataset.fontFamily` after insertion.
- `document.fonts.load()` may be used only as a fire-and-forget fetch/repaint hint. Do not gate UI
  visibility on its promise and do not reintroduce a dimmed `is-loading` state.
- Repaint individual glyph cells after their own load settles, plus timed fallback repaints. The cell
  should render via normal CSS font selection, not by canvas/image snapshots or manual glyph drawing.

Labels are `中文名 · English Name` (no coverage annotations); the redundant `异体字 · 异体字` is
collapsed to just `异体字`.

Inspector interaction details:
- The glyph switcher includes the 规范字 as the first item, followed by the row's 繁体字 and 异体字.
- Clicking the main table's 规范字 / 繁体字 / 异体字 should open the inspector focused on that exact
  clicked glyph; clicking elsewhere in the row may default to the 规范字.
- Switching glyphs inside the inspector must update the header glyph, codepoint metadata, and the font
  comparison grid together. Do not regress to rendering every row inspector with only `r.c`.

## Testing

Local server: `python3 -m http.server 8137` (served files at repo root). Validate data in Node:
`node -e 'global.window={};require("./data.js");console.log(window.GCTABLE.rows.length)'`.

Visual checks via headless Chrome screenshots:
```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --hide-scrollbars --window-size=1000,900 --virtual-time-budget=9000 \
  --screenshot=/tmp/out.png "http://localhost:8137/#q=..."
```
To exercise the inspector, copy `index.html` and inject an auto-open script before `</body>`:
`openInspector(ROWS.find(r=>r.s===782))`. Use a visually distinctive char (e.g. 你 / serial 782) —
simple glyphs like 干 barely differ between fonts. After touching `fontGridHtml()` or
`loadFontGrid()`, inspect a glyph cell in a real browser: its computed `font-family` must be the
primary family plus `serif`, not the broad `FALLBACK`, and the HTML must not contain a truncated
`style="font-family:"LXGW...` attribute.

## Conventions

- **Country-neutral wording:** write "中国国务院", not bare "国务院" (don't assume 国务院 ⇒ China). Apply
  the same principle to other jurisdiction-implying terms.
- Keep it dependency-free and buildless; it must run from any static host or `file://`.

## Repo / deploy

- GitHub `frankslin/cn-characters-standard`, branch `main`. The SPA commit was rebased on top of the
  upstream `cdtym`-derived history (unrelated histories: `git rebase --onto origin/main --root`).
- Data source: `cdtym/digital-table-of-general-standard-chinese-characters`.
- Changes are not auto-deployed — `git push` is required, and the live site reflects the deployed
  (not local) code, so verify against the right target when a user reports a bug.
