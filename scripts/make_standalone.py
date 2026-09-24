"""Wrap the artifact HTML into a file that opens from disk with no network.

The published page relies on the artifact host for two things: the <!doctype>/<head>
skeleton it is wrapped in at publish time, and a Google Fonts stylesheet. Opened straight
from the filesystem it would have neither, so this adds the skeleton and swaps the webfont
link for a system font stack. Everything else in the page is already inline.

Usage:
    python make_standalone.py
"""

from __future__ import annotations

import io
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The report lives in report/; this script lives in scripts/ beside it.
REPORT = HERE.parent / "report" if (HERE.parent / "report").is_dir() else HERE
SRC = REPORT / "tempekg_report.html"
DST = REPORT / "tempekg_report_offline.html"

# Substituted for the Google Fonts link. Instrument Sans and JetBrains Mono are not
# installed on most machines, so name them first and let the stack fall through.
FALLBACK = """<style>
  /* offline build: no webfont fetch, so these stacks stand in for the published faces */
  body, button { font-family: "Instrument Sans", "Segoe UI", system-ui,
                 -apple-system, "Helvetica Neue", Arial, sans-serif; }
  code, pre, .mono, .num, td.num, th.num,
  .card .big, .meta, .tag, .pill { font-family: "JetBrains Mono", "Cascadia Mono",
                 Consolas, "SF Mono", ui-monospace, monospace; }
</style>"""


def main() -> int:
    html = SRC.read_text(encoding="utf-8")

    link = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis[^>]*>', html)
    if link:
        html = html.replace(link.group(0), FALLBACK, 1)
        print("replaced the Google Fonts link with a local stack")
    else:
        print("no font link found -- nothing to replace")

    title = re.search(r"<title>(.*?)</title>", html)
    page_title = title.group(1) if title else "TempEKG"

    out = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{page_title}</title>
<style>
  :root {{ color-scheme: light dark;
           padding-top: env(safe-area-inset-top, 0px);
           padding-bottom: env(safe-area-inset-bottom, 0px); }}
  body {{ margin: 0; font: 14px system-ui, sans-serif; background: #f6f6f4; }}
  img {{ max-width: 100%; }}
  [hidden] {{ display: none !important; }}
</style>
</head>
<body>
{html}
</body>
</html>
"""
    DST.write_text(out, encoding="utf-8")
    kb = DST.stat().st_size / 1024
    print(f"wrote {DST.name}  ({kb:.0f} KB, opens with a double-click, no network needed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
