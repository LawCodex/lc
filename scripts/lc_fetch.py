#!/usr/bin/env python3
"""Fetch the Revised Laws of Saint Lucia (2023) from the Attorney General's
Chambers website (https://attorneygeneralchambers.com/laws-of-saint-lucia).

The site publishes each law as HTML, one page per heading/section/schedule.
For each law we read its table-of-contents page, then every leaf page linked
from it (in order), and keep only the <section id="document"> fragment in
_raw/lc/html/<slug>/NNNN-<leaf>.html. Subsidiary legislation (every
leaf from the "subsidiary-legislation" heading on) is skipped. robots.txt (WordPress default) sets no Crawl-delay; we use 4 worker
threads, each pausing 0.5 s between requests.
Usage: lc_fetch.py [slug ...]
"""
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup

SITE = "https://attorneygeneralchambers.com"
BASE = SITE + "/laws-of-saint-lucia"
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
RAW = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_raw", "lc"))
DELAY = 0.5
WORKERS = 4
tl = threading.local()


def sess():
    if not hasattr(tl, "s"):
        tl.s = requests.Session()
        tl.s.headers["User-Agent"] = UA
    return tl.s


def get(url):
    for i in range(6):
        try:
            r = sess().get(url, timeout=120)
            time.sleep(DELAY)
            if r.status_code in (200, 404, 410):
                return r
            print("  status", r.status_code, url, file=sys.stderr, flush=True)
        except requests.RequestException as e:
            print("  retry", url, e, file=sys.stderr, flush=True)
        time.sleep(5 * (i + 1))
    raise RuntimeError("failed " + url)


def build_index():
    ip = os.path.join(RAW, "index.json")
    if os.path.exists(ip):
        return json.load(open(ip))
    laws, seen, p, last = [], set(), 1, 1
    while p <= last:
        soup = BeautifulSoup(get("%s?p=%d" % (BASE, p)).text, "lxml")
        ll = soup.find("a", class_="lastLink")
        if ll and re.search(r"p=(\d+)", ll["href"]):
            last = max(last, int(re.search(r"p=(\d+)", ll["href"]).group(1)))
        got = 0
        for a in soup.find_all("a", href=re.compile(r"^/laws-of-saint-lucia/[a-z0-9-]+$")):
            slug = a["href"].rsplit("/", 1)[1]
            if slug in seen:
                continue
            seen.add(slug)
            laws.append({"slug": slug, "title": a.get_text(" ", strip=True)})
            got += 1
        print("page", p, got, flush=True)
        if not got:
            break
        p += 1
    json.dump(laws, open(ip, "w"), indent=1)
    return laws


def fetch_law(law):
    slug = law["slug"]
    d = os.path.join(RAW, "html", slug)
    done = os.path.join(d, "_done.json")
    if os.path.exists(done):
        return slug, "cached"
    os.makedirs(d, exist_ok=True)
    r = get(BASE + "/" + slug)
    if r.status_code != 200:
        return slug, "toc %d" % r.status_code
    soup = BeautifulSoup(r.text, "lxml")
    meta = soup.find("meta", attrs={"name": "description"})
    leaves = []
    for a in soup.find_all("a", href=True):
        h = a["href"].replace("http://attorneygeneralchambers.com", "").replace("https://attorneygeneralchambers.com", "")
        m = re.match(r"^/laws-of-saint-lucia/%s/([^/#?]+)$" % re.escape(slug), h)
        if not m or m.group(1) in [x["leaf"] for x in leaves]:
            continue
        cls = "part" if "part-title" in (a.get("class") or []) else "item"
        leaves.append({"leaf": m.group(1), "label": a.get_text(" ", strip=True), "cls": cls})
    in_sub = False
    for i, lf in enumerate(leaves):
        if lf["leaf"].startswith("subsidiary-legislation"):
            in_sub = True
        if in_sub:
            lf["skipped"] = True
            continue
        fp = os.path.join(d, "%04d-%s.html" % (i, lf["leaf"][:80]))
        lf["file"] = os.path.basename(fp)
        if os.path.exists(fp):
            continue
        rr = get(BASE + "/" + slug + "/" + lf["leaf"])
        m = re.search(r'<section id="document">.*?</section>', rr.text, re.S)
        if rr.status_code != 200 or not m:
            lf["error"] = rr.status_code
            continue
        open(fp, "w").write(m.group(0))
    info = {"slug": slug, "title": law["title"], "description": meta["content"] if meta else "",
            "leaves": leaves, "url": BASE + "/" + slug}
    json.dump(info, open(done, "w"), indent=1)
    return slug, "%d leaves" % len(leaves)


def main():
    laws = build_index()
    if len(sys.argv) > 1:
        laws = [l for l in laws if l["slug"] in sys.argv[1:]]
    print(len(laws), "laws", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for n, (slug, st) in enumerate(ex.map(fetch_law, laws)):
            print(n, slug, st, flush=True)


if __name__ == "__main__":
    main()
