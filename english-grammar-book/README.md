# English for Competitive Exams (BCS · Bank · Admission · SAT · GRE · GMAT)

Sample chapters: **Ch 23 Subject-Verb Agreement** and **Ch 45 Vocabulary with Synonyms & Antonyms**.

- `src/` — chapter sources in Markdown (one or more files per chapter, `chNN_*.md`) plus `cover.html`.
- `build/` — build pipeline: `build.py` (pandoc → HTML, soft hyphenation), `style.css` (A4, two justified columns), `render.js` (Chromium → PDF).
- `output/English_Sample_Ch23_Ch45.pdf` — the rendered PDF.

Build: `python3 build/build.py` (needs pandoc, `pip install pyphen`, Node Playwright with Chromium, FreeSerif font for Bangla).
