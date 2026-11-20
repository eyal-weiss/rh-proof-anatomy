#!/usr/bin/env python3
"""Make the publishable Artifact copy of rh_anatomy.html.

The Artifact platform wraps the file in its own <!doctype>/<html>/<head>/<body> skeleton (with charset and viewport
metas), so this strips those from the local page, gives it a short name as <title>, and adds the viewport-fit meta
that goes with the page's max()-based side gutter.  Usage: python3 make_artifact.py OUT.html
"""
import re, sys

src = open("rh_anatomy.html", encoding="utf-8").read()
out = src
for pat in [r"<!DOCTYPE html>\s*", r"<html[^>]*>\s*", r"</html>\s*", r"<head>\s*", r"</head>\s*", r"<body>\s*", r"</body>\s*",
            r'<meta charset="utf-8">\s*', r'<meta name="viewport"[^>]*>\s*']:
    out = re.sub(pat, "", out, count=1, flags=re.I)
out = re.sub(r"<title>.*?</title>", '<title>RH Proof Anatomy</title>\n<meta name="claude:viewport-fit-sides" content="cover">', out, count=1)
assert "padding-left:max(" in out and "<script>" in out and "<body" not in out.lower()
open(sys.argv[1], "w", encoding="utf-8").write(out)
print("wrote", sys.argv[1], len(out), "bytes")
