"""
Henter alle puber i Irland (Republikken + Nord-Irland) fra OpenStreetMap
via Overpass API, lagrer dem som CSV og plotter dem som prikker.

Krav:  pip install requests matplotlib
"""
import csv
import requests
import matplotlib.pyplot as plt

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

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


def hent_puber():
    headers = {
        "User-Agent": "irland-pubkart/1.0 (jakobhatland@yahoo.no)",
        "Accept": "application/json",
    }
    servere = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]
    for url in servere:
        try:
            r = requests.post(url, data={"data": QUERY}, headers=headers, timeout=200)
            r.raise_for_status()
            data = r.json()
            break
        except Exception as e:
            print(f"Feilet mot {url}: {e}")
    else:
        raise SystemExit("Alle Overpass-servere feilet.")

    puber = []
    for el in data["elements"]:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {})
        puber.append({
            "osm_id": f'{el["type"]}/{el["id"]}',
            "navn": tags.get("name", ""),
            "by": tags.get("addr:city", ""),
            "lat": lat,
            "lon": lon,
        })
    return puber


def lagre_csv(puber, fil="irske_puber.csv"):
    with open(fil, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=puber[0].keys())
        w.writeheader()
        w.writerows(puber)


def plott(puber, fil="irske_puber.png"):
    lon = [p["lon"] for p in puber]
    lat = [p["lat"] for p in puber]

    fig, ax = plt.subplots(figsize=(8, 10), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")
    ax.scatter(lon, lat, s=0.8, c="#f2b632", alpha=0.7, linewidths=0)
    ax.set_aspect(1 / 0.594)  # korrigerer for breddegrad ~53,5° N
    ax.set_title(f"{len(puber)} puber i Irland", color="white", fontsize=16)
    ax.axis("off")
    ax.text(0.99, 0.01, "Data: © OpenStreetMap-bidragsytere (ODbL)",
            transform=ax.transAxes, ha="right", color="#888", fontsize=7)
    plt.savefig(fil, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.show()


if __name__ == "__main__":
    puber = hent_puber()
    print(f"Fant {len(puber)} puber")
    lagre_csv(puber)
    plott(puber)