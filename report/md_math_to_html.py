# -*- coding: utf-8 -*-
"""Convert TEMPEKG_TOAN_HOC.md (Markdown + LaTeX) to a self-contained HTML page rendered by MathJax.
Supports the subset used in the report: headings, paragraphs, bullet/ordered lists, tables, bold,
italics, inline code, $...$ and $$...$$ math, horizontal rules."""
import io, re, html, sys
from pathlib import Path
SRC = Path(__file__).with_name("TEMPEKG_TOAN_HOC.md"); OUT = Path(__file__).with_name("TEMPEKG_TOAN_HOC.html")
md = io.open(SRC, encoding="utf-8").read()

MATH = []
def stash(m):
    MATH.append(m.group(0)); return "\x00%d\x00" % (len(MATH) - 1)
md = re.sub(r"\$\$.+?\$\$", stash, md, flags=re.S)
md = re.sub(r"(?<!\\)\$[^\$\n]+?\$", stash, md)
CODE = []
def cstash(m):
    CODE.append(m.group(1)); return "\x01%d\x01" % (len(CODE) - 1)
md = re.sub(r"`([^`\n]+)`", cstash, md)

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\x01(\d+)\x01", lambda m: "<code>%s</code>" % html.escape(CODE[int(m.group(1))], quote=False), s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: html.escape(MATH[int(m.group(1))], quote=False), s)
    return s

def slug(t, used):
    b = re.sub(r"[^\w]+", "-", t.lower()).strip("-")[:40] or "muc"
    s = b; i = 2
    while s in used: s = "%s-%d" % (b, i); i += 1
    used.add(s); return s

lines = md.split("\n"); out = []; toc = []; used = set(); i = 0
def flush_para(buf):
    if buf: out.append("<p>%s</p>" % inline(" ".join(x.strip() for x in buf)))
para = []
while i < len(lines):
    ln = lines[i]
    if not ln.strip():
        flush_para(para); para = []; i += 1; continue
    m = re.match(r"^(#{1,3}) (.*)", ln)
    if m:
        flush_para(para); para = []
        lvl = len(m.group(1)); txt = m.group(2)
        if lvl == 1: out.append('<h1>%s</h1>' % inline(txt))
        else:
            sid = slug(re.sub(r"\x00\d+\x00|\x01\d+\x01", "", txt), used)
            if lvl == 2: toc.append((sid, txt))
            out.append('<h%d id="%s">%s</h%d>' % (lvl, sid, inline(txt), lvl))
        i += 1; continue
    if ln.strip() == "---":
        flush_para(para); para = []; out.append("<hr/>"); i += 1; continue
    if ln.startswith("|"):
        flush_para(para); para = []
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
        head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)]
        t = ['<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>' % "".join("<th>%s</th>" % inline(c) for c in head)]
        for r in body: t.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r))
        t.append("</tbody></table></div>"); out.append("".join(t)); continue
    m = re.match(r"^(\s*)(- |\d+\. )(.*)", ln)
    if m:
        flush_para(para); para = []
        ordered = m.group(2)[0].isdigit(); items = []
        while i < len(lines):
            mm = re.match(r"^(\s*)(- |\d+\. )(.*)", lines[i])
            if mm and len(mm.group(1)) == 0:
                items.append([mm.group(3)]); i += 1
            elif mm and items:                       # nested item -> keep as sub-bullet text
                items[-1].append("\x02" + mm.group(3)); i += 1
            elif lines[i].startswith("  ") and lines[i].strip() and items:
                items[-1].append(lines[i].strip()); i += 1
            else: break
        tag = "ol" if ordered else "ul"; li = []
        for it in items:
            main = [x for x in it if not x.startswith("\x02")]; sub = [x[1:] for x in it if x.startswith("\x02")]
            s = inline(" ".join(main))
            if sub: s += "<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in sub)
            li.append("<li>%s</li>" % s)
        out.append("<%s>%s</%s>" % (tag, "".join(li), tag)); continue
    mdisp = re.fullmatch(r"\s*\x00(\d+)\x00\s*", ln)
    if mdisp and MATH[int(mdisp.group(1))].startswith("$$"):
        flush_para(para); para = []
        out.append('<div class="display">%s</div>' % inline(ln.strip())); i += 1; continue
    para.append(ln); i += 1
flush_para(para)

body = "\n".join(out)
toc_html = "".join('<li><a href="#%s">%s</a></li>' % (sid, inline(t)) for sid, t in toc)
page = io.open(Path(__file__).with_name("math_template.html"), encoding="utf-8").read()
page = page.replace("{{TOC}}", toc_html).replace("{{BODY}}", body)
io.open(OUT, "w", encoding="utf-8").write(page)
print("ok", OUT, len(page), "ky tu;", len(MATH), "cong thuc;", len(toc), "muc")
