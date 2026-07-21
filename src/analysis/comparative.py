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
    rows.append(
        {
            "technologie": "LoRaWAN",
            "acteur": "Orange (réseau opéré)",
            "indicateur": "Croissance objets connectés",
            "valeur": orange_lora.get("objects_growth"),
            "unite": "",
            "type": "tendance",
            "source": "Orange Business (JDN)",
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
                "indicateur": "Hotspots réseau FR (estim. vérifiée)",
                "valeur": helium.get("france_network_estimated")
                or helium.get("france_estimated_total"),
                "unite": "hotspots",
                "type": "estimé_vérifié",
                "source": helium.get("verification") or helium.get("source"),
            }
        )
        if helium.get("france_entity_stock_estimated"):
            rows.append(
                {
                    "technologie": "LoRaWAN",
                    "acteur": "Helium IoT",
                    "indicateur": "Stock Entity géolocalisé FR (≠ actifs)",
                    "valeur": helium.get("france_entity_stock_estimated"),
                    "unite": "hotspots",
                    "type": "estimé_api_stock",
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

    for actor, key in [
        ("Orange", "orange"),
        ("SFR", "sfr"),
        ("Bouygues / Objenious", "bouygues_objenious"),
    ]:
        nb = curated.get("nbiot", {}).get(key, {})
        rows.append(
            {
                "technologie": "NB-IoT",
                "acteur": actor,
                "indicateur": "Couverture population déclarée",
                "valeur": nb.get("population_coverage_pct"),
                "unite": "%",
                "type": "déclaratif",
                "source": "GSMA / opérateurs / agrégats",
            }
        )
        rows.append(
            {
                "technologie": "NB-IoT",
                "acteur": actor,
                "indicateur": "Positionnement FR",
                "valeur": nb.get("status", "positioned_fr"),
                "unite": "",
                "type": "qualitatif",
                "source": "GSMA / Live Objects / opérateurs",
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


def build_growth_metrics(ts: dict[str, Any]) -> dict[str, Any]:
    """Indicateurs de croissance / décroissance antennes et utilisateurs."""
    lora_sum = ts.get("antennas_lora_trend_summary") or {}
    sites = ts.get("sites_4g_proxy_nbiot") or {}
    users = ts.get("users_connections") or {}
    return {
        "lora_public_antennas": {
            "peak": lora_sum.get("peak_public_antennas"),
            "peak_year": lora_sum.get("peak_public_year"),
            "after_objenious_shutdown": lora_sum.get("post_objenious_antennas"),
            "delta_pct": lora_sum.get("delta_public_pct"),
            "direction": "décroissance",
            "interpretation": (lora_sum.get("interpretation") or "").strip(),
        },
        "nbiot_proxy_4g_sites": {
            "growth_2023_2026_pct": sites.get("growth_2023_to_2026_pct"),
            "direction": "croissance",
            "interpretation": (sites.get("interpretation") or "").strip(),
        },
        "users": {
            "lora_trend": (users.get("trend_summary") or {}).get("lora_users"),
            "nbiot_trend": (users.get("trend_summary") or {}).get("nbiot_users"),
            "net_france": (users.get("trend_summary") or {}).get("net_france"),
        },
        "lora_antenna_series": ts.get("antennas_lora_public", {}).get("series", []),
        "users_series": users.get("series", []),
    }


def compare_deployment_models(curated: dict[str, Any], growth: dict[str, Any]) -> dict[str, Any]:
    return {
        "lora_public_national_operators": 1,
        "nbiot_national_operators": 3,  # Orange, SFR, Bouygues
        "lora_orange_antennas": curated.get("lora", {}).get("orange", {}).get("antennas"),
        "lora_orange_pop_pct": curated.get("lora", {}).get("orange", {}).get("population_coverage_pct"),
        "nbiot_orange_pop_pct": curated.get("nbiot", {}).get("orange", {}).get("population_coverage_pct"),
        "nbiot_sfr_pop_pct": curated.get("nbiot", {}).get("sfr", {}).get("population_coverage_pct"),
        "nbiot_bouygues_pop_pct": curated.get("nbiot", {})
        .get("bouygues_objenious", {})
        .get("population_coverage_pct"),
        "structural_shift": (
            "Depuis fin 2024 : parc d'antennes LoRaWAN public en DÉCROISSANCE nette "
            f"({growth['lora_public_antennas'].get('delta_pct')}% vs pic) après arrêt Objenious ; "
            "Orange reste le seul opérateur LoRaWAN national mais est aussi positionné NB-IoT "
            "(avec SFR et Bouygues). Les sites 4G (proxy NB-IoT) et les utilisateurs cellulaires "
            "LPWA sont en CROISSANCE ; les objets LoRaWAN Orange croissent encore (double digit YoY) "
            "malgré la contraction du réseau public concurrent."
        ),
        "growth_highlights": growth,
    }


def run_analysis(root: Path) -> dict[str, Any]:
    curated = load_yaml(root / "data" / "curated" / "operator_coverage_france.yaml")
    timeline = load_yaml(root / "data" / "curated" / "timeline_france.yaml")
    timeseries = load_yaml(root / "data" / "curated" / "deployment_timeseries.yaml")

    pb_path = root / "data" / "processed" / "packetbroker_france_summary.json"
    he_path = root / "data" / "processed" / "helium_france_estimate.json"
    ar_path = root / "data" / "processed" / "arcep_sites_4g_trend.json"

    packetbroker = load_json(pb_path) if pb_path.exists() else None
    helium = load_json(he_path) if he_path.exists() else None
    arcep = load_json(ar_path) if ar_path.exists() else None

    growth = build_growth_metrics(timeseries)

    result = {
        "kpis": build_kpi_table(curated, packetbroker, helium, arcep),
        "arcep_4g_trend": arcep_4g_trend_table(arcep or {}),
        "growth_metrics": growth,
        "deployment_models": compare_deployment_models(curated, growth),
        "timeline_events": timeline.get("events", []),
        "qualitative_axes": timeline.get("qualitative_axes", []),
        "inputs": {
            "packetbroker": bool(packetbroker),
            "helium": bool(helium),
            "arcep": bool(arcep),
            "timeseries": True,
        },
    }
    out_path = root / "data" / "processed" / "comparative_analysis.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(run_analysis(root), indent=2, ensure_ascii=False)[:5000])
