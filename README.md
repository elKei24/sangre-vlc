# sangre-vlc

**Open the map: https://elkei24.github.io/sangre-vlc/**

Map of the blood donation points in the Comunitat Valenciana (Valencia, Castellón, Alicante). Select a pin to see the dates and hours. Use the date filter to show only the points available in a given period.

The data comes from the [Centro de Transfusión](https://centro-transfusion.san.gva.es/es/puntos-de-donacion) web page. That page does not send CORS headers, so a browser cannot read it directly. A GitHub Actions workflow runs `scrape.py` each day, geocodes new locations with Nominatim and commits `data.json`. GitHub Pages serves `index.html` and `data.json` as static files.

## Files

- `index.html`, `app.js`, `style.css`: the map (Leaflet, no build step).
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

## Dependency updates

`.github/workflows/renovate.yml` runs a self-hosted Renovate each Monday. It needs the repository secret `RENOVATE_TOKEN`: a personal access token with `repo` and `workflow` scope, so that Renovate can also update the files in `.github/workflows`. Minor and patch updates merge automatically after the CI workflow passes.
