#!/usr/bin/env python3
"""Geo helpers for the Madison events job.
  distance: python3 geo.py dist <lat> <lon>        -> miles from home
  geocode:  python3 geo.py geocode "<venue address or city, WI>"
Reads home coords from config.json next to this script. Uses the US Census
geocoder (Nominatim blocks this server)."""
import json, math, sys, urllib.parse, urllib.request
from pathlib import Path

CFG = json.loads((Path(__file__).parent / "config.json").read_text())
HOME = (CFG["home"]["lat"], CFG["home"]["lon"])

def miles(lat, lon):
    R = 3958.8
    p1, p2 = math.radians(HOME[0]), math.radians(lat)
    dp = math.radians(lat - HOME[0]); dl = math.radians(lon - HOME[1])
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def geocode(q):
    url = CFG["geocoder"].replace("{ADDR_URL}", urllib.parse.quote(q))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    m = d.get("result", {}).get("addressMatches", [])
    if not m:
        return None
    c = m[0]["coordinates"]
    return (c["y"], c["x"], m[0].get("matchedAddress", q))

if __name__ == "__main__":
    if sys.argv[1] == "dist":
        print(f"{miles(float(sys.argv[2]), float(sys.argv[3])):.1f}")
    elif sys.argv[1] == "geocode":
        r = geocode(sys.argv[2])
        if r:
            print(json.dumps({"lat": r[0], "lon": r[1], "matched": r[2],
                              "miles": round(miles(r[0], r[1]), 1)}))
        else:
            print('null'); sys.exit(1)
