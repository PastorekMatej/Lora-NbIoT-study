"""Filtres géographiques France métropolitaine (+ Corse) via polygones simplifiés."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

GEOJSON_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "france_regions.geojson"


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Ray casting; ring = [[lon, lat], ...]."""
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 0.0) + xi
        ):
            inside = not inside
        j = i
    return inside


def _point_in_polygon(lon: float, lat: float, coords: list) -> bool:
    """Polygon coords: [exterior, hole1, ...]."""
    if not coords:
        return False
    if not _point_in_ring(lon, lat, coords[0]):
        return False
    for hole in coords[1:]:
        if _point_in_ring(lon, lat, hole):
            return False
    return True


def _point_in_geometry(lon: float, lat: float, geom: dict[str, Any]) -> bool:
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        return _point_in_polygon(lon, lat, coords)
    if gtype == "MultiPolygon":
        return any(_point_in_polygon(lon, lat, poly) for poly in coords)
    return False


@lru_cache(maxsize=1)
def _france_geometries() -> tuple[dict[str, Any], ...]:
    data = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    geoms = []
    for feat in data.get("features") or []:
        geom = feat.get("geometry")
        if geom:
            geoms.append(geom)
    return tuple(geoms)


def in_france_metro(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    lat_f, lon_f = float(lat), float(lon)
    # Quick reject bbox before PIP
    if not (41.3 <= lat_f <= 51.15 and -5.5 <= lon_f <= 9.7):
        return False
    return any(_point_in_geometry(lon_f, lat_f, g) for g in _france_geometries())


def bbox_metadata() -> dict:
    return {
        "method": "point_in_polygon",
        "geojson": str(GEOJSON_PATH.name),
        "regions": 13,
        "includes_corsica": True,
    }
