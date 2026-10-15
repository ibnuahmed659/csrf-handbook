# VERIFICATION REPORT

Generated: 2026-10-15T06:14:16.991394

## Summary

| Metric | Value |
| --- | --- |
| Source file | `csrf_copy.docx` |
| Parts | 8 |
| Blocks extracted | 621 |
| Blocks missing from HTML | 0 |
| Tables | 4 |
| Code / request-response blocks | 53 |
| Lists | 96 |
| Headings (sections + subsections) | 94 |
| Source characters (normalised) | 53986 |
| Site characters (normalised) | 91414 |
| Unique source words absent from site | 0 |

## Per-part block counts

| Part | Title | Blocks |
| --- | --- | --- |
| `part-intro` | HORDHAC BUUGGA | 2 |
| `part-1` | QAYBTA I — FALSAFADDA CSRF | 36 |
| `part-2` | QAYBTA II — HTTP | 67 |
| `part-3` | QAYBTA III  ANATOMY OF CSRF | 94 |
| `part-4` | QAYBTA IV  DEFENSES | 67 |
| `part-5` | QAYBTA V — BILOW: LABS-KA FUDUD | 78 |
| `part-6` | QAYBTA VI — DHEXDHEXAAD BYPASSES | 103 |
| `part-7` | QAYBTA VII SAMESITE, WEBSOCKET, IYO BEYOND | 174 |

## Missing blocks

None. Every extracted block appears in the generated HTML.

## Testing checklist

| # | Check | Result |
| --- | --- | --- |
| 1 | Every original part present | PASS (8 parts) |
| 2 | Every subsection accounted for | PASS |
| 3 | Every paragraph accounted for | PASS |
| 4 | Every table preserved | PASS (4) |
| 5 | Every code block present & intact | PASS (53) |
| 6 | Every HTTP request/response preserved | PASS |
| 7 | No content replaced by summary | PASS |
| 8 | Search index covers full content | PASS |
| 13 | Internal links / assets resolve | PASS |
| 19 | Document-to-website comparison performed | PASS |
| 20 | No invented content presented as original | PASS (see notes) |

Checks that require a live browser (theme switching, responsive
layout at specific viewports, console errors, animation timing,
keyboard focus traversal) are implemented in code and CSS but were
not executed in this headless environment; they should be confirmed
with a quick manual pass.

## Limitations & notes

- The introduction lists nine planned parts (I-IX); the source
  document contains parts I-VII only. The site reproduces the
  introduction verbatim and does not fabricate the missing parts.
- Navigation labels and interface strings are supplementary UI,
  kept distinct from the book text.
- Automated checks are text/structure based; visual rendering was
  not verified in a browser in this environment.
