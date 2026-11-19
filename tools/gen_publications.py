#!/usr/bin/env python3
"""Regenerate the publications section of index.html from rsernaoliver.bib.

Usage: python3 tools/gen_publications.py [--check]

The region between <!-- Publications start--> and <!-- Publications end--> in
index.html is replaced with a rendering derived from the BibTeX file.
Category order is fixed (CATEGORIES); entries within a category keep the
order given there. PDF links resolve to files in publications/ named after
the bib key (case- and hyphen-normalized); entries without a local PDF fall
back to url/doi fields.

Dependencies: Python 3 standard library only.
"""

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "publications" / "rsernaoliver.bib"
INDEX = ROOT / "index.html"
PUBDIR = ROOT / "publications"

START_MARKER = "<!-- Publications start-->"
END_MARKER = "<!-- Publications end-->"

# Fixed section order; keep in sync with the site's structure.
CATEGORIES = [
    ("Journal Articles", ["Steiner_CSM18", "Craciunas_JRTS16"]),
    ("Conference Publications", [
        "Finzi_ECRTS22", "Craciunas_WFCS21", "Serna_RTAS18",
        "Craciunas_RTNS16", "Serna_RTN16", "Craciunas_RTNS14",
        "Serna_CAMAD14", "Craciunas_ETFA14", "Steine_MSWIM11",
        "Serna_RTN10", "Serna_SAC10", "Rousselot_EMS09", "Serna_MASS09",
        "Schoffs_SENSAPEAL09", "Serna_RTN09",
    ]),
    ("Demos and Work-in-Progress", [
        "Craciunas_RTASDEMO18", "Serna_SENSYS09", "Serna_RTSSWIP08",
    ]),
    ("Technical Reports", [
        "Craciunas_CORR17", "Craciunas_ETR17", "Serna_TR09", "Stanley-Marbell_ESR08",
    ]),
    ("Books and Theses", [
        "Ahmadian_DREAMS18", "Serna_PhD-TUKL10",
    ]),
    ("Patents", [
        "US20240095068A1", "US11367024B2", "EP4125249A1", "EP3468118",
        "EP3139547", "US2016246646",
    ]),
]

# Venue/location text rendered as on the original hand-written page.
VENUE_OVERRIDES = {
    "Steine_MSWIM11": "14th ACM International Conference on Modeling, Analysis and Simulation of Wireless and Mobile Systems, Miami, FL, USA, October 2011",
    "Serna_RTSSWIP08": "In Proceedings of the Work-in-Progress Session, 29th IEEE Real-Time Systems Symposium (RTSS08), Barcelona, Spain, December 2008",
}

def parse_bibtex(text):
    """Minimal stdlib BibTeX parser: {key: {field: value, '_type': entrytype}}."""
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,([^@]*)", text, re.S):
        etype, key, body = m.group(1), m.group(2), m.group(3)
        fields = {}
        for fm in re.finditer(r'(\w+)\s*=\s*((?:\{(?:[^{}]|\{[^{}]*\})*\})|(?:"[^"]*")|(?:\S+))', body):
            name, val = fm.group(1).lower(), fm.group(2)
            if val[:1] in "{\"":
                val = val[1:-1]
            fields[name] = val.strip()
        fields["_type"] = etype.lower()
        entries[key] = fields
    return entries

