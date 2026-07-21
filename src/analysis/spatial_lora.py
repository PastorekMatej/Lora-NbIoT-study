"""Agrégation spatiale des gateways Packet Broker France → GeoJSON / stats département."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.collectors.geo_fr import in_france_metro


def gateways_to_geojson(gateways: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for g in gateways:
        loc = g.get("location") or {}
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if not in_france_metro(lat, lon):
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "id": g.get("id"),
                    "netID": g.get("netID"),
                    "tenantID": g.get("tenantID"),
                    "online": bool(g.get("online")),
                    "antennaPlacement": g.get("antennaPlacement"),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def density_grid(gateways: list[dict[str, Any]], step: float = 0.5) -> list[dict[str, Any]]:
    """Grille lat/lon simple pour densité relative."""
    cells: dict[tuple[float, float], dict[str, int]] = defaultdict(lambda: {"total": 0, "online": 0})
    for g in gateways:
        loc = g.get("location") or {}
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if not in_france_metro(lat, lon):
            continue
        key = (round(lat / step) * step, round(lon / step) * step)
        cells[key]["total"] += 1
        if g.get("online"):
            cells[key]["online"] += 1
    return [
        {"lat": k[0], "lon": k[1], "total": v["total"], "online": v["online"]}
        for k, v in sorted(cells.items(), key=lambda x: -x[1]["total"])
    ]


def run(root: Path) -> dict[str, Any]:
    raw = root / "data" / "raw" / "packetbroker_gateways_france.json"
    if not raw.exists():
        raise FileNotFoundError(f"Manquant: {raw} — lancer d'abord le collecteur Packet Broker")
    gateways = json.loads(raw.read_text(encoding="utf-8"))
    geo = gateways_to_geojson(gateways)
    dens = density_grid(gateways)
    out_geo = root / "data" / "processed" / "packetbroker_france.geojson"
    out_dens = root / "data" / "processed" / "packetbroker_france_density_grid.json"
    out_geo.write_text(json.dumps(geo), encoding="utf-8")
    summary = {
        "features": len(geo["features"]),
        "top_cells": dens[:30],
        "grid_step_deg": 0.5,
    }
    out_dens.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Carte Folium optionnelle
    try:
        import folium
        from folium.plugins import HeatMap

        m = folium.Map(location=[46.6, 2.5], zoom_start=6, tiles="CartoDB positron")
        heat = [
            [f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]]
            for f in geo["features"]
            if f["properties"].get("online")
        ]
        if heat:
            HeatMap(heat, radius=12, blur=18, max_zoom=10).add_to(m)
        map_path = root / "reports" / "figures" / "carte_gateways_lorawan_online.html"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(map_path))
        summary["map"] = str(map_path)
    except Exception as e:  # noqa: BLE001
        summary["map_error"] = str(e)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(Path(__file__).resolve().parents[2]), indent=2)[:2000])
