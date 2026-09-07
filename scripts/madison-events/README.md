# madison-events

Daily local-events scout: checks a list of event listings/sources, filters to
what's within a radius of home over the next few days, geocodes venues, and
emails a roundup newsletter.

## How it runs

```
[agent scans sources.txt listings]
geo.py geocode "<venue>"        → lat/lon  (US Census geocoder)
geo.py dist <lat> <lon>         → miles from home
   [keep only items within radius_miles]
templates/newsletter.html       → rendered email
```

Like the other pipelines, the discovery/writing is done by the scheduled
agent; `geo.py` and the data files carry the deterministic weight.

## Files

| File | Purpose |
|---|---|
| `geo.py` | Distance + geocoding helper. `geo.py dist <lat> <lon>` prints miles from home; `geo.py geocode "<address or city, WI>"` prints coords. Uses the **US Census geocoder — Nominatim blocks this server's IP**, so don't swap it casually. |
| `venues.json` | **The cache that matters:** pre-verified coordinates for known venues (park trailheads, venues whose street address geocodes wrong). Check this file *before* geocoding anything. `miles` values are from home. |
| `sources.txt` | One URL per line — the listings pages the scout reads. |
| `config.json` | Home coordinates (placeholder here), radius (miles), lookahead window, geocoder URL template. |
| `templates/newsletter.html` | Dark-theme email template. ⭐ marks the user's favorite venues. |
| `state.json` (generated) | Dedupe history so an event isn't emailed twice. |

## Setup

1. Put your home address + coordinates in `config.json` (`lat`/`lon` drive
   every distance; the address string is informational).
2. Tune `radius_miles` and `window_days`.
3. Add your local listings pages to `sources.txt`.
4. As the scout finds venues that geocode badly (parks, campuses), add
   verified entries to `venues.json` — this is what makes it accurate over
   time.

## Gotchas

- County parks and trailheads routinely fail the census geocoder or resolve
  to the wrong town; trust `venues.json` over live geocoding.
- Deleting `state.json` re-announces everything currently listed.
