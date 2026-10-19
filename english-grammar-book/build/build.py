#!/usr/bin/env python3
"""Build the two-column A4 PDF from the Markdown chapters in ../src.

Pipeline: Markdown (pandoc) -> HTML fragment -> soft hyphenation + marks
-> full HTML page with print CSS -> PDF via headless Chromium (render.js).

Usage: python3 build.py [output.pdf]
"""
import html
import re
import subprocess
import sys
from pathlib import Path

import pyphen

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "src"
OUT_DIR = ROOT.parent / "output"

HYPH = pyphen.Pyphen(lang="en_GB")
SHY = "­"
WORD_RE = re.compile(r"[A-Za-z]{7,}")
# Text between tags, skipping anything inside <h1..h6>, <code>, <th>.
TAG_SPLIT = re.compile(r"(<[^>]+>)")


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
    # Wrap tables so they can be styled/scrolled consistently.
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
        key = p.name[:4]  # e.g. ch23
        groups.setdefault(key, []).append(p)
    return [groups[k] for k in sorted(groups)]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    out_pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR / "English_Sample_Ch23_Ch45.pdf"
    css = (ROOT / "style.css").read_text()
    cover = (SRC / "cover.html").read_text() if (SRC / "cover.html").exists() else ""

    body = [cover]
    for files in chapters():
        frag = "\n".join(postprocess(md_to_html(f)) for f in files)
        body.append(f'<section class="chapter-sec">\n{frag}\n</section>')

    page = f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>{html.escape('English for Competitive Exams — Sample')}</title>
<style>{css}</style></head>
<body>{''.join(body)}</body></html>"""
    html_path = OUT_DIR / "book.html"
    html_path.write_text(page, encoding="utf-8")
    subprocess.run(["node", str(ROOT / "render.js"), str(html_path), str(out_pdf)], check=True)
    print(f"Wrote {out_pdf}")


if __name__ == "__main__":
    main()
