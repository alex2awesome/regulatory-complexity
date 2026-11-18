#!/usr/bin/env python3
"""Merge public county datasets into corpus/counties/ca_counties_covariates.csv.

Workstream A7 of docs/2026-09-16-county-scale-up-plan.md: the keystone table.
Every column comes from a keyless public download already cached under
corpus/counties/raw/; nothing is invented, and a value that is not in a source
stays empty. Sources and vintages are recorded in corpus/counties/README.md.

    python3 pipeline/recon/build_county_covariates.py

Re-download the raw inputs (only needed when a vintage changes):
    python3 pipeline/recon/build_county_covariates.py --fetch
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "corpus/counties/raw"
OUT = ROOT / "corpus/counties"

UA = "Mozilla/5.0 (research; regulatory-complexity county covariates)"
SOURCES = {
    "rucc_2023.csv": "https://www.ers.usda.gov/media/5768/2023-rural-urban-continuum-codes.csv?v=70189",
    "poverty.csv": "https://www.ers.usda.gov/media/5496/poverty-estimates-for-the-united-states-states-and-counties-2023.csv?v=51214",
    "income_unemp.csv": "https://www.ers.usda.gov/media/5497/unemployment-and-median-household-income-for-the-united-states-states-and-counties-2000-23.csv?v=30518",
    "population.csv": "https://www.ers.usda.gov/media/5499/population-estimates-for-the-united-states-states-and-counties-2020-23.csv?v=80903",
    "education.csv": "https://www.ers.usda.gov/media/5495/educational-attainment-for-adults-age-25-and-older-for-the-united-states-states-and-counties-1970-2023.csv?v=70564",
    "gaz.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_counties_national.zip",
    # CA Dept of Finance E-1: population of every city and of the
    # unincorporated remainder of every county. The unincorporated share is the
    # exposure denominator for any county-administered program that only has
    # jurisdiction outside city limits (ADU permitting, environmental health).
    "dof_e1_2026.xlsx": "https://dof.ca.gov/media/docs/forecasting/Demographics/estimates-e1/E-1_2026_InternetVersion.xlsx",
    # Secretary of State Statement of Vote, November 5 2024 general election.
    # "President by County" gives the DEM share for all 58 counties. The SOS
    # publishes no xlsx at a guessable path (every candidate name returned an
    # S3 403); the complete PDF is the machine-reachable form.
    "sos_sov_2024_general.pdf": "https://elections.cdn.sos.ca.gov/sov/2024-general/sov/complete-sov.pdf",
    # ACS table B28002 (internet subscriptions by type) for all 58 counties,
    # via Census Reporter, which redistributes ACS keyless. api.census.gov now
    # answers "Missing Key"; see README. Release id is inside the payload.
    "acs_b28002_censusreporter.json": "https://api.censusreporter.org/1.0/data/show/latest?table_ids=B28002&geo_ids=050%7C04000US06",
    # State Controller county Financial Transactions Report, general-fund
    # revenues FY 2023-24, summed over every revenue line whose fund is the
    # General Fund. counties.bythenumbers.sco.ca.gov is a Socrata domain and
    # its SODA endpoint is keyless, which is the way around the gcc.sco.ca.gov
    # and publicpay.ca.gov 403s. 57 counties: San Francisco files a city FTR.
    "sco_county_general_fund_fy2024.json": (
        "https://bythenumbers.sco.ca.gov/resource/emxv-k8xv.json"
        "?$select=entity_name,sum(values)%20AS%20general_fund_revenues_usd"
        "&$where=fiscal_year=2024%20AND%20type=%27Revenues%27"
        "%20AND%20subcategory_1=%27General%27"
        "&$group=entity_name&$limit=100"
    ),
}
# BLS QCEW, one call per county (see fetch_qcew): local-government employment is
# the only keyless, uniform capacity proxy available for all 58 counties. It
# counts every local employer in the county (county government, cities, school
# districts, special districts), not county government alone; see README.
QCEW = "https://data.bls.gov/cew/data/api/2023/a/area/%s.csv"

# Subreddit subscriber counts. Every reddit.com path (www, old, api, oauth,
# about.json and the plain subreddit page) answers HTTP 403 "You've been
# blocked by network security" to scripted fetches, with or without a browser
# User-Agent. Arctic Shift's subreddit metadata endpoint carries the
# `subscribers` field and is keyless, so it is the substitute; see README for
# what that costs in vintage precision.
ARCTIC_SHIFT = "https://arctic-shift.photon-reddit.com/api/subreddits/search?subreddit=%s&limit=1"

# The 40 RCRC member counties (Rural County Representatives of California),
# rcrcnet.org membership list. Recorded here because the membership page is not
# a machine-readable download; it is California's own working definition of a
# rural county and differs from the USDA codes.
RCRC = {
    "Alpine", "Amador", "Butte", "Calaveras", "Colusa", "Del Norte", "El Dorado", "Glenn",
    "Humboldt", "Imperial", "Inyo", "Kings", "Lake", "Lassen", "Madera", "Mariposa",
    "Mendocino", "Merced", "Modoc", "Mono", "Napa", "Nevada", "Plumas", "San Benito",
    "Shasta", "Sierra", "Siskiyou", "Sutter", "Tehama", "Trinity", "Tuolumne", "Yuba",
}

# San Francisco is California's only consolidated city and county: the city is
# coterminous with the county, so DOF's E-1 lists it once with no city sub-row
# and no "Unincorporated" row. Its unincorporated share is 0 and its
# incorporated-city count is 1 by construction, not by estimate. Alpine,
# Mariposa and Trinity also have no city rows in E-1, for the opposite reason
# (no incorporated city at all), and the parser derives 100% for them from the
# county total minus zero city population.
CONSOLIDATED_CITY_COUNTY = {"San Francisco"}

# CalSAWS legacy consortium. calsaws.org/about-us/history/ states that the
# LEADER Replacement System (LRS) was Los Angeles County's system, and gives
# counts for the other two consortia -- 39 C-IV counties and 18 CalWIN (formerly
# WCDS) counties -- but names none of them. No fetchable source enumerates that
# membership (calwin.org 403s, its Wayback snapshot has no member list, the
# Wayback CDX API was offline, cwda.org/calsaws 404s), so the other 57 counties
# stay empty rather than being guessed. See README.
CALSAWS_LEGACY = {"Los Angeles": "LRS"}

COUNTY_SEATS = {
    "Alameda": "Oakland", "Alpine": "Markleeville", "Amador": "Jackson", "Butte": "Oroville",
    "Calaveras": "San Andreas", "Colusa": "Colusa", "Contra Costa": "Martinez",
    "Del Norte": "Crescent City", "El Dorado": "Placerville", "Fresno": "Fresno",
    "Glenn": "Willows", "Humboldt": "Eureka", "Imperial": "El Centro", "Inyo": "Independence",
    "Kern": "Bakersfield", "Kings": "Hanford", "Lake": "Lakeport", "Lassen": "Susanville",
    "Los Angeles": "Los Angeles", "Madera": "Madera", "Marin": "San Rafael",
    "Mariposa": "Mariposa", "Mendocino": "Ukiah", "Merced": "Merced", "Modoc": "Alturas",
    "Mono": "Bridgeport", "Monterey": "Salinas", "Napa": "Napa", "Nevada": "Nevada City",
    "Orange": "Santa Ana", "Placer": "Auburn", "Plumas": "Quincy", "Riverside": "Riverside",
    "Sacramento": "Sacramento", "San Benito": "Hollister", "San Bernardino": "San Bernardino",
    "San Diego": "San Diego", "San Francisco": "San Francisco", "San Joaquin": "Stockton",
    "San Luis Obispo": "San Luis Obispo", "San Mateo": "Redwood City",
    "Santa Barbara": "Santa Barbara", "Santa Clara": "San Jose", "Santa Cruz": "Santa Cruz",
    "Shasta": "Redding", "Sierra": "Downieville", "Siskiyou": "Yreka", "Solano": "Fairfield",
    "Sonoma": "Santa Rosa", "Stanislaus": "Modesto", "Sutter": "Yuba City",
    "Tehama": "Red Bluff", "Trinity": "Weaverville", "Tulare": "Visalia",
    "Tuolumne": "Sonora", "Ventura": "Ventura", "Yolo": "Woodland", "Yuba": "Marysville",
}


def _curl(url: str, dest: pathlib.Path, check: bool = True) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sL", "--max-time", "120", "-H", "User-Agent: " + UA,
                    url, "-o", str(dest)], check=check)


def fetch():
    """Re-download every input in SOURCES, overwriting the cache."""
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        dest = RAW / name
        _curl(url, dest)
        print("fetched %-36s %8d bytes" % (name, dest.stat().st_size))


def ensure_sources():
    """Download only the inputs missing from the cache, so a fresh clone builds."""
    for name, url in SOURCES.items():
        dest = RAW / name
        if dest.exists() and dest.stat().st_size:
            continue
        _curl(url, dest, check=False)
        if dest.exists():
            print("fetched %-36s %8d bytes" % (name, dest.stat().st_size))


try:                                    # the same candidate map the coverage sweep uses
    from county_coverage import COUNTY_SUBS
except ImportError:                     # pragma: no cover - script run from elsewhere
    COUNTY_SUBS = {}


def fetch_qcew(fips_list):
    """One QCEW call per county; cached under raw/qcew/."""
    import time
    d = RAW / "qcew"; d.mkdir(parents=True, exist_ok=True)
    for f in fips_list:
        path = d / ("%s.csv" % f)
        if path.exists():
            continue
        subprocess.run(["curl", "-sL", "--max-time", "60", "-H", "User-Agent: " + UA,
                        QCEW % f, "-o", str(path)], check=False)
        time.sleep(0.3)


def qcew_local_government() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    d = RAW / "qcew"
    for path in sorted(d.glob("*.csv")) if d.exists() else []:
        try:
            rows = list(csv.DictReader(path.open()))
        except Exception:
            continue
        loc = next((r for r in rows if r.get("own_code") == "3" and r.get("industry_code") == "10"
                    and r.get("agglvl_code") == "71"), None)
        tot = next((r for r in rows if r.get("own_code") == "0" and r.get("industry_code") == "10"
                    and r.get("agglvl_code") == "70"), None)
        if loc:
            out[path.stem] = dict(local_govt_employment_2023=loc["annual_avg_emplvl"],
                                  local_govt_wages_2023=loc["total_annual_wages"],
                                  local_govt_establishments_2023=loc["annual_avg_estabs"],
                                  total_employment_2023=(tot or {}).get("annual_avg_emplvl", ""))
    return out


def fetch_subreddit_about(subs):
    """One Arctic Shift call per candidate subreddit; cached under raw/subreddit_about/."""
    import time
    d = RAW / "subreddit_about"
    for sub in subs:
        path = d / ("%s.json" % sub.lower())
        if path.exists():
            continue
        _curl(ARCTIC_SHIFT % sub, path, check=False)
        time.sleep(0.3)


def subreddit_subscribers() -> dict[str, str]:
    """{subreddit (lowercased): subscribers} from the cached Arctic Shift payloads."""
    out: dict[str, str] = {}
    d = RAW / "subreddit_about"
    for path in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            data = json.loads(path.read_text()).get("data") or []
        except (json.JSONDecodeError, OSError):
            continue
        if not data or data[0].get("subscribers") is None:
            continue
        if (data[0].get("display_name") or "").lower() != path.stem:
            continue                            # never attribute a fuzzy match to the wrong sub
        out[path.stem] = str(data[0]["subscribers"])
    return out


_X_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_X_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _xlsx_col(ref: str) -> int:
    """'B12' -> 1. Cell references are how a sparse xlsx row says which column."""
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def xlsx_rows(path: pathlib.Path, sheet_name: str):
    """Minimal stdlib xlsx reader: one list of cell strings per row of one sheet.

    The repo is stdlib-only on purpose, so this unzips the workbook rather than
    taking an openpyxl dependency for a single table.
    """
    with zipfile.ZipFile(path) as z:
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target")
                for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        target = next((rels[s.get(_X_REL + "id")] for s in book.iter(_X_MAIN + "sheet")
                       if s.get("name") == sheet_name), None)
        if target is None:
            raise KeyError("no sheet %r in %s" % (sheet_name, path.name))
        shared = ["".join(t.text or "" for t in si.iter(_X_MAIN + "t"))
                  for si in (ET.fromstring(z.read("xl/sharedStrings.xml"))
                             if "xl/sharedStrings.xml" in z.namelist() else [])]
        inner = target if target.startswith("xl/") else "xl/" + target.lstrip("/")
        sheet = ET.fromstring(z.read(inner))
    for row in sheet.iter(_X_MAIN + "row"):
        cells: list[str] = []
        for c in row.iter(_X_MAIN + "c"):
            v = c.find(_X_MAIN + "v")
            txt = "" if v is None else (v.text or "")
            if c.get("t") == "s" and txt.isdigit():
                txt = shared[int(txt)]
            elif c.get("t") == "inlineStr":
                node = c.find(_X_MAIN + "is")
                txt = "".join(t.text or "" for t in node.iter(_X_MAIN + "t")) if node is not None else ""
            while len(cells) < _xlsx_col(c.get("r") or ""):
                cells.append("")
            cells.append(txt.strip())
        yield cells


def dof_unincorporated() -> dict[str, dict[str, str]]:
    """DOF E-1 -> {county: {pct_pop_unincorporated, n_incorporated_cities}}.

    E-1's city/county sheet is one block per county in alphabetical order: a
    county total row, then one row per incorporated city, then one
    "Unincorporated" row. Blocks are found by matching the next expected county
    name, because several cities share their county's name (Alameda, Amador,
    Colusa, ...). Rows with no population are the sheet's footer, not places.
    """
    path = RAW / "dof_e1_2026.xlsx"
    if not path.exists():
        return {}
    expected = sorted(COUNTY_SEATS)
    blocks: dict[str, dict] = {}
    idx, cur = 0, None
    for cells in xlsx_rows(path, "E-1 CityCounty2026"):
        name = cells[0] if cells else ""
        pop = _num(cells[2]) if len(cells) > 2 else ""
        if not name:
            continue
        if idx < len(expected) and name == expected[idx]:
            cur = expected[idx]
            idx += 1
            blocks[cur] = {"total": pop, "cities": 0, "city_pop": 0.0, "uninc": ""}
            continue
        if cur is None or not pop:
            continue
        if name.lower().startswith("unincorporated"):
            blocks[cur]["uninc"] = pop
        else:
            blocks[cur]["cities"] += 1
            blocks[cur]["city_pop"] += float(pop)
    out: dict[str, dict[str, str]] = {}
    for county, b in blocks.items():
        if not b["total"]:
            continue
        total = float(b["total"])
        if county in CONSOLIDATED_CITY_COUNTY:      # city coterminous with county
            out[county] = {"pct_pop_unincorporated": "0.0", "n_incorporated_cities": "1"}
            continue
        uninc = float(b["uninc"]) if b["uninc"] else total - b["city_pop"]
        if abs(b["city_pop"] + uninc - total) > 1:  # the block did not reconcile
            continue
        out[county] = {
            "pct_pop_unincorporated": str(round(100 * uninc / total, 1)) if total else "",
            "n_incorporated_cities": str(b["cities"]),
        }
    return out


def sos_president_dem_pct() -> dict[str, str]:
    """{county: DEM share of the 2024 presidential vote} from the SOS Statement of Vote.

    The SOV is a PDF, so the text layer is extracted with pdftotext -layout and
    cached beside it. In "President by County" each county row is followed by a
    "Percent" row whose first figure is the Democratic share; that printed
    figure is taken as-is rather than recomputed.
    """
    pdf = RAW / "sos_sov_2024_general.pdf"
    txt = RAW / "sos_sov_2024_general.txt"
    if not txt.exists() and pdf.exists():
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=False)
    if not txt.exists():
        return {}
    names = sorted(COUNTY_SEATS, key=len, reverse=True)
    row = re.compile(r"^(%s)\s{2,}[\d,]" % "|".join(re.escape(n) for n in names))
    pct = re.compile(r"^Percent\s+(\d+\.\d)%")
    out: dict[str, str] = {}
    contest, prev, pending = None, "", None
    for line in txt.read_text(errors="replace").splitlines():
        bare = line.strip()
        if bare in ("President", "United States Senate (Full Term)",
                    "United States Senate (Partial/Unexpired Term)"):
            if "General Election" in prev:          # a page header, not a mention
                contest = bare
        prev = bare
        if contest != "President":
            continue
        m = row.match(bare)
        if m:
            pending = m.group(1)
            continue
        m = pct.match(bare)
        if m and pending:
            out.setdefault(pending, m.group(1))     # first page wins; pages repeat headers
            pending = None
    return out


def acs_broadband() -> tuple[dict[str, str], str]:
    """({fips: percent of households with broadband of any type}, release id).

    Census Reporter's ACS mirror, table B28002: line 004 "Broadband of any
    type" over line 001 "Total" households.
    """
    path = RAW / "acs_b28002_censusreporter.json"
    if not path.exists():
        return {}, ""
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:                    # e.g. an api "Missing Key" html page
        return {}, ""
    out: dict[str, str] = {}
    for geoid, tables in payload.get("data", {}).items():
        est = tables.get("B28002", {}).get("estimate", {})
        total, broadband = est.get("B28002001"), est.get("B28002004")
        if total and broadband is not None:
            out[geoid[-5:]] = str(round(100 * float(broadband) / float(total), 1))
    return out, (payload.get("release") or {}).get("id", "")


def sco_general_fund() -> dict[str, str]:
    """{county: FY 2023-24 general-fund revenues, USD} from the State Controller FTR."""
    path = RAW / "sco_county_general_fund_fy2024.json"
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    out = {}
    for r in rows:
        value = _num(r.get("general_fund_revenues_usd", ""))
        if value:
            out[r["entity_name"].strip()] = str(int(float(value)))
    return out


def saws_consortium() -> dict[str, dict[str, str]]:
    """Legacy SAWS consortium per county, from the DHCS Medi-Cal renewals file.

    This column was blocked: CalSAWS publishes member COUNTS but names no member
    counties, calwin.org 403s, and no roster survives in the archive. The DHCS
    renewals-by-county file carries a `SAWS` label on every county-month, which
    names the consortium directly. All 58 counties appear, and all 58 change
    label during the migration, so the column records the county's LEGACY
    consortium (its earliest non-CalSAWS label) and the month it went live on
    CalSAWS. Verified 2026-09-16; found by packet P6.
    """
    src = RAW / "p6/p6_medical_renewals_by_county.csv"
    if not src.exists():
        return {}
    seen: dict[str, dict[str, str]] = {}
    for row in csv.DictReader(src.open(encoding="utf-8-sig", errors="replace")):
        county = (row.get("County") or "").strip()
        saws = (row.get("SAWS") or "").strip()
        year, month = (row.get("Year") or "").strip(), (row.get("Renewal Due Month") or "").strip()
        if not county or not saws:
            continue
        slot = seen.setdefault(county, dict(labels=set(), calsaws_from=None))
        slot["labels"].add(saws)
        if saws == "CalSAWS":
            # "Renewal Due Month" already carries the year, so do not prefix it again
            stamp = month if month.startswith(year) else "%s-%s" % (year, month)
            if slot["calsaws_from"] is None or stamp < slot["calsaws_from"]:
                slot["calsaws_from"] = stamp
    out = {}
    for county, slot in seen.items():
        legacy = sorted(slot["labels"] - {"CalSAWS"})
        out[county] = dict(calsaws_legacy_consortium="|".join(legacy),
                           calsaws_live_from=slot["calsaws_from"] or "")
    return out


# UIC 2024 codes whose own description says "Noncore", read off the file's
# Description attribute rather than assumed: 3 (adjacent to a large metro),
# 6 (adjacent to a small metro), 8 (non-adjacent, town of 5,000+) and
# 9 (non-adjacent, no such town). Codes 2, 5 and 7 are MICROPOLITAN, which is
# exactly the band the old RUCC >= 6 rule wrongly swept in.
UIC_NONCORE = {"3", "6", "8", "9"}


def urban_influence() -> tuple[dict[str, str], dict[str, str]]:
    """(uic code, noncore flag) per county FIPS, from the USDA Urban Influence Codes.

    Cached by the cross-scoping audit at raw/qa_usda_2024_urban_influence.csv.
    Falls back to empty, which leaves the columns blank rather than guessing.
    """
    src = RAW / "qa_usda_2024_urban_influence.csv"
    if not src.exists():
        return {}, {}
    uic, noncore = {}, {}
    for row in csv.DictReader(src.open(encoding="latin-1", errors="replace")):
        # long format, like the other ERS files: (fips, state, area, attribute, value)
        fips = (row.get("FIPS-UIC") or row.get("FIPS") or row.get("FIPStxt") or "").strip().zfill(5)
        if not fips.startswith("06") or (row.get("Attribute") or "").strip() != "UIC_2024":
            continue
        code = (row.get("Value") or "").strip()
        if not code:
            continue
        uic[fips] = code
        noncore[fips] = "1" if code in UIC_NONCORE else "0"
    return uic, noncore


def long_table(path: pathlib.Path, fips_col: int, state_col: int, attr_col: int, val_col: int,
               state: str = "CA") -> dict[str, dict[str, str]]:
    """ERS files are long: (fips, state, area, attribute, value) -> {fips: {attr: value}}."""
    out: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="latin-1") as f:
        for row in csv.reader(f):
            if len(row) <= max(fips_col, state_col, attr_col, val_col):
                continue
            if row[state_col].strip().strip('"') != state:
                continue
            fips = row[fips_col].strip().strip('"').zfill(5)
            slot = out.setdefault(fips, {})
            slot["_area_name"] = row[2].strip().strip('"')
            slot[row[attr_col].strip().strip('"')] = row[val_col].strip().strip('"')
    return out


def _num(x):
    if x in (None, "", "NA", "(NA)"):
        return ""
    return x.replace(",", "").replace("$", "").strip()


def build():
    ensure_sources()
    rucc = long_table(RAW / "rucc_2023.csv", 0, 1, 3, 4)
    pov = long_table(RAW / "poverty.csv", 0, 1, 3, 4)
    inc = long_table(RAW / "income_unemp.csv", 0, 1, 3, 4)
    pop = long_table(RAW / "population.csv", 0, 1, 3, 4)
    edu = long_table(RAW / "education.csv", 0, 1, 3, 4)

    # land area from the Census gazetteer (tab separated, inside the zip)
    land: dict[str, tuple[str, str]] = {}
    with zipfile.ZipFile(RAW / "gaz.zip") as z:
        name = next(n for n in z.namelist() if n.endswith(".txt"))
        text = z.read(name).decode("latin-1")
    for row in csv.reader(io.StringIO(text), delimiter="\t"):
        if len(row) < 8 or row[0].strip() != "CA":
            continue
        land[row[1].strip().zfill(5)] = (row[6].strip(), row[3].strip())

    fips_all = sorted(f for f in rucc if f.startswith("06") and f != "06000")
    fetch_qcew(fips_all)
    qcew = qcew_local_government()
    saws = saws_consortium()
    uic, noncore = urban_influence()
    uninc = dof_unincorporated()
    dem_pct = sos_president_dem_pct()
    broadband, acs_release = acs_broadband()
    general_fund = sco_general_fund()
    fetch_subreddit_about(sorted({s for subs in COUNTY_SUBS.values() for s in subs}))
    subscribers = subreddit_subscribers()
    rows = []
    for fips in fips_all:
        name = rucc[fips].get("_area_name", "").replace(" County", "").strip()
        area = land.get(fips, ("", ""))[0]
        p = _num(pop.get(fips, {}).get("POP_ESTIMATE_2023", ""))
        density = ""
        if p and area:
            try:
                density = str(round(float(p) / float(area), 1))
            except (ValueError, ZeroDivisionError):
                density = ""
        rucc_code = _num(rucc[fips].get("RUCC_2023", ""))
        rows.append({
            "county": name,
            "fips": fips,
            "county_seat": COUNTY_SEATS.get(name, ""),
            "pop_2023": p,
            "pop_census_2020": _num(pop.get(fips, {}).get("CENSUS_2020_POP", "")),
            "pop_change_2020_2023_pct": (
                str(round(100 * (float(p) / float(_num(pop[fips]["CENSUS_2020_POP"])) - 1), 2))
                if p and _num(pop.get(fips, {}).get("CENSUS_2020_POP", "")) else ""),
            "land_area_sqmi": area,
            "pop_density_per_sqmi": density,
            "rucc_2023": rucc_code,
            "rucc_description": rucc[fips].get("Description", ""),
            "metro_2023": _num(inc.get(fips, {}).get("Metro_2023", "")),
            # "Noncore" means outside BOTH metro and micropolitan statistical areas.
            # An earlier version tested RUCC >= 6, which is wrong: RUCC 6 and 7 are
            # the nonmetro band with 5,000-19,999 urban residents, i.e. largely
            # MICROPOLITAN. That rule called 15 counties noncore and misclassified
            # Alpine, Del Norte, Inyo and Lassen, all micropolitan per the USDA
            # Urban Influence Codes. The UIC file settles it; correct count is 11.
            # (Found by the cross-scoping audit, 2026-09-16.)
            "is_noncore": noncore.get(fips, ""),
            "uic_2024": uic.get(fips, ""),
            "rcrc_member": "1" if name in RCRC else "0",
            "median_hh_income_2023": _num(pov.get(fips, {}).get("MEDHHINC_2023", "")),
            "poverty_rate_2023": _num(pov.get(fips, {}).get("PCTPOVALL_2023", "")),
            "poverty_count_2023": _num(pov.get(fips, {}).get("POVALL_2023", "")),
            "unemployment_rate_2023": _num(inc.get(fips, {}).get("Unemployment_rate_2023", "")),
            "civilian_labor_force_2023": _num(inc.get(fips, {}).get("Civilian_labor_force_2023", "")),
            "pct_bachelors_2019_23": _num(next(
                (v for k, v in edu.get(fips, {}).items()
                 if k.startswith("Percent of adults with a bachelor's degree or higher")
                 and "2019-23" in k), "")),
            "pct_not_hs_graduate_2019_23": _num(next(
                (v for k, v in edu.get(fips, {}).items()
                 if k.startswith("Percent of adults who are not high school graduates")
                 and "2019-23" in k), "")),
            "local_govt_employment_2023": qcew.get(fips, {}).get("local_govt_employment_2023", ""),
            "local_govt_establishments_2023": qcew.get(fips, {}).get("local_govt_establishments_2023", ""),
            "local_govt_wages_2023": qcew.get(fips, {}).get("local_govt_wages_2023", ""),
            "total_employment_2023": qcew.get(fips, {}).get("total_employment_2023", ""),
            "local_govt_empl_per_1k_pop": (
                str(round(1000 * float(qcew[fips]["local_govt_employment_2023"]) / float(p), 2))
                if p and qcew.get(fips, {}).get("local_govt_employment_2023") else ""),
            "avg_local_govt_wage_2023": (
                str(round(float(qcew[fips]["local_govt_wages_2023"]) /
                          float(qcew[fips]["local_govt_employment_2023"])))
                if qcew.get(fips, {}).get("local_govt_employment_2023") not in (None, "", "0") else ""),
            # County-government FTE has no keyless source: the State Controller's
            # Government Compensation in California (gcc.sco.ca.gov, publicpay.ca.gov)
            # answers 403 to every scripted path and has no mirror. Stays empty.
            "county_employees_fte": "",
            "county_general_fund_usd": general_fund.get(name, ""),
            "general_fund_per_capita": (
                str(round(float(general_fund[name]) / float(p), 2))
                if p and general_fund.get(name) else ""),
            "pct_pop_unincorporated": uninc.get(name, {}).get("pct_pop_unincorporated", ""),
            "n_incorporated_cities": uninc.get(name, {}).get("n_incorporated_cities", ""),
            "broadband_subscription_pct": broadband.get(fips, ""),
            "calsaws_legacy_consortium": saws.get(name, {}).get("calsaws_legacy_consortium", ""),
            "calsaws_live_from": saws.get(name, {}).get("calsaws_live_from", ""),
            # permit_portal_vendor, code_host and eh_department_structure are
            # filled by the ADU (A3) and environmental-health (A5) workstreams,
            # which inspect each county's own site. Not written here.
            "permit_portal_vendor": "",
            "code_host": "",
            "county_subreddit": ("r/" + COUNTY_SUBS.get(name, [""])[0]) if COUNTY_SUBS.get(name) else "",
            "n_candidate_subreddits": str(len(COUNTY_SUBS.get(name, []))),
            "subreddit_subscribers": (
                subscribers.get(COUNTY_SUBS[name][0].lower(), "") if COUNTY_SUBS.get(name) else ""),
            "vote_2024_dem_pct": dem_pct.get(name, ""),
            "eh_department_structure": "",
        })
    cols = list(rows[0])
    path = OUT / "ca_counties_covariates.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    filled = {c: sum(1 for r in rows if r[c] not in ("", None)) for c in cols}
    print("wrote %s  %d rows x %d cols" % (path, len(rows), len(cols)))
    print("\ncoverage (of %d counties):" % len(rows))
    for c in cols:
        flag = "" if filled[c] == len(rows) else ("  <-- EMPTY, needs a source" if filled[c] == 0 else "  <-- partial")
        print("  %-30s %2d%s" % (c, filled[c], flag))
    (OUT / "covariates_coverage.json").write_text(json.dumps(dict(
        n_counties=len(rows), filled=filled,
        sources={**SOURCES, "qcew/<fips>.csv": QCEW,
                 "subreddit_about/<sub>.json": ARCTIC_SHIFT},
        acs_release=acs_release), indent=1))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="re-download the raw inputs first")
    args = ap.parse_args(argv)
    if args.fetch:
        fetch()
    build()


if __name__ == "__main__":
    main()
