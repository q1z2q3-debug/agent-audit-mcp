# -*- coding: utf-8 -*-
"""md -> 学术风 HTML 转换器（论文 PDF 构建链第一步）。

用法：
    python md2paper_html.py
输入：与本脚本同目录的 Auditing_AI_Agent_Decisions_in_a_Trinary_Cognitive_Space.md
输出：同目录 .html（随后用 Chrome headless 打印为 PDF）：

    chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=8000 \
           --no-pdf-header-footer --print-to-pdf=out.pdf paper.html
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "Auditing_AI_Agent_Decisions_in_a_Trinary_Cognitive_Space.md")
OUT = os.path.join(HERE, "Auditing_AI_Agent_Decisions_in_a_Trinary_Cognitive_Space.html")

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
* { box-sizing: border-box; }
body { font-family: Georgia, "Times New Roman", "Microsoft YaHei", serif;
       font-size: 10.5pt; line-height: 1.62; color: #1a1a1a; margin: 0; }
.titleblock { text-align: center; margin: 0 0 6mm 0; }
.titleblock h1 { font-size: 19pt; line-height: 1.35; margin: 0 0 4mm 0; font-weight: 700; }
.titleblock .author { font-size: 11.5pt; margin: 0 0 1mm 0; }
.titleblock .version { font-size: 9.5pt; color: #666; margin: 0; }
h2 { font-size: 13pt; margin: 7mm 0 2.5mm 0; padding-bottom: 1.2mm;
     border-bottom: 1px solid #d8d8d8; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 2mm 0; page-break-after: avoid; }
p { margin: 0 0 2.6mm 0; text-align: justify; }
a { color: #1a4f8a; text-decoration: none; }
code { font-family: "Cascadia Code", Consolas, "Courier New", monospace;
       font-size: 0.88em; background: #f2f4f7; padding: 0.5px 4px; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 4px;
      padding: 3mm 3.5mm; font-size: 8.6pt; line-height: 1.45; overflow-wrap: break-word;
      page-break-inside: avoid; margin: 0 0 3mm 0; }
pre code { background: none; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0 3.5mm 0;
        font-size: 8.8pt; line-height: 1.4; page-break-inside: avoid; }
th { background: #eef1f4; text-align: left; }
th, td { border: 1px solid #c9ced4; padding: 1.6mm 2.2mm; vertical-align: top; }
tr { page-break-inside: avoid; }
ul, ol { margin: 0 0 3mm 0; padding-left: 6mm; }
li { margin-bottom: 1.4mm; text-align: justify; }
blockquote { margin: 0 0 3mm 0; padding: 2mm 4mm; border-left: 3px solid #b9c4cf;
             background: #f7f9fb; font-size: 9.3pt; color: #444; page-break-inside: avoid; }
blockquote p { margin: 0; }
hr { border: none; border-top: 1px solid #ccc; margin: 5mm 0; }
.abstract-box { border: 1px solid #c9ced4; background: #f7f9fb; padding: 3.5mm 4.5mm;
                margin: 0 0 4mm 0; }
.abstract-box h2 { margin-top: 0; border-bottom: none; padding-bottom: 0; font-size: 12pt; }
.refs p { text-indent: -6mm; padding-left: 6mm; margin-bottom: 2mm; text-align: left; }
.kw { margin: 0 0 3mm 0; }
"""


def inline(text: str) -> str:
    codes = []
    def _code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes)-1}\x00"
    text = re.sub(r"`([^`]+)`", _code, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"([A-Za-z0-9]+)_\{([^}]+)\}", r"\1<sub>\2</sub>", text)
    text = re.sub(r"([A-Za-z0-9]+)\^\{([^}]+)\}", r"\1<sup>\2</sup>", text)
    text = text.replace("3^9", "3<sup>9</sup>")
    def _restore(m):
        return "<code>" + html.escape(codes[int(m.group(1))], quote=False) + "</code>"
    text = re.sub(r"\x00(\d+)\x00", _restore, text)
    return text


def convert():
    with open(MD, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")

    out = []
    i, n = 0, len(lines)
    title_done = False
    in_abstract = False
    para = []

    def flush_para():
        nonlocal para
        if not para:
            return
        text = " ".join(para).strip()
        para = []
        if not text:
            return
        if text.startswith("**Keywords:**"):
            out.append('<p class="kw">' + inline(text) + "</p>")
        else:
            out.append("<p>" + inline(text) + "</p>")

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para(); i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(code), quote=False) + "</code></pre>")
            continue

        if stripped.startswith("### "):
            flush_para()
            out.append("<h3>" + inline(stripped[4:].strip()) + "</h3>"); i += 1; continue
        if stripped.startswith("## "):
            flush_para()
            h = stripped[3:].strip()
            if h == "Abstract":
                out.append('<div class="abstract-box"><h2>' + inline(h) + "</h2>")
                in_abstract = True
            elif h == "References":
                if in_abstract:
                    out.append("</div>"); in_abstract = False
                out.append('<h2 class="refs-h">' + inline(h) + "</h2>")
            else:
                if in_abstract:
                    out.append("</div>"); in_abstract = False
                out.append("<h2>" + inline(h) + "</h2>")
            i += 1; continue
        if stripped.startswith("# "):
            flush_para()
            if not title_done:
                out.append('<div class="titleblock"><h1>' + inline(stripped[2:].strip()) + "</h1>")
                j = i + 1
                meta = []
                while j < n and len(meta) < 2:
                    s = lines[j].strip()
                    if s and s != "---":
                        meta.append(s)
                    j += 1
                for k, m in enumerate(meta):
                    cls = "author" if k == 0 else "version"
                    out.append(f'<p class="{cls}">' + inline(m) + "</p>")
                out.append("</div>")
                title_done = True
                i = j
                continue
            out.append("<h2>" + inline(stripped[2:].strip()) + "</h2>"); i += 1; continue

        if stripped == "---":
            flush_para(); out.append("<hr>"); i += 1; continue

        if stripped.startswith(">"):
            flush_para()
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote><p>" + inline(" ".join(quote)) + "</p></blockquote>")
            continue

        if stripped.startswith("|"):
            flush_para()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            body_rows = [r for r in rows if not re.match(r"^\|[\s:\-|]+\|$", r)]
            if body_rows:
                out.append("<table>")
                for k, r in enumerate(body_rows):
                    cells = [c.strip() for c in r.strip("|").split("|")]
                    tag = "th" if k == 0 else "td"
                    out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
                out.append("</table>")
            continue

        if re.match(r"^(-|\d+\.)\s", stripped):
            flush_para()
            ordered = bool(re.match(r"^\d+\.\s", stripped))
            items = []
            while i < n and re.match(r"^(-|\d+\.)\s", lines[i].strip()):
                items.append(re.sub(r"^(-|\d+\.)\s+", "", lines[i].strip())); i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(it)}</li>" for it in items) + f"</{tag}>")
            continue

        if not stripped:
            flush_para(); i += 1; continue

        para.append(stripped); i += 1

    flush_para()
    if in_abstract:
        out.append("</div>")

    doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Auditing AI Agent Decisions in a 3^9 = 19,683-State Trinary Cognitive Space</title>"
        "<style>" + CSS + "</style></head><body>" + "\n".join(out) + "</body></html>"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("written:", OUT, len(doc.encode("utf-8")), "bytes")


if __name__ == "__main__":
    convert()
