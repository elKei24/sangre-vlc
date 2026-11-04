#!/usr/bin/env python3
"""Fetch the official donation schedule, geocode locations, write data.json."""
import datetime as dt
import html
import json
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
GEOCACHE = "geocache.json"

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
    m = re.match(r"^(.*), (L'|LA|EL|ELS|LES|LOS|LAS)$", town)
    if m:
        town = m.group(2) + ("" if m.group(2) == "L'" else " ") + m.group(1)
    return town.split("/")[0]


def queries(town, loc, province):
    """Nominatim queries from most to least specific."""
    town = town_name(town)
    loc = re.sub(r"\(.*?\)", "", loc)
    street = ", ".join(p.strip() for p in loc.split(",")[1:]) if "," in loc else ""
    street = re.sub(r"\b(S/N|Nº|N\.|NUM\.?)\b", "", street, flags=re.I).strip(" ,")
    if street:
        yield f"{street}, {town}, {province}"
        yield f"{re.sub(r'[\d,].*$', '', street).strip()}, {town}, {province}"
    yield f"{town}, {province}"


def geocode(cache, town, loc, province):
    key = f"{province}|{town}|{loc}"
    if key in cache:
        return cache[key]
    hit = None
    for q in queries(town, loc, province):
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            {"format": "json", "limit": 1, "countrycodes": "es", "q": q})
        res = json.loads(get(url))
        time.sleep(1.1)  # Nominatim usage policy: max 1 request/second
        if res:
            hit = {"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"]),
                   "approx": q.count(",") == 1}
            break
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
    new = sum(k not in cache for k in places)
    print(f"{len(places)} places, {new} to geocode", file=sys.stderr)
    for i, (key, p) in enumerate(places.items(), 1):
        if i % 25 == 0:
            print(f"{i}/{len(places)}", file=sys.stderr)
        g = geocode(cache, p["town"], p["location"], p["province"])
        if g:
            out.append({**p, **g})
        else:
            print(f"not geocoded: {key}", file=sys.stderr)
        json.dump(cache, open(GEOCACHE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0, sort_keys=True)
    json.dump({"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
               "places": out}, open("data.json", "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
