# CSRF Handbook — Website

A premium, responsive, interactive website built from the Somali-language
Word document **`csrf handbook.docx`**. The site preserves **100%** of the
source text — every heading, paragraph, list, table and code/HTTP example —
and never summarises, rewrites or invents content.

## Highlights

- **Faithful content.** Every block of the source document is rendered
  verbatim. See [`VERIFICATION.md`](VERIFICATION.md) for the automated
  completeness report (0 missing blocks, 0 missing words).
- **Premium reading experience.** Sticky header, in-page table of contents,
  chapter sidebar, reading-progress bar, breadcrumbs, chapter pager and
  back-to-top.
- **Dark & light themes** with OS preference detection and persistence.
- **Full-text search** across headings, paragraphs, lists, tables and code,
  with keyboard support (`/` or `Ctrl/⌘ + K`) and per-result excerpts.
- **Responsive** from large desktop down to mobile (off-canvas sidebar and
  on-this-page drawer on small screens).
- **Syntax highlighting** with Prism (markup, JavaScript, PHP, HTTP, Bash,
  JSON, CSS) using a theme-adaptive custom token theme.
- **Accessible**: semantic landmarks, `aria` attributes, skip link,
  focus-visible styles, `prefers-reduced-motion` support, print styles.
- **Offline-friendly**: no CDN or network calls. Everything is vendored and
  the site works when opened directly from the filesystem (`file://`).

## Project structure

```
csrf-handbook/
├─ index.html                     Landing page (hero + intro + chapter cards)
├─ chapters/
│  ├─ part-intro.html             HORDHAC BUUGGA
│  └─ part-1.html … part-7.html   QAYBTA I … QAYBTA VII
├─ assets/
│  ├─ css/    themes.css, style.css, responsive.css
│  ├─ js/     theme.js, navigation.js, reading-progress.js, search.js, app.js
│  ├─ img/    favicon.svg
│  └─ vendor/ bootstrap/, prism/
├─ data/
│  ├─ content.json                Structured source model (8 parts, 621 blocks)
│  ├─ search-index.json           Search index (machine readable)
│  ├─ search-index.js             Same index as window.SEARCH_INDEX (file:// safe)
│  └─ content-manifest.json       Traceability manifest (source → destination)
├─ tools/
│  ├─ extract_docx.py             .docx → data/content.json
│  ├─ build.py                    data/content.json → HTML pages + indexes
│  └─ verify.py                   Completeness checker → VERIFICATION.md
├─ VERIFICATION.md                Generated verification report
└─ README.md
```

## Viewing the site

Open `index.html` in any modern browser. No build step or web server is
required — the pages reference only local, relative assets.

> Tip: for the nicest experience (and correct search-index script loading),
> you may also serve the folder, e.g. `python -m http.server`, but this is
> optional.

## Regenerating the site

Requires Python 3 (standard library only).

```powershell
# 1. Extract the source document into the structured content model
python tools/extract_docx.py "path\to\csrf handbook.docx" data/content.json

# 2. Build the HTML pages, search index and manifest
python tools/build.py

# 3. (Optional) Re-run the completeness verification
python tools/verify.py "path\to\csrf handbook.docx"
```

`extract_docx.py` reads the WordprocessingML directly (paragraph styles,
run fonts, numbering and tables) so that code blocks, lists and tables are
detected faithfully. `build.py` only wraps the preserved text in semantic
HTML and adds presentation/interaction layers — it never alters wording.

## Editing or adding chapters without losing content

The website is generated from `data/content.json`, which is the single
structured model of the book. There are two ways to make changes:

**A. Change wording in the model (safe, no content loss).**

1. Edit the relevant `html`/`text`/`lines`/`items`/`rows` fields in
   `data/content.json`. Every block already has a stable `id`
   (e.g. `part-3-b42`) used by anchors, the search index and the manifest.
2. Run `python tools/build.py` to regenerate the pages, then
   `python tools/verify.py "<original.docx>"` to re-check completeness.

**B. Add a new chapter.**

1. Add the new content to the source `.docx` (or append new blocks to
   `data/content.json`), keeping a single leading `part` block whose text
   starts with `QAYBTA …` or `HORDHAC`.
2. Re-run `tools/extract_docx.py` (if you edited the `.docx`) and then
   `tools/build.py`. New pages, sidebar entries, pagers, the search index
   and the manifest are all regenerated automatically.

Because pages are generated, **never edit the files under `chapters/` or
`index.html` by hand** — your changes will be overwritten on the next
build. Always edit the model (or the source document) and rebuild.

To customise styling, edit `assets/css/themes.css` (design tokens),
`assets/css/style.css` (components) or `assets/css/responsive.css`
(breakpoints); these are not touched by the build.

## Content fidelity notes

- The introduction lists **nine** planned parts (I–IX). The source document
  itself only contains parts **I–VII**; the site reproduces the introduction
  exactly as written and does not invent the missing parts.
- The site's navigation labels and any interface strings (buttons, titles,
  hints) are **additive UI**, clearly separated from the book's text. The
  book's own wording is never replaced.

## Browser support

Modern evergreen browsers (Chrome, Edge, Firefox, Safari). JavaScript
enhances the experience (search, drawers, copy buttons, theme toggle); the
full text remains readable with JavaScript disabled.

## Licensing / attribution

The book content belongs to its original author. This repository only
provides a web presentation of that content.
