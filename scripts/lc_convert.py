#!/usr/bin/env python3
"""Convert the HTML fragments fetched by lc_fetch.py into one Markdown file
per law.

  constitution/constitution-of-saint-lucia.md
  codes/<slug>.md      Civil Code, Criminal Code, Code of Civil Procedure ...
  acts/<letter>/<slug>.md   all other Acts of the Revised Laws (2023)
Usage: lc_convert.py
"""
import datetime
import json
import os
import re

from bs4 import BeautifulSoup
from markdownify import markdownify

RAW = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_raw", "lc"))
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TODAY = datetime.date.today().isoformat()


def yq(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def frag_md(html, top_level):
    soup = BeautifulSoup(html, "lxml")
    sec = soup.find("section")
    for sp in sec.select("span.label"):
        sp.decompose()
    for tag in sec.find_all(["ol", "ul"]):
        tag.name = "div"
    for tag in sec.find_all("li"):
        tag.name = "div"
    hs = sec.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    first = True
    for h in hs:
        txt = re.sub(r"\s+", " ", h.get_text(" ", strip=True))
        lvl = top_level if first else min(top_level + 1, 6)
        first = False
        new = soup.new_tag("p")
        new.string = "\x00H%d\x00%s" % (lvl, txt)
        h.replace_with(new)
    md = markdownify(str(sec), heading_style="ATX", bullets="-", strip=["section"])
    md = re.sub(r"\x00H(\d)\x00", lambda m: "#" * int(m.group(1)) + " ", md)
    md = md.replace(" ", " ")
    md = re.sub(r"^(\s*\(?[A-Za-z0-9]{1,6}[.)]) {2,}", r"\1 ", md, flags=re.M)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def classify(slug, title):
    t = title.lower()
    slug = slug[:100].rstrip("-")
    if slug.startswith("constitution-of-saint-lucia"):
        return "constitution", os.path.join("constitution", slug + ".md")
    if re.search(r"\bcode\b", t) and not t.endswith(" act"):
        return "code", os.path.join("codes", slug + ".md")
    return "act", os.path.join("acts", slug[0], slug + ".md")


def main():
    idx = json.load(open(os.path.join(RAW, "index.json")))
    counts, missing = {}, []
    for law in idx:
        d = os.path.join(RAW, "html", law["slug"])
        dp = os.path.join(d, "_done.json")
        if not os.path.exists(dp):
            missing.append(law["slug"])
            continue
        info = json.load(open(dp))
        parts, errors = [], 0
        for lf in info["leaves"]:
            if lf["leaf"].startswith("subsidiary-legislation"):
                break
            if lf.get("skipped"):
                continue
            fp = os.path.join(d, lf.get("file", ""))
            if not lf.get("file") or not os.path.exists(fp):
                errors += 1
                parts.append("*[%s — text not available from source]*" % lf["label"])
                continue
            leaf = lf["leaf"]
            if leaf == "act":
                lvl = 2
            elif lf["cls"] == "part" or leaf.startswith(("schedule", "part-", "preliminary", "chapter-", "division-", "book-", "title-")):
                lvl = 2
            else:
                lvl = 3
            md = frag_md(open(fp, encoding="utf-8").read(), lvl)
            if leaf == "act":
                md = re.sub(r"^## ACT\s*\n", "", md)
            parts.append(md)
        title = info["title"].strip()
        kind, rel = classify(law["slug"], title)
        m = re.search(r"as at (\d{1,2} \w+ \d{4})", info.get("description", ""))
        cons = ""
        if m:
            try:
                cons = datetime.datetime.strptime(m.group(1), "%d %B %Y").date().isoformat()
            except ValueError:
                cons = ""
        first = parts[0] if parts else ""
        mm = re.search(r"\(((?:Act|Ordinance|S\.I\.|Statutory)[^)]{0,300})\)", first)
        fm = ["---", "title: " + yq(title), "identifier: " + yq(law["slug"]),
              "type: " + kind, "jurisdiction: lc", "language: en"]
        if mm:
            fm.append("enactment: " + yq(re.sub(r"[*_]", "", mm.group(1)).strip()))
        if cons:
            fm.append("last_amended: " + cons)
        fm += ["status: in_force", "source: " + yq(info["url"]), "retrieved: " + TODAY,
               'edition: "Revised Laws of Saint Lucia (2023)"']
        if errors:
            fm.append("incomplete_pages: %d" % errors)
        fm.append("---")
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(fm) + "\n\n# " + title + "\n\n" + "\n\n".join(p for p in parts if p) + "\n")
        counts[kind] = counts.get(kind, 0) + 1
    print(counts, "not fetched:", len(missing), missing[:10])


if __name__ == "__main__":
    main()
