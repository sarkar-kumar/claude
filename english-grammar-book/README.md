# English for Competitive Exams (BCS · Bank · Admission · SAT · GRE · GMAT)

A complete English grammar, vocabulary and usage book in 54 chapters, written for the competitive examinations of Bangladesh, with SAT, GRE and GMAT concepts blended in. It is rendered as an A4 PDF with two justified columns per page.

- **Part A — Grammar (Chapters 01–44):** parts of speech, nouns, determiners, articles, pronouns, adjectives, verbs, modals, non-finites, adverbs, inversion, prepositions, conjunctions, tense, right form of verbs, agreement, comparison, conditionals, voice, narration, tag questions, modifiers, phrases, clauses, sentence types, transformation, error detection, missing words, embedded questions, redundancy, parallelism, affixes, word families, correction and punctuation.
- **Part B — Vocabulary & Usage (Chapters 45–53):** synonyms and antonyms (with Bangla meanings), spelling, phrasal verbs, idioms, foreign phrases, one-word substitution, analogy, confusable words and proverbs.
- **Part C — Miscellaneous (Chapter 54):** translation, reading comprehension, writing skills (paragraph, essay, letters, email, report, précis, amplification, dialogue, CV), sentence completion, linkers, British vs American English, abbreviations, test formats and exam strategy.

## Layout of the repository

- `src/` — chapter sources in Markdown (`chNN_*.md`; a chapter may be split across several files) and `cover.html`.
- `build/` — `build.py` (pandoc → HTML, soft hyphenation, contents page with page numbers, part dividers), `style.css` (A4, two justified columns), `render.js` (headless Chromium → PDF with bookmarks).
- `output/English_for_Competitive_Exams.pdf` — the rendered book.

## Building

Requirements: `pandoc`, Python 3 with `pyphen` and `pypdf`, Node.js with Playwright and Chromium, and the Liberation, DejaVu and FreeSerif fonts (FreeSerif renders the Bangla text).

```
python3 build/build.py
```

The build renders twice: the first pass finds the page on which each chapter starts, and the second pass fills those numbers into the contents page.