def detex(s):
    """Convert common TeX escapes in bib strings to plain text."""
    if not s:
        return ""
    rep = {
        '{\\"u}': "ü", '{\\"o}': "ö", '{\\"a}': "ä", '\\"{i}': "ï", '{\\"i}': "ï",
        "{\\'e}": "é", "{\\`e}": "è", "\\'{E}": "É", "\\\"{i}": "ï",
        "\\'e": "é", "\\`e": "è",
    }
    for k, v in rep.items():
        s = s.replace(k, v)
    s = s.replace("L'\\'{E}cole d'\\'{E}t\\'{e} Temps R\\'{e}el", "L'École d'Été Temps Réel")
    s = re.sub(r"[{}\\]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def fmt_authors(fields):
    names = [a.strip() for a in fields.get("author", "").split(" and ") if a.strip()]
    out = []
    for name in names:
        if "," in name:
            last, first = (x.strip() for x in name.split(",", 1))
            if last.lower() == "serna oliver":
                out.append("R. Serna Oliver")
            else:
                ini = " ".join(f"{p[0]}." for p in first.split())
                out.append(f"{ini} {last}".strip())
        else:
            parts = name.split()
            if len(parts) >= 3 and parts[0].lower() == "silviu":
                out.append("S.S. Craciunas")
            elif parts[-2:] == ["Serna", "Oliver"]:
                # Compound surname without comma form, e.g. "R. Serna Oliver"
                ini = ".".join(p[0] for p in parts[:-2]) + "."
                out.append(f"{ini} Serna Oliver" if ini else "Serna Oliver")
            elif len(parts) == 1:
                out.append(parts[0])
            else:
                ini = ".".join(p[0] for p in parts[:-1]) + "."
                out.append(f"{ini} {' '.join(parts[-1:])}")
    if not out:
        return ""
    if len(out) == 1:
        return out[0]
    return ", ".join(out[:-1]) + " and " + out[-1]

def local_pdf(key):
    for cand in (key, key.upper(), key.replace("-", "_"), key.upper().replace("-", "_"),
                 key.replace("_", "-"), key.upper().replace("_", "-")):
        f = PUBDIR / f"{cand}.pdf"
        if f.exists():
            return f"publications/{f.name}"
    return None

def link_for(key, fields):
    """(href, label) for the trailing bracket link, or None."""
    if lp := local_pdf(key):
        return lp, "PDF"
    if fields.get("url"):
        return fields["url"], "Link"
    if fields.get("doi"):
        return f"https://doi.org/{fields['doi']}", "DOI"
    return None

def esc(s):
    return html.escape(detex(s), quote=False)

def render_entry(key, f):
    year = f.get("year", "")
    award = ('<span class="award">(Best paper award)</span> '
             if "best paper" in f.get("note", "").lower() else "")
    parts = [f'<p>{award}<em>{esc(fmt_authors(f))}</em> - <strong>{esc(f.get("title", ""))}</strong>']

    def add_link():
        if lnk := link_for(key, f):
            href, label = lnk
            parts.append(f' [<a href="{href}" target="_blank" rel="noopener noreferrer">{label}</a>]')

    if key == "Serna_PhD-TUKL10":
        parts.append(". " + esc(f"Ph.D. thesis, {f.get('school', '')}, {f.get('month', '')} {year}."))
        if (PUBDIR / "thesis.pdf").exists():
            parts.append(' [<a href="publications/thesis.pdf" target="_blank" rel="noopener noreferrer">PDF</a>]')
    elif key == "Ahmadian_DREAMS18":
        parts.append(". " + esc(f"Chapter in \"{f.get('title', '')}\", {f.get('publisher', '')}, {year}."))
        if f.get("url"):
            parts.append(f' [<a href="{f["url"]}" target="_blank" rel="noopener noreferrer">Link</a>]')
    elif f["_type"] == "patent":
        line = ". " + esc(f"Patent {f.get('number', key)}, {year}.")
        if f.get("note"):
            line += " " + esc(f"({f['note']})")
        parts.append(line)
        if f.get("url"):
            parts.append(f' [<a href="{f["url"]}" target="_blank" rel="noopener noreferrer">Link</a>]')
    else:
        if key in VENUE_OVERRIDES:
            parts.append(". " + esc(VENUE_OVERRIDES[key]))
        else:
            venue = []
            if bt := f.get("booktitle"):
                venue.append(f"In {detex(bt)}")
            elif j := f.get("journal"):
                venue.append(f"In {detex(j)}")
            elif hp := f.get("howpublished"):
                venue.append(detex(hp))
            if inst := f.get("institution"):
                venue.append(detex(inst))
            if vol := f.get("volume"):
                loc = f"Volume {vol}"
                if f.get("number"):
                    loc += f", Issue {f['number']}"
                if pg := f.get("pages"):
                    loc += f", pp. {pg.replace('--', '-')}"
                venue.append(loc)
            elif pg := f.get("pages"):
                venue.append(f"pp. {pg.replace('--', '-')}")
            if addr := f.get("address"):
                month = f.get("month", "")
                venue.append(f"{detex(addr)}, {month} {year}".strip())
            else:
                venue.append(year)
            txt = ", ".join(v for v in venue if v)
            if not txt.endswith("."):
                txt += "."
            parts.append(". " + esc(txt))
        add_link()
    body = "".join(parts) + "</p>"
    return f'\t\t\t<li>\n\t\t\t{body}\n\t\t\t</li>\n'

def render_all(entries):
    chunks = []
    for title, keys in CATEGORIES:
        chunk = f"\t\t<h3>{title}</h3>\n\n\t\t<ul>\n"
        for k in keys:
            chunk += render_entry(k, entries[k])
        chunk += "\t\t</ul>\n"
        chunks.append(chunk)
    return "\n".join(chunks)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if index.html differs from the bib-derived rendering")
    args = ap.parse_args()

    entries = parse_bibtex(BIB.read_text())

    listed = [k for _, keys in CATEGORIES for k in keys]
    if len(set(listed)) != len(listed):
        sys.exit("Duplicate keys in CATEGORIES")
    missing = [k for k in listed if k not in entries]
    if missing:
        sys.exit(f"Keys in CATEGORIES but not in bib: {missing}")
    unplaced = [k for k in entries if k not in listed]
    if unplaced:
        print(f"WARNING: bib entries not rendered (add to a category): {unplaced}", file=sys.stderr)
        if args.check:
            sys.exit(1)

    index = INDEX.read_text()
    pat = re.compile(re.escape(START_MARKER) + r"\n?(.*?)" + re.escape(END_MARKER), re.S)
    m = pat.search(index)
    if not m:
        sys.exit("Publication markers not found in index.html")
    rendered = render_all(entries)
    updated = pat.sub(lambda _: START_MARKER + "\n\n" + rendered + "\n\t\t" + END_MARKER, index, count=1)

    if args.check:
        sys.exit(0 if updated == index else 1)

    INDEX.write_text(updated)
    print(f"index.html publications section regenerated "
          f"({len(listed)} entries across {len(CATEGORIES)} categories)")

if __name__ == "__main__":
    main()
