"""Collecteur Helium Entity API — hotspots IoT (LoRaWAN communautaire)."""

from __future__ import annotations

import json
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests

from src.collectors.geo_fr import bbox_metadata, in_france_metro

BASE = "https://entities.nft.helium.io/v2/hotspots"
META = "https://entities.nft.helium.io/v2/hotspots/pagination-metadata"
HEADERS = {
    "User-Agent": "LoRa-NBIoT-Study/1.0 (research; comparative-deployment-france)",
    "Accept": "application/json",
}


def collect(
    raw_dir: Path,
    processed_dir: Path,
    max_pages: int = 10,
    sleep_s: float = 0.15,
) -> dict[str, Any]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    meta = requests.get(META, params={"subnetwork": "iot"}, headers=HEADERS, timeout=60).json()
    cursor = None
    fr_hotspots: list[dict[str, Any]] = []
    scanned = 0
    active_fr = 0
    pages = 0

    while pages < max_pages:
        params: dict[str, str] = {"subnetwork": "iot"}
        if cursor:
            params["cursor"] = cursor
        r = requests.get(BASE, params=params, headers=HEADERS, timeout=120)
        r.raise_for_status()
        payload = r.json()
        items = payload.get("items") or []
        pages += 1
        scanned += len(items)
        for h in items:
            if in_france_metro(h.get("lat"), h.get("long")):
                fr_hotspots.append(h)
                if h.get("is_active"):
                    active_fr += 1
        cursor = payload.get("cursor")
        if not cursor:
            break
        time.sleep(sleep_s)

    ratio = (len(fr_hotspots) / scanned) if scanned else 0.0
    entity_stock = int(ratio * meta.get("totalItems", 0))
    # Le stock Entity géolocalisé surestime fortement le « réseau » FR utile
    # (vérif. 2026-07-21 : ~11,7k Entity vs ~3,2k réseau presse/trackers).
    # KPI principal = réseau ; Entity stock séparé.
    network_est = 3200
    out = {
        "source": BASE,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "global_meta": meta,
        "sample_pages": pages,
        "sample_scanned": scanned,
        "france_in_sample": len(fr_hotspots),
        "france_active_in_sample": active_fr,
        "france_ratio_sample": ratio,
        "france_entity_stock_estimated": entity_stock,
        "france_network_estimated": network_est,
        "france_estimated_total": network_est,
        "geo_filter": bbox_metadata(),
        "note": (
            "france_estimated_total = estimation réseau FR (~3,2k, JDN+Paris scaling), "
            "pas le stock Entity géolocalisé. "
            "Coordonnées Helium obfuscées (H3 res 8) ; is_active souvent faux."
        ),
        "verification": "data/processed/helium_france_verification.json",
    }
    (raw_dir / "helium_hotspots_france_sample.json").write_text(
        json.dumps(fr_hotspots, ensure_ascii=False), encoding="utf-8"
    )
    (processed_dir / "helium_france_estimate.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(collect(root / "data" / "raw", root / "data" / "processed"), indent=2))
