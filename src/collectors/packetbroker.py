"""Collecteur Packet Broker Mapper — gateways LoRaWAN fédérés (TTN/TTS...)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from src.collectors.geo_fr import bbox_metadata, in_france_metro

API_URL = "https://mapper.packetbroker.net/api/v2/gateways"


def fetch_gateways(timeout: int = 180) -> list[dict[str, Any]]:
    r = requests.get(API_URL, timeout=timeout, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def filter_france(gateways: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for g in gateways:
        loc = g.get("location") or {}
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if in_france_metro(lat, lon):
            out.append(g)
    return out


def summarize(gateways: list[dict[str, Any]], global_total: int | None = None) -> dict[str, Any]:
    from collections import Counter

    online = sum(1 for g in gateways if g.get("online"))
    tenants = Counter((g.get("netID"), g.get("tenantID")) for g in gateways)
    return {
        "source": API_URL,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "global_total": global_total,
        "france_metro_total": len(gateways),
        "france_metro_online": online,
        "online_ratio": round(online / len(gateways), 4) if gateways else 0,
        "geo_filter": bbox_metadata(),
        "top_networks": [
            {"netID": k[0], "tenantID": k[1], "count": v} for k, v in tenants.most_common(25)
        ],
    }


def collect(raw_dir: Path, processed_dir: Path) -> dict[str, Any]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    all_gw = fetch_gateways()
    fr = filter_france(all_gw)
    (raw_dir / "packetbroker_gateways_france.json").write_text(
        json.dumps(fr, ensure_ascii=False), encoding="utf-8"
    )
    summary = summarize(fr, global_total=len(all_gw))
    (processed_dir / "packetbroker_france_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    s = collect(root / "data" / "raw", root / "data" / "processed")
    print(json.dumps(s, indent=2, ensure_ascii=False))
