"""Collecteur Arcep — sites mobiles métropole (proxy densification cellulaire / NB-IoT)."""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

BASE = "https://data.arcep.fr/mobile/sites"
DEFAULT_QUARTERS = ["2023_T1", "2024_T1", "2025_T1", "2026_T1"]


def download_quarter(quarter: str, dest: Path) -> Path | None:
    url = f"{BASE}/{quarter}/{quarter}_sites_Metropole.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=120)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def analyze_csv(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delim = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(fh, delimiter=delim)
        rows = list(reader)

    by_op: dict[str, dict[str, int]] = defaultdict(lambda: {"sites": 0, "4g": 0, "5g": 0, "3g": 0, "2g": 0})
    for row in rows:
        op = row.get("nom_op") or row.get("code_op") or "unknown"
        by_op[op]["sites"] += 1
        for tech, key in [("site_4g", "4g"), ("site_5g", "5g"), ("site_3g", "3g"), ("site_2g", "2g")]:
            val = (row.get(tech) or "0").strip()
            if val in {"1", "true", "True", "oui", "Oui"}:
                by_op[op][key] += 1

    # NB-IoT operators of interest in France
    nbiot_ops = {"Orange", "SFR", "Bouygues Telecom", "Free Mobile"}
    return {
        "file": path.name,
        "total_rows": len(rows),
        "by_operator": dict(by_op),
        "sites_4g_nbiot_relevant": {
            op: by_op[op]["4g"] for op in by_op if op in nbiot_ops or "Bouygues" in op
        },
        "note": (
            "Les sites 4G Arcep ne distinguent pas NB-IoT/LTE-M. "
            "Ils mesurent la densification RAN cellulaire sous-jacente."
        ),
    }


def collect(
    raw_dir: Path,
    processed_dir: Path,
    quarters: list[str] | None = None,
) -> dict[str, Any]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    quarters = quarters or DEFAULT_QUARTERS
    series = []
    for q in quarters:
        path = raw_dir / f"arcep_sites_{q}_Metropole.csv"
        if not path.exists():
            downloaded = download_quarter(q, path)
            if downloaded is None:
                continue
        series.append({"quarter": q, **analyze_csv(path)})

    out = {
        "source": BASE,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "series": series,
    }
    (processed_dir / "arcep_sites_4g_trend.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(collect(root / "data" / "raw", root / "data" / "processed"), indent=2, ensure_ascii=False))
