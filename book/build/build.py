#!/usr/bin/env python3
"""Build the two-column A4 PDF from the Markdown chapters in ../src.

Pipeline: Markdown (pandoc) -> HTML fragment -> soft hyphenation + marks
-> full HTML page with print CSS -> PDF via headless Chromium (render.js).

The contents page needs page numbers, so the book is rendered twice: the
first pass finds the page on which every chapter starts (from the PDF
outline), the second pass prints those numbers in the contents.

Usage: python3 build.py [output.pdf]
"""
import html
import re
import subprocess
import sys
from pathlib import Path

import pyphen
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "src"
OUT_DIR = ROOT.parent / "output"

HYPH = pyphen.Pyphen(lang="en_GB")
SHY = "­"
WORD_RE = re.compile(r"[A-Za-z]{7,}")
TAG_SPLIT = re.compile(r"(<[^>]+>)")
TITLE_RE = re.compile(r"^# (.+?) \{#ch(\d\d)\}", re.M)

# (first chapter, part label, part title, part subtitle)
PARTS = [
    (1, "Part A", "Grammar", "Chapters 01–44 · Parts of speech, sentence structure, usage, error detection and correction"),
    (45, "Part B", "Vocabulary & Usage", "Chapters 45–53 · Words, spelling, phrasal verbs, idioms, foreign phrases, one-word substitution, analogy, confusables, proverbs"),
    (54, "Part C", "English Literature", "Chapters 54–64 · Periods, writers, works, characters, quotations, literary terms and special lists"),
    (65, "Part D", "Miscellaneous", "Chapter 65 · Further facts and topics for competitive examinations"),
]


def hyphenate_text(text: str) -> str:
    return WORD_RE.sub(lambda m: HYPH.inserted(m.group(0), hyphen=SHY), text)


def postprocess(fragment: str) -> str:
    parts = TAG_SPLIT.split(fragment)
    out, skip = [], 0
    for part in parts:
        if part.startswith("<"):
            name = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            if name and name.group(1).lower() in {"h1", "h2", "h3", "h4", "code", "th"}:
                skip += -1 if part.startswith("</") else 1
            out.append(part)
        else:
            out.append(part if skip else hyphenate_text(part))
    s = "".join(out)
    s = s.replace("✘", '<span class="mk x">✘</span>')
    s = s.replace("✔", '<span class="mk ok">✔</span>')
    s = s.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    return s


def md_to_html(md_path: Path) -> str:
    res = subprocess.run(
        ["pandoc", "-f", "markdown+fenced_divs+bracketed_spans-implicit_figures", "-t", "html5",
         "--wrap=none", str(md_path)],
        check=True, capture_output=True, text=True)
    return res.stdout


def chapters():
    """Return [(number, title, [files])] sorted by chapter number."""
    groups = {}
    for p in sorted(SRC.glob("ch*.md")):
        groups.setdefault(int(p.name[2:4]), []).append(p)
    result = []
    for num in sorted(groups):
        files = groups[num]
        m = TITLE_RE.search(files[0].read_text(encoding="utf-8"))
        title = m.group(1) if m else f"Chapter {num:02d}"
        result.append((num, title, files))
    return result


def part_page(label, title, subtitle):
    return (f'<section class="part-page"><div class="part-inner">'
            f'<div class="part-label">{label}</div><h1 class="part-title">{html.escape(title)}</h1>'
            f'<p class="part-sub">{html.escape(subtitle)}</p></div></section>')


def contents(chaps, pages):
    rows = []
    starts = {p[0]: p for p in PARTS}
    for num, title, _ in chaps:
        if num in starts:
            _, label, ptitle, _ = starts[num]
            rows.append(f'<div class="toc-part">{label} · {html.escape(ptitle)}</div>')
        pg = pages.get(num, "")
        rows.append(f'<div class="toc-row"><span class="toc-no">{num:02d}</span>'
                    f'<span class="toc-title">{html.escape(title)}</span>'
                    f'<span class="toc-dots"></span><span class="toc-pg">{pg}</span></div>')
    return f'<section class="toc-page"><h1 class="toc-head">Contents</h1>{"".join(rows)}</section>'


def build_html(chaps, pages, frags):
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    css = css.replace("url(fonts/", f"url(file://{ROOT}/fonts/")
    cover = (SRC / "cover.html").read_text(encoding="utf-8")
    starts = {p[0]: p for p in PARTS}
    body = [cover, contents(chaps, pages)]
    for num, title, _ in chaps:
        if num in starts:
            _, label, ptitle, sub = starts[num]
            body.append(part_page(label, ptitle, sub))
        body.append(f'<section class="chapter-sec" id="sec{num:02d}">\n{frags[num]}\n</section>')
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>English for Competitive Exams</title>
<style>{css}</style></head>
<body>{''.join(body)}</body></html>"""


def render(page_html: str, out_pdf: Path):
    html_path = OUT_DIR / "book.html"
    html_path.write_text(page_html, encoding="utf-8")
    subprocess.run(["node", str(ROOT / "render.js"), str(html_path), str(out_pdf)], check=True)


def chapter_pages(pdf: Path):
    """Map chapter number -> 1-based page, using the PDF outline (h1 headings)."""
    reader = PdfReader(str(pdf))
    pages = {}

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
                continue
            m = re.match(r"\s*Chapter\s+(\d+)", it.title or "")
            title = it.title or ""
            for num, t, _ in CHAPS:
                if num not in pages and title.strip() == t.strip():
                    pages[num] = reader.get_destination_page_number(it) + 1
                    break
            else:
                if m and int(m.group(1)) not in pages:
                    pages[int(m.group(1))] = reader.get_destination_page_number(it) + 1
    walk(reader.outline)
    return pages, len(reader.pages)


def main():
    global CHAPS
    OUT_DIR.mkdir(exist_ok=True)
    out_pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR / "English_for_Competitive_Exams.pdf"
    CHAPS = chapters()
    frags = {num: "\n".join(postprocess(md_to_html(f)) for f in files) for num, _, files in CHAPS}
    words = sum(len(f.read_text(encoding="utf-8").split()) for _, _, fs in CHAPS for f in fs)
    print(f"{len(CHAPS)} chapters, ~{words:,} words of Markdown source")

    render(build_html(CHAPS, {}, frags), out_pdf)
    pages, total = chapter_pages(out_pdf)
    missing = [n for n, _, _ in CHAPS if n not in pages]
    if missing:
        print("warning: no page found for chapters", missing)
    render(build_html(CHAPS, pages, frags), out_pdf)
    print(f"Wrote {out_pdf} ({total} pages)")


if __name__ == "__main__":
    main()
