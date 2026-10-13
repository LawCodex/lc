# Saint Lucia — LawCodex

Legislation of Saint Lucia as plain Markdown. Part of [LawCodex](https://github.com/LawCodex).

**Status: full.** The repo has every law in the official **Revised Laws of Saint Lucia (2023)**,
showing the law as at 31 December 2023, as published in HTML by the Attorney General's
Chambers.

## What is covered

| Directory | Contents | Files |
|---|---|---|
| `constitution/` | Constitution of Saint Lucia (S.I. 1978 No. 1901 (U.K.), Schedule 1, as amended to 2023) | 1 |
| `codes/` | Civil Code of Saint Lucia, Commercial Code, Code of Civil Procedure, Criminal Code | 4 |
| `acts/<first letter>/` | All other Acts of the Revised Laws (2023) | 395 |

**Total: 400 texts.**

### Source

**Revised Laws of Saint Lucia (2023)**, Attorney General's Chambers:
https://attorneygeneralchambers.com/laws-of-saint-lucia

The site serves each law as a table of contents. Every heading, part, section and schedule is
on its own HTML page. `scripts/lc_fetch.py` reads each law's table of contents and fetches
every page in order, keeping only the `<section id="document">` content.
`scripts/lc_convert.py` joins the pages into one Markdown file per law. The first block of each
file is the law's front page from the site: enactment history (Acts and S.I.s with
commencement dates), arrangement of sections, long title and commencement.

## What is not covered (gaps)

- **Subsidiary legislation.** Every page from a law's "Subsidiary Legislation" heading
  onward (regulations, rules, orders, S.I.s made under the Act) was skipped to keep the
  crawl reasonable. The site is slow, typically 3–20 s per page, and the Acts alone took
  about 20,000 page requests.
- Acts passed after 31 December 2023 are not in this revised edition. The site has no annual
  Acts series.

## Format

One Markdown file per law with YAML front matter (`title`, `identifier` (site slug), `type`,
`jurisdiction`, `language`, `enactment` (the enactment / amendment history line),
`last_amended` (revision date, 2023-12-31), `status`, `source`, `retrieved`, `edition`).
Parts, chapters, divisions and schedules are `##` headings and sections are `###` headings.
Tables are kept as Markdown tables. Amendment notes such as *(Amended by Act 34 of 1956)*
are kept in italics as on the site. In the codes, where articles are numbered paragraphs
inside a chapter or section page, the article number is shown as a bold label (`**14.**`).
Titles are kept in the site's capitals.

## Licence / copyright

Official legislative texts of Saint Lucia, published by the Government of Saint Lucia
(Attorney General's Chambers) for free public access. No terms of use restricting reuse were
found on the site. This is not an official publication.

## Regenerate

```sh
pip install -r scripts/requirements.txt
python3 scripts/lc_fetch.py      # ~20k pages into ../_raw/lc/html (4 threads, 0.5 s pause each)
python3 scripts/lc_convert.py    # Markdown
```

Retrieved: 2026-10-13.
