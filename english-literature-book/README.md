# English Literature for Competitive Exams (BCS · Bank · Admission)

A complete English literature book for the competitive examinations of Bangladesh, rendered as an A4 PDF with two justified columns per page.

- **Part A — English Literature (Chapters 01–12):** history and periods of English literature, the Old English, Middle English, Renaissance, Neo-Classical, Romantic, Victorian, Modern and Post-Modern periods, quotations, literary terms, and a special chapter of lists (titles, pen names, translations, Nobel and Booker winners and more). Each writer has a life sketch, summaries of the important works and key quotations.
- **Part B — Miscellaneous (Chapter 13).**

**Status:** Chapter 03 (The Middle English Period) is written as a sample: `output/Chapter_03_Middle_English_Period_Sample.pdf`.

## Layout of the repository

- `src/` — chapter sources in Markdown (`chNN_*.md`; a chapter may be split across several files).
- `build/` — `build.py` (pandoc → HTML, soft hyphenation, contents page with page numbers when there is more than one chapter, part dividers, PDF bookmarks), `style.css` (A4, two justified columns), `render.js` (headless Chromium → PDF).
- `output/` — the rendered PDFs.

Markdown conventions: `::: facts` for a writer's profile box, `::: quotes` for quotations (each item is the quotation in italics, then `[meaning]{.mean}` and `[— source]{.src}`; `[heading]{.qh}` titles the box), and `::: note` for side notes.

## Building

Requirements: `pandoc`, Python 3 with `pyphen` and `pypdf`, Node.js with Playwright and Chromium, and the Liberation and DejaVu fonts.

```
python3 build/build.py                                   # whole book
python3 build/build.py output/Chapter_03_Middle_English_Period_Sample.pdf --only 03
```
