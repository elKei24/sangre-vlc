#!/usr/bin/env python3
"""Fetch the official donation schedule, geocode locations, write data.json."""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://centro-transfusion.san.gva.es/es/puntos-de-donacion?provincia="
PROVINCES = {"valencia": "Valencia", "castellon": "Castellón", "alicante": "Alicante"}
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
UA = "sangre-vlc (https://github.com/elKei24/sangre-vlc)"
ROOT = pathlib.Path(__file__).resolve().parents[1]
GEOCACHE = ROOT / "scripts" / "geocache.json"
DATA = ROOT / "site" / "data.json"

DATE_RE = re.compile(r'<p class="subtitulo2">[^<]*?(\d+) de (\w+)</p>')
ROW_RE = re.compile(
    r'poblacion">\s*<b[^>]*>[^<]*</b>([^<]*)</td>\s*'
    r'<td[^>]*ubicacion">\s*<b[^>]*>[^<]*</b>([^<]*)</td>\s*'
    r'<td[^>]*horario">\s*<b[^>]*>[^<]*</b>([^<]*)</td>')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def to_date(day, month, today):
    d = dt.date(today.year, MONTHS.index(month.lower()) + 1, int(day))
    # The page shows no year; a date far in the past belongs to next year.
    return d.replace(year=d.year + 1) if d < today - dt.timedelta(days=60) else d


def parse(page, today):
    """Yield (date, town, location, hours) for each schedule row."""
    parts = re.split(r'(<p class="subtitulo2">[^<]*?\d+ de \w+</p>)', page)
    for i in range(1, len(parts), 2):
        day, month = DATE_RE.match(parts[i]).groups()
        date = to_date(day, month, today)
        for town, loc, hours in ROW_RE.findall(parts[i + 1]):
            hours = clean(hours)
            if hours == "-":
                continue
            yield date, clean(town), clean(loc), hours


def town_name(town):
    # "POBLA DE VALLBONA, LA" -> "LA POBLA DE VALLBONA"; "ALMASSORA/ALMAZORA" -> "ALMASSORA"
    m = re.match(r"^(.*?),? \(?(L'|LA|EL|ELS|LES|LOS|LAS)\)?$", town)
    if m:
        town = m.group(2) + ("" if m.group(2) == "L'" else " ") + m.group(1)
    return town.split("/")[0]


STREET_RE = re.compile(
    r"\b(C/|CALLE|CARRER|AVDA?\.?|AVINGUDA|AVENIDA|AV\.|PLAZA|PLAÇA|PL\.|CTRA\.?|CARRETERA|"
    r"CAMI|CAMINO|PASEO|PASSEIG|POL\.?|POLIGONO|POLÍGONO|PARTIDA|RONDA|GRAN VIA|PARC\b|PARQUE)", re.I)
ROOM_RE = re.compile(
    r"\b(ANTESALA|SAL[OÓ]N? D(E |')ACT[EO]S|SALA|SALITA|PLANTA|HALL|GIMNASIO|BIBLIOTECA|AULA|"
    r"VEST[IÍ]BULO|PASILLO|LOCAL|SOLO|S[OÓ]LO|EXCLUSIVA)\b.*$", re.I)
ABBREV = {"C.S.": "CENTRO DE SALUD ", "C.S": "CENTRO DE SALUD ", "HOSP.": "HOSPITAL",
          "I.E.S.": "IES", "C.E.I.P.": "CEIP", "AJUNT.": "AJUNTAMENT", "AYTO.": "AYUNTAMIENTO"}


def venue(loc):
    """'ALCOI-CIP FP BATOI SALÓN DE ACTOS, C/ ...' -> 'CIP FP BATOI'"""
    head = loc.split(",")[0]
    head = re.sub(r"^[^-]*-\s*", "", head)  # town prefix
    head = head.split("-")[0]
    for k, v in ABBREV.items():
        head = head.replace(k, v)
    return clean(ROOM_RE.sub("", head))


def street(loc):
    """Comma parts from the first one that names a street, e.g. 'C/ COLON, 44'"""
    parts = [p.strip() for p in loc.split(",")]
    for i, part in enumerate(parts[1:], 1):
        if STREET_RE.search(part):
            s = ", ".join(p for p in parts[i:] if p).split(" - ")[0]
            return re.sub(r"\b(S/N|Nº|N\.|NUM\.?)\b", "", s, flags=re.I).strip(" ,")
    return ""


def queries(loc):
    """Search texts from most to least specific; the town comes from the bounding box."""
    loc = re.sub(r"\(.*?\)", "", loc)
    st, ven = street(loc), venue(loc)
    if st:
        yield st
    if ven:
        yield ven
    if st and re.search(r"\d", st):
        yield re.sub(r"[\d,].*$", "", st).strip()


def nominatim(params):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"format": "json", "limit": 1, "countrycodes": "es", **params})
    res = json.loads(get(url))
    time.sleep(1.1)  # Nominatim usage policy: max 1 request/second
    return res[0] if res else None


def geocode(cache, towns, town, loc, province):
    """Find the town first, then search the location only inside the town's bounding box."""
    key = f"{province}|{town}|{loc}"
    if key in cache:
        return cache[key]
    name = town_name(town)
    if name not in towns:
        towns[name] = nominatim({"q": f"{name}, {province}"})
    t = towns[name]
    hit = None
    if t:
        south, north, west, east = t["boundingbox"]
        for q in queries(loc):
            r = nominatim({"q": q, "viewbox": f"{west},{south},{east},{north}", "bounded": 1})
            if r:
                hit = {"lat": float(r["lat"]), "lon": float(r["lon"]), "approx": False}
                break
        else:
            hit = {"lat": float(t["lat"]), "lon": float(t["lon"]), "approx": True}
    cache[key] = hit
    return hit


def main():
    today = dt.date.today()
    try:
        cache = json.load(open(GEOCACHE, encoding="utf-8"))
    except FileNotFoundError:
        cache = {}
    places = {}
    for slug, province in PROVINCES.items():
        page = get(BASE + slug)
        n = 0
        for date, town, loc, hours in parse(page, today):
            n += 1
            key = f"{province}|{town}|{loc}"
            p = places.setdefault(key, {"town": town, "location": loc,
                                        "province": province, "slots": []})
            p["slots"].append([date.isoformat(), hours])
        print(f"{province}: {n} slots", file=sys.stderr)
        if n == 0:
            sys.exit(f"no rows parsed for {province}; page layout changed?")
    out = []
    towns = {}
    new = sum(k not in cache for k in places)
    print(f"{len(places)} places, {new} to geocode", file=sys.stderr)
    for i, (key, p) in enumerate(places.items(), 1):
        if i % 25 == 0:
            print(f"{i}/{len(places)}", file=sys.stderr)
        g = geocode(cache, towns, p["town"], p["location"], p["province"])
        if not g:
            print(f"not geocoded: {key}", file=sys.stderr)
        out.append({**p, **(g or {})})
        json.dump(cache, open(GEOCACHE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0, sort_keys=True)
    json.dump({"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
               "places": out}, open(DATA, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
