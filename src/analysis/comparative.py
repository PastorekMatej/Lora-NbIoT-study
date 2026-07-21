"""Analyse quantitative comparative LoRaWAN vs NB-IoT — France."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_kpi_table(
    curated: dict[str, Any],
    packetbroker: dict[str, Any] | None,
    helium: dict[str, Any] | None,
    arcep: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    orange_lora = curated.get("lora", {}).get("orange", {})
    rows.append(
        {
            "technologie": "LoRaWAN",
            "acteur": "Orange (réseau opéré)",
            "indicateur": "Antennes / gateways",
            "valeur": orange_lora.get("antennas"),
            "unite": "antennes",
            "type": "déclaratif",
            "source": "Orange Business",
        }
    )
    rows.append(
        {
            "technologie": "LoRaWAN",
            "acteur": "Orange (réseau opéré)",
            "indicateur": "Couverture population",
            "valeur": orange_lora.get("population_coverage_pct"),
            "unite": "%",
            "type": "déclaratif",
            "source": "Orange Business",
        }
    )
    rows.append(
        {
            "technologie": "LoRaWAN",
            "acteur": "Orange (réseau opéré)",
            "indicateur": "Communes couvertes",
            "valeur": orange_lora.get("communes"),
            "unite": "communes",
            "type": "déclaratif",
            "source": "Orange Business",
        }
    )

    if packetbroker:
        rows.append(
            {
                "technologie": "LoRaWAN",
                "acteur": "Communautaire (Packet Broker)",
                "indicateur": "Gateways géolocalisés FR métropole",
                "valeur": packetbroker.get("france_metro_total"),
                "unite": "gateways",
                "type": "mesuré_api",
                "source": packetbroker.get("source"),
            }
        )
        rows.append(
            {
                "technologie": "LoRaWAN",
                "acteur": "Communautaire (Packet Broker)",
                "indicateur": "Gateways online",
                "valeur": packetbroker.get("france_metro_online"),
                "unite": "gateways",
                "type": "mesuré_api",
                "source": packetbroker.get("source"),
            }
        )

    if helium:
        rows.append(
            {
                "technologie": "LoRaWAN",
                "acteur": "Helium IoT",
                "indicateur": "Hotspots estimés FR (échantillon)",
                "valeur": helium.get("france_estimated_total"),
                "unite": "hotspots",
                "type": "estimé_api",
                "source": helium.get("source"),
            }
        )

    obj = curated.get("lora", {}).get("objenious_bouygues", {})
    rows.append(
        {
            "technologie": "LoRaWAN",
            "acteur": "Objenious / Bouygues",
            "indicateur": "Statut réseau",
            "valeur": obj.get("status"),
            "unite": "",
            "type": "fait",
            "source": "Objenious (arrêt 2024)",
        }
    )

    for actor, key in [("SFR", "sfr"), ("Bouygues / Objenious", "bouygues_objenious")]:
        nb = curated.get("nbiot", {}).get(key, {})
        rows.append(
            {
                "technologie": "NB-IoT",
                "acteur": actor,
                "indicateur": "Couverture population déclarée",
                "valeur": nb.get("population_coverage_pct"),
                "unite": "%",
                "type": "déclaratif",
                "source": "Opérateur / presse IoT",
            }
        )

    orange_nb = curated.get("nbiot", {}).get("orange", {})
    rows.append(
        {
            "technologie": "NB-IoT",
            "acteur": "Orange",
            "indicateur": "Positionnement FR",
            "valeur": orange_nb.get("status"),
            "unite": "",
            "type": "qualitatif",
            "source": "Orange Business (JDN)",
        }
    )

    if arcep and arcep.get("series"):
        latest = arcep["series"][-1]
        for op, stats in (latest.get("by_operator") or {}).items():
            if op in {"Orange", "SFR", "Bouygues Telecom", "Free Mobile"}:
                rows.append(
                    {
                        "technologie": "Cellulaire (proxy NB-IoT/LTE-M)",
                        "acteur": op,
                        "indicateur": f"Sites 4G Arcep ({latest.get('quarter')})",
                        "valeur": stats.get("4g"),
                        "unite": "sites",
                        "type": "mesuré_open_data",
                        "source": "Arcep Mon Réseau Mobile",
                    }
                )

    market = curated.get("market_global_context", {})
    rows.append(
        {
            "technologie": "LPWAN mondial",
            "acteur": "IoT Analytics",
            "indicateur": "Connexions LPWAN 2023",
            "valeur": market.get("lpwan_connections_2023_bn"),
            "unite": "milliards",
            "type": "marché",
            "source": "IoT Analytics 2024",
        }
    )
    rows.append(
        {
            "technologie": "LoRa (ex-Chine)",
            "acteur": "IoT Analytics",
            "indicateur": "Part connexions LPWAN",
            "valeur": market.get("lora_share_ex_china_pct"),
            "unite": "%",
            "type": "marché",
            "source": "IoT Analytics 2024",
        }
    )
    rows.append(
        {
            "technologie": "NB-IoT (ex-Chine)",
            "acteur": "IoT Analytics",
            "indicateur": "Part connexions LPWAN",
            "valeur": market.get("nbiot_share_ex_china_pct"),
            "unite": "%",
            "type": "marché",
            "source": "IoT Analytics 2024",
        }
    )
    return rows


def arcep_4g_trend_table(arcep: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in arcep.get("series") or []:
        q = item.get("quarter")
        for op, stats in (item.get("by_operator") or {}).items():
            if op in {"Orange", "SFR", "Bouygues Telecom", "Free Mobile"}:
                out.append(
                    {
                        "quarter": q,
                        "operator": op,
                        "sites_total": stats.get("sites"),
                        "sites_4g": stats.get("4g"),
                        "sites_5g": stats.get("5g"),
                    }
                )
    return out


def compare_deployment_models(curated: dict[str, Any]) -> dict[str, Any]:
    """Synthèse structurée pour la partie qualitative/quantitative."""
    return {
        "lora_public_national_operators": 1,  # Orange seul après arrêt Objenious
        "nbiot_national_operators": 2,  # SFR + Bouygues (Orange non positionné)
        "lora_orange_antennas": curated.get("lora", {}).get("orange", {}).get("antennas"),
        "lora_orange_pop_pct": curated.get("lora", {}).get("orange", {}).get("population_coverage_pct"),
        "nbiot_sfr_pop_pct": curated.get("nbiot", {}).get("sfr", {}).get("population_coverage_pct"),
        "nbiot_bouygues_pop_pct": curated.get("nbiot", {})
        .get("bouygues_objenious", {})
        .get("population_coverage_pct"),
        "structural_shift": (
            "Depuis fin 2024, le duopole LoRaWAN opéré (Orange/Objenious) est devenu "
            "un monopole public Orange, tandis que NB-IoT/LTE-M se déploie en multi-opérateurs "
            "cellulaires (SFR, Bouygues ; Orange sur LTE-M)."
        ),
    }


def run_analysis(root: Path) -> dict[str, Any]:
    curated = load_yaml(root / "data" / "curated" / "operator_coverage_france.yaml")
    timeline = load_yaml(root / "data" / "curated" / "timeline_france.yaml")

    pb_path = root / "data" / "processed" / "packetbroker_france_summary.json"
    he_path = root / "data" / "processed" / "helium_france_estimate.json"
    ar_path = root / "data" / "processed" / "arcep_sites_4g_trend.json"

    packetbroker = load_json(pb_path) if pb_path.exists() else None
    helium = load_json(he_path) if he_path.exists() else None
    arcep = load_json(ar_path) if ar_path.exists() else None

    result = {
        "kpis": build_kpi_table(curated, packetbroker, helium, arcep),
        "arcep_4g_trend": arcep_4g_trend_table(arcep or {}),
        "deployment_models": compare_deployment_models(curated),
        "timeline_events": timeline.get("events", []),
        "qualitative_axes": timeline.get("qualitative_axes", []),
        "inputs": {
            "packetbroker": bool(packetbroker),
            "helium": bool(helium),
            "arcep": bool(arcep),
        },
    }
    out_path = root / "data" / "processed" / "comparative_analysis.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(run_analysis(root), indent=2, ensure_ascii=False)[:4000])
