# sangre-vlc

**Open the map: https://elkei24.github.io/sangre-vlc/**

Map of the blood donation points in the Comunitat Valenciana (Valencia, Castellón, Alicante). Select a pin to see the dates and hours. Use the date filter to show only the points available in a given period.

The data comes from the [Centro de Transfusión](https://centro-transfusion.san.gva.es/es/puntos-de-donacion) web page. That page does not send CORS headers, so a browser cannot read it directly. A GitHub Actions workflow runs the scraper each day, geocodes new locations with Nominatim and commits `site/data.json`. A second workflow deploys the `site` folder to GitHub Pages on each push to `main`.

## Layout

- `site/`: the web site (Leaflet map, no build step) and the generated `data.json`.
- `scripts/scrape.py`: fetches the three province pages, parses the schedule and writes `site/data.json`. Python standard library only.
- `scripts/geocache.json`: cache of geocoded locations. Delete an entry to geocode it again.
- `.github/workflows/update.yml`: daily data update.
- `.github/workflows/pages.yml`: deploys `site/` to GitHub Pages.
- `.github/workflows/ci.yml`: checks that run on each pull request.
- `.github/workflows/renovate.yml`: weekly dependency updates.

## Run locally

```sh
python3 scripts/test_scrape.py
python3 scripts/scrape.py          # first run geocodes all locations, about 7 minutes
python3 -m http.server -d site     # open http://localhost:8000
```

## Deploy

GitHub Pages is set to "GitHub Actions" as the source. The `pages.yml` workflow deploys on each push to `main`.

## Secrets

- `DEPLOY_KEY`: private SSH deploy key with write access. The daily data update pushes to `main` with it, because the branch ruleset lets only this key push without a pull request.
- `RENOVATE_TOKEN`: see below.

## Dependency updates

`.github/workflows/renovate.yml` runs a self-hosted Renovate each Monday. It needs the repository secret `RENOVATE_TOKEN`: a personal access token with `repo` and `workflow` scope, so that Renovate can also update the files in `.github/workflows`. Minor and patch updates merge automatically after the CI workflow passes.
