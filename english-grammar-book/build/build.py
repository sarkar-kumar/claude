#!/usr/bin/env python3
"""Build the two-column A4 PDF from the Markdown chapters in ../src.

Pipeline: Markdown (pandoc) -> HTML fragment -> soft hyphenation + marks
-> full HTML page with print CSS -> PDF via headless Chromium (render.js).

The table of contents needs page numbers, so the book is rendered twice:
the first pass finds the page on which each chapter starts (via an
invisible marker in every chapter opener), the second pass prints the
final PDF with those numbers filled in.

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

HYPH = pyphen.Pyphen(lang="en_GB", left=3, right=3)
SHY = "­"
WORD_RE = re.compile(r"[A-Za-z]{9,}")
TAG_SPLIT = re.compile(r"(<[^>]+>)")
TITLE_RE = re.compile(r"^# (.+?) \{#ch(\d\d)\}", re.M)

PARTS = {
    "01": ("Part A", "Grammar", "Chapters 01 – 44",
           "Parts of speech, sentence structure, tenses, agreement, voice, narration, "
           "transformation, error detection and punctuation — every rule with exam examples."),
    "45": ("Part B", "Vocabulary & Usage", "Chapters 45 – 53",
           "Synonyms and antonyms, spelling, phrasal verbs, idioms, foreign phrases, "
           "one-word substitution, analogy, confusable words and proverbs."),
    "54": ("Part C", "Miscellaneous", "Chapter 54",
           "Written English and other exam essentials beyond grammar and vocabulary."),
}


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
        ["pandoc", "-f", "markdown+fenced_divs+bracketed_spans", "-t", "html5",
         "--wrap=none", str(md_path)],
        check=True, capture_output=True, text=True)
    return res.stdout


def chapters():
    groups = {}
    for p in sorted(SRC.glob("ch*.md")):
        groups.setdefault(p.name[2:4], []).append(p)
    return [(k, groups[k]) for k in sorted(groups)]


def chapter_title(files) -> str:
    m = TITLE_RE.search(files[0].read_text(encoding="utf-8"))
    return m.group(1) if m else files[0].stem


def toc_html(entries, pages) -> str:
    rows = []
    for num, title in entries:
        if num in PARTS:
            part, name, _, _ = PARTS[num]
            rows.append(f'<div class="toc-part">{part} · {html.escape(name)}</div>')
        pg = pages.get(num, "")
        rows.append(
            f'<div class="toc-row"><span class="toc-no">{num}</span>'
            f'<span class="toc-title">{html.escape(title)}</span>'
            f'<span class="toc-dots"></span><span class="toc-pg">{pg}</span></div>')
    return ('<section class="contents"><h1 class="toc-h">Contents</h1>'
            f'<div class="toc-list">{"".join(rows)}</div></section>')


def part_html(num) -> str:
    part, name, span, blurb = PARTS[num]
    return (f'<section class="part-page"><div class="part-inner">'
            f'<div class="part-kicker">{part}</div><h1>{html.escape(name)}</h1>'
            f'<div class="part-span">{span}</div><p>{html.escape(blurb)}</p>'
            f'</div></section>')


def render(page_html: str, html_path: Path, pdf_path: Path):
    html_path.write_text(page_html, encoding="utf-8")
    subprocess.run(["node", str(ROOT / "render.js"), str(html_path), str(pdf_path)], check=True)


def find_chapter_pages(pdf_path: Path) -> dict:
    found = {}
    for i, page in enumerate(PdfReader(str(pdf_path)).pages, start=1):
        for num in re.findall(r"QQCH(\d\d)QQ", page.extract_text() or ""):
            found.setdefault(num, i)
    return found


def main():
    OUT_DIR.mkdir(exist_ok=True)
    out_pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR / "English_for_Competitive_Exams.pdf"
    css = (ROOT / "style.css").read_text()
    cover = (SRC / "cover.html").read_text() if (SRC / "cover.html").exists() else ""

    chs = chapters()
    entries = [(num, chapter_title(files)) for num, files in chs]
    sections = []
    for num, files in chs:
        if num in PARTS:
            sections.append(part_html(num))
        frag = "\n".join(postprocess(md_to_html(f)) for f in files)
        marker = f'<span class="pmark">QQCH{num}QQ</span>'
        frag = frag.replace('<div class="chapter">', f'<div class="chapter">{marker}', 1)
        sections.append(f'<section class="chapter-sec" id="sec{num}">\n{frag}\n</section>')

    def page(pages):
        return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>{html.escape('English for Competitive Exams')}</title>
<style>{css}</style></head>
<body>{cover}{toc_html(entries, pages)}{''.join(sections)}</body></html>"""

    html_path = OUT_DIR / "book.html"
    render(page({}), html_path, out_pdf)
    pages = find_chapter_pages(out_pdf)
    render(page(pages), html_path, out_pdf)
    missing = [n for n, _ in entries if n not in pages]
    if missing:
        print("warning: no page found for chapters", missing)
    print(f"Wrote {out_pdf} ({len(PdfReader(str(out_pdf)).pages)} pages)")


if __name__ == "__main__":
    main()
