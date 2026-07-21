"""
Pipeline d'étude comparative LoRaWAN vs NB-IoT — France.

Usage:
  python -m scripts.run_study --collect --analyze --report
  python -m scripts.run_study --analyze --report   # réutilise data/raw existantes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Étude LoRaWAN vs NB-IoT France")
    parser.add_argument("--collect", action="store_true", help="Collecter via APIs / open data")
    parser.add_argument("--skip-helium", action="store_true", help="Ne pas interroger Helium")
    parser.add_argument("--skip-packetbroker", action="store_true")
    parser.add_argument("--skip-arcep", action="store_true")
    parser.add_argument("--helium-pages", type=int, default=10)
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--spatial", action="store_true", help="GeoJSON + heatmap Folium LoRa")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    raw = ROOT / "data" / "raw"
    processed = ROOT / "data" / "processed"
    raw.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    if args.collect:
        if not args.skip_packetbroker:
            from src.collectors.packetbroker import collect as collect_pb

            print(">>> Packet Broker…")
            print(json.dumps(collect_pb(raw, processed), indent=2, ensure_ascii=False)[:800])
        if not args.skip_helium:
            from src.collectors.helium import collect as collect_he

            print(">>> Helium…")
            print(json.dumps(collect_he(raw, processed, max_pages=args.helium_pages), indent=2, ensure_ascii=False))
        if not args.skip_arcep:
            from src.collectors.arcep_sites import collect as collect_ar

            print(">>> Arcep sites…")
            print(json.dumps(collect_ar(raw, processed), indent=2, ensure_ascii=False)[:1200])

    if args.spatial:
        from src.analysis.spatial_lora import run as spatial_run

        print(">>> Spatial LoRa…")
        print(json.dumps(spatial_run(ROOT), indent=2, ensure_ascii=False)[:1000])

    if args.analyze:
        from src.analysis.comparative import run_analysis

        print(">>> Analyse…")
        result = run_analysis(ROOT)
        print(f"KPIs: {len(result['kpis'])} | timeline: {len(result['timeline_events'])}")

    if args.report:
        from src.analysis.report import generate_report

        print(">>> Rapport…")
        path = generate_report(ROOT)
        print(f"Rapport écrit: {path}")

    if not (args.collect or args.analyze or args.report or args.spatial):
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
