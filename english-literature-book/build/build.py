#!/usr/bin/env python3
"""Build the two-column A4 PDF from the Markdown chapters in ../src.

Pipeline: Markdown (pandoc) -> HTML fragment -> soft hyphenation
-> full HTML page with print CSS -> PDF via headless Chromium (render.js).

When the book has more than one chapter, a contents page is added. It needs
page numbers, so the book is then rendered twice: the first pass finds the
page on which each chapter starts (via an invisible marker in every chapter
opener), the second pass prints the final PDF with those numbers filled in.

Usage: python3 build.py [output.pdf] [--only NN[,NN...]]
"""
import argparse
import html
import re
import subprocess
from pathlib import Path

import pyphen
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "src"
OUT_DIR = ROOT.parent / "output"
TITLE = "English Literature for Competitive Exams"

HYPH = pyphen.Pyphen(lang="en_GB", left=3, right=3)
SHY = "­"
WORD_RE = re.compile(r"[A-Za-z]{9,}")
TAG_SPLIT = re.compile(r"(<[^>]+>)")
TITLE_RE = re.compile(r"^# (.+?) \{#ch(\d\d)\}", re.M)
SECTION_RE = re.compile(r"^## (\d+\.\d+) (.+)$", re.M)

PARTS = {
    "01": ("Part A", "English Literature", "Chapters 01 – 12",
           "The periods of English literature from the Old English age to the post-modern "
           "world: writers, works, summaries and quotations, literary terms and special lists."),
    "13": ("Part B", "Miscellaneous", "Chapter 13",
           "Further facts of English literature that are often asked in competitive examinations."),
}


def hyphenate_text(text: str) -> str:
    return WORD_RE.sub(lambda m: HYPH.inserted(m.group(0), hyphen=SHY), text)


def postprocess(fragment: str) -> str:
    parts = TAG_SPLIT.split(fragment)
    out, skip = [], 0
    for part in parts:
        if part.startswith("<"):
            name = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            if name and name.group(1).lower() in {"h1", "h2", "h3", "h4", "th"}:
                skip += -1 if part.startswith("</") else 1
            out.append(part)
        else:
            out.append(part if skip else hyphenate_text(part))
    s = "".join(out)
    return s.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")


def md_to_html(md_path: Path) -> str:
    res = subprocess.run(
        ["pandoc", "-f", "markdown+fenced_divs+bracketed_spans", "-t", "html5",
         "--wrap=none", str(md_path)],
        check=True, capture_output=True, text=True)
    return res.stdout


def chapters(only=None):
    groups = {}
    for p in sorted(SRC.glob("ch*.md")):
        groups.setdefault(p.name[2:4], []).append(p)
    return [(k, groups[k]) for k in sorted(groups) if not only or k in only]


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


def sections(files):
    out = []
    for f in files:
        out += SECTION_RE.findall(f.read_text(encoding="utf-8"))
    return out


def add_outline(pdf_path: Path, chs, entries, pages, toc_page):
    """Add Part / Chapter / Section bookmarks to the finished PDF."""
    reader = PdfReader(str(pdf_path))
    texts = [re.sub(r"\s+", " ", (pg.extract_text() or "").replace(SHY, "")) for pg in reader.pages]
    writer = PdfWriter(clone_from=reader)
    if toc_page:
        writer.add_outline_item("Contents", toc_page - 1)
    starts = [pages[n] for n, _ in entries if n in pages] + [len(texts) + 1]
    part_item = None
    for i, ((num, files), (_, title)) in enumerate(zip(chs, entries)):
        if num not in pages:
            continue
        first = pages[num] - 1
        if num in PARTS:
            part, name, _, _ = PARTS[num]
            part_item = writer.add_outline_item(f"{part} · {name}", first - 1)
        ch_item = writer.add_outline_item(f"{num} {title}", first, parent=part_item)
        last = starts[i + 1] - 1
        cursor = first
        for secno, sectitle in sections(files):
            clean = re.sub(r"[*_`]", "", sectitle)
            probe = f"{secno} {clean}"[:28]
            for pg in range(cursor, last):
                if probe in texts[pg]:
                    writer.add_outline_item(f"{secno} {clean}", pg, parent=ch_item)
                    cursor = pg
                    break
    writer.page_mode = "/UseOutlines"
    with open(pdf_path, "wb") as fh:
        writer.write(fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", nargs="?", default=str(OUT_DIR / "English_Literature_for_Competitive_Exams.pdf"))
    ap.add_argument("--only", help="comma-separated chapter numbers to build, e.g. 03")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    out_pdf = Path(args.output)
    css = (ROOT / "style.css").read_text()
    cover = (SRC / "cover.html").read_text() if (SRC / "cover.html").exists() and not args.only else ""

    chs = chapters(set(args.only.split(",")) if args.only else None)
    entries = [(num, chapter_title(files)) for num, files in chs]
    with_toc = len(chs) > 1
    body = []
    for num, files in chs:
        if num in PARTS and with_toc:
            body.append(part_html(num))
        frag = "\n".join(postprocess(md_to_html(f)) for f in files)
        marker = f'<span class="pmark">QQCH{num}QQ</span>'
        frag = frag.replace('<div class="chapter">', f'<div class="chapter">{marker}', 1)
        body.append(f'<section class="chapter-sec" id="sec{num}">\n{frag}\n</section>')

    def page(pages):
        toc = toc_html(entries, pages) if with_toc else ""
        return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>{html.escape(TITLE)}</title>
<style>{css}</style></head>
<body>{cover}{toc}{''.join(body)}</body></html>"""

    html_path = OUT_DIR / "book.html"
    render(page({}), html_path, out_pdf)
    pages = find_chapter_pages(out_pdf)
    if with_toc:
        render(page(pages), html_path, out_pdf)
    add_outline(out_pdf, chs, entries, pages, (2 if cover else 1) if with_toc else None)
    missing = [n for n, _ in entries if n not in pages]
    if missing:
        print("warning: no page found for chapters", missing)
    print(f"Wrote {out_pdf} ({len(PdfReader(str(out_pdf)).pages)} pages)")


if __name__ == "__main__":
    main()
