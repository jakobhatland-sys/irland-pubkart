"""
Lager pubs.geojson til webkartet.

- Finnes puber.json (raw OSM-eksport fra Overpass Turbo) i mappen, brukes den.
- Ellers hentes data fra Overpass API (prøver flere servere) og lagres som puber.json.

Kjør:  python lag_geojson.py
"""
import json
import os
import requests

QUERY = """
[out:json][timeout:180];
area["ISO3166-1"="IE"][admin_level=2]->.ie;
area["ISO3166-2"="GB-NIR"]->.ni;
(
  nwr["amenity"="pub"](area.ie);
  nwr["amenity"="pub"](area.ni);
);
out center tags;
"""

SERVERE = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
HEADERS = {"User-Agent": "irland-pubkart/1.0", "Accept": "application/json"}


def hent_raw():
    if os.path.exists("puber.json"):
        print("Leser puber.json")
        with open("puber.json", encoding="utf-8") as f:
            return json.load(f)
    for url in SERVERE:
        try:
            print(f"Henter fra {url} ...")
            r = requests.post(url, data={"data": QUERY}, headers=HEADERS, timeout=200)
            r.raise_for_status()
            data = r.json()
            with open("puber.json", "w", encoding="utf-8") as f:
                json.dump(data, f)
            return data
        except Exception as e:
            print(f"  feilet: {e}")
    if os.path.exists("irske_puber.csv"):
        import csv
        print("Alle servere feilet – bruker irske_puber.csv (kun navn/by/koordinater)")
        with open("irske_puber.csv", encoding="utf-8") as f:
            return {"elements": [
                {"type": r["osm_id"].split("/")[0], "id": r["osm_id"].split("/")[1],
                 "lat": float(r["lat"]), "lon": float(r["lon"]),
                 "tags": {k: v for k, v in (("name", r["navn"]), ("addr:city", r["by"])) if v}}
                for r in csv.DictReader(f)]}
    raise SystemExit("Alle Overpass-servere feilet. Prøv igjen senere, eller eksporter puber.json fra overpass-turbo.eu.")


def til_geojson(raw):
    features = []
    for el in raw["elements"]:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        t = el.get("tags", {})
        gate = " ".join(x for x in (t.get("addr:housenumber"), t.get("addr:street")) if x)
        by = (t.get("addr:city") or t.get("addr:town") or t.get("addr:village")
              or t.get("addr:suburb") or "")
        props = {
            "id": f'{el["type"]}/{el["id"]}',
            "navn": t.get("name", ""),
            "gate": gate,
            "by": by,
            "nettside": t.get("website") or t.get("contact:website") or "",
            "apningstider": t.get("opening_hours", ""),
        }
        props = {k: v for k, v in props.items() if v}  # dropp tomme felt -> mindre fil
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


if __name__ == "__main__":
    gj = til_geojson(hent_raw())
    with open("pubs.geojson", "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Skrev pubs.geojson med {len(gj['features'])} puber")