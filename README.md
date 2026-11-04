# sangre-vlc

Map of the blood donation points in the Comunitat Valenciana (Valencia, Castellón, Alicante).

The data comes from the [Centro de Transfusión](https://centro-transfusion.san.gva.es/es/puntos-de-donacion) web page. That page does not send CORS headers, so a browser cannot read it directly. A GitHub Actions workflow runs `scrape.py` each day, geocodes new locations with Nominatim and commits `data.json`. GitHub Pages serves `index.html` and `data.json` as static files.

## Files

- `index.html`: the map (Leaflet, no build step).
- `scrape.py`: fetches the three province pages, parses the schedule and writes `data.json`. Python standard library only.
- `geocache.json`: cache of geocoded locations. Delete an entry to geocode it again.
- `.github/workflows/update.yml`: daily update job.

## Run locally

```sh
python3 test_scrape.py
python3 scrape.py          # first run geocodes all locations, about 7 minutes
python3 -m http.server     # open http://localhost:8000
```

## Deploy

Enable GitHub Pages for the repository with the source "Deploy from a branch", branch `main`, folder `/`.
