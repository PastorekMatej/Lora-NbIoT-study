"""Analyse et graphiques — antennes LoRaWAN vs capacité radio NB-IoT depuis 2015."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_lora_antennas(data: dict[str, Any], out: Path) -> Path:
    series = data["lora_antennas_france"]["series"]
    years = [r["year"] for r in series]
    orange = [r.get("orange") for r in series]
    obj = [r.get("objenious") for r in series]
    total = [r.get("total_public") for r in series]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(years, orange, "o-", color="#1f6f5b", lw=2, label="Orange (dédiées)")
    ax.plot(years, obj, "s-", color="#c45c26", lw=2, label="Objenious (dédiées)")
    ax.plot(years, total, "D--", color="#222", lw=2, label="Total public LoRaWAN")
    ax.axvline(2024.85, color="#a00", ls=":", lw=1.4)
    ax.text(2025.0, 5500, "Arrêt\nObjenious\n−47%", color="#a00", fontsize=9)
    ax.set_title("France — Antennes LoRaWAN dédiées depuis 2015")
    ax.set_xlabel("Année")
    ax.set_ylabel("Gateways / antennes")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    path = out / "antennes_lora_depuis_2015.png"
    _save(fig, path)
    return path


def plot_nbiot_capacity(data: dict[str, Any], out: Path) -> Path:
    series = data["nbiot_radio_sites_france"]["series"]
    years = [r["year"] for r in series]
    # Prefer with Orange when available, else active_nbiot_capacity
    cap = []
    for r in series:
        if r.get("active_nbiot_capacity_with_orange") is not None:
            cap.append(r["active_nbiot_capacity_with_orange"])
        else:
            cap.append(r.get("active_nbiot_capacity") or 0)
    sfr = [r.get("sfr") or 0 for r in series]
    byg = [r.get("bouygues") or 0 for r in series]
    ora = [r.get("orange") or 0 for r in series]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.stackplot(
        years,
        sfr,
        byg,
        ora,
        labels=["SFR 4G (NB-IoT)", "Bouygues 4G (NB-IoT)", "Orange 4G (NB-IoT)"],
        colors=["#8b0000", "#0b3d91", "#ff7900"],
        alpha=0.85,
    )
    ax.plot(years, cap, "k--", lw=1.5, label="Capacité totale (proxy)")
    ax.axvline(2019, color="#333", ls=":", lw=1)
    ax.text(2019.1, max(cap) * 0.55, "SFR\nlance\nNB-IoT", fontsize=8)
    ax.axvline(2022, color="#333", ls=":", lw=1)
    ax.text(2022.1, max(cap) * 0.35, "Bouygues\nnational\n>99%", fontsize=8)
    ax.set_title("France — Capacité radio NB-IoT (proxy sites 4G in-band) depuis 2015")
    ax.set_xlabel("Année")
    ax.set_ylabel("Sites 4G (proxy, pas d'antennes dédiées)")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    path = out / "antennes_nbiot_proxy_depuis_2015.png"
    _save(fig, path)
    return path


def plot_dual_comparison(data: dict[str, Any], out: Path) -> Path:
    lora = {r["year"]: r.get("total_public") for r in data["lora_antennas_france"]["series"]}
    nbiot = {}
    for r in data["nbiot_radio_sites_france"]["series"]:
        y = r["year"]
        nbiot[y] = r.get("active_nbiot_capacity_with_orange")
        if nbiot[y] is None:
            nbiot[y] = r.get("active_nbiot_capacity") or 0

    years = sorted(set(lora) | set(nbiot))
    l_vals = [lora.get(y) for y in years]
    n_vals = [nbiot.get(y) or 0 for y in years]

    fig, ax1 = plt.subplots(figsize=(11, 5.4))
    ax2 = ax1.twinx()
    (l1,) = ax1.plot(years, l_vals, "o-", color="#1f6f5b", lw=2.5, label="LoRaWAN antennes dédiées (axe G)")
    (l2,) = ax2.plot(years, n_vals, "s-", color="#0b3d91", lw=2.5, label="NB-IoT proxy sites 4G (axe D)")
    ax1.set_ylabel("Antennes LoRaWAN dédiées", color="#1f6f5b")
    ax2.set_ylabel("Sites 4G proxy NB-IoT", color="#0b3d91")
    ax1.set_xlabel("Année")
    ax1.set_title("France 2015–2026 — Antennes LoRaWAN vs capacité NB-IoT (échelles distinctes)")
    ax1.set_xticks(years)
    ax1.grid(True, alpha=0.25)
    ax1.legend(handles=[l1, l2], loc="upper left")
    ax1.annotate(
        "LoRa en avance\npuis plateau / chute",
        xy=(2019, 9100),
        xytext=(2016.2, 7000),
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color="#1f6f5b"),
    )
    ax2.annotate(
        "NB-IoT démarre\npuis densifie",
        xy=(2022, 78000),
        xytext=(2020.2, 35000),
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color="#0b3d91"),
    )
    path = out / "comparaison_antennes_lora_vs_nbiot_2015.png"
    _save(fig, path)
    return path


def plot_phases(out: Path) -> Path:
    """Schéma des phases de déploiement."""
    fig, ax = plt.subplots(figsize=(11, 3.8))
    phases = [
        (2015, 2016.8, "LoRa\nlancement", "#1f6f5b"),
        (2016.8, 2019.2, "LoRa\ncroissance", "#2a9d7a"),
        (2019.2, 2024.7, "LoRa\nplateau ~9100", "#6bb89a"),
        (2024.7, 2026.5, "LoRa\nchute −47%", "#a04040"),
    ]
    for x0, x1, label, color in phases:
        ax.barh(1, x1 - x0, left=x0, height=0.55, color=color, alpha=0.9)
        ax.text((x0 + x1) / 2, 1, label, ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    phases_nb = [
        (2015, 2019, "NB-IoT\n0 commercial FR", "#8899aa"),
        (2019, 2022, "NB-IoT\nSFR puis montée", "#3d6bb3"),
        (2022, 2026.5, "NB-IoT\nnational + densif. ↑", "#0b3d91"),
    ]
    for x0, x1, label, color in phases_nb:
        ax.barh(0, x1 - x0, left=x0, height=0.55, color=color, alpha=0.9)
        ax.text((x0 + x1) / 2, 0, label, ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["NB-IoT\n(proxy 4G)", "LoRaWAN\n(antennes dédiées)"])
    ax.set_xlim(2014.8, 2026.7)
    ax.set_xlabel("Année")
    ax.set_title("Phases de déploiement antennes / capacité radio — France 2015–2026")
    ax.axvline(2019, color="#333", ls=":", lw=0.8)
    ax.axvline(2022, color="#333", ls=":", lw=0.8)
    ax.axvline(2024.9, color="#a00", ls=":", lw=0.8)
    path = out / "phases_deploiement_antennes_2015.png"
    _save(fig, path)
    return path


def build_table(data: dict[str, Any]) -> list[dict[str, Any]]:
    lora = {r["year"]: r for r in data["lora_antennas_france"]["series"]}
    nbiot = {r["year"]: r for r in data["nbiot_radio_sites_france"]["series"]}
    rows = []
    for y in range(2015, 2027):
        lr, nr = lora.get(y, {}), nbiot.get(y, {})
        nb_cap = nr.get("active_nbiot_capacity_with_orange")
        if nb_cap is None:
            nb_cap = nr.get("active_nbiot_capacity")
        rows.append(
            {
                "year": y,
                "lora_orange": lr.get("orange"),
                "lora_objenious": lr.get("objenious"),
                "lora_total_public": lr.get("total_public"),
                "nbiot_proxy_sites": nb_cap,
                "nbiot_sfr": nr.get("sfr"),
                "nbiot_bouygues": nr.get("bouygues"),
                "nbiot_orange": nr.get("orange"),
            }
        )
    return rows


def run(root: Path) -> dict[str, Any]:
    data = load_yaml(root / "data" / "curated" / "antennas_since_2015.yaml")
    fig_dir = root / "reports" / "figures"
    art_dir = Path("/opt/cursor/artifacts/figures")
    art_dir.mkdir(parents=True, exist_ok=True)

    figs = [
        plot_phases(fig_dir),
        plot_lora_antennas(data, fig_dir),
        plot_nbiot_capacity(data, fig_dir),
        plot_dual_comparison(data, fig_dir),
    ]
    for f in figs:
        dest = art_dir / f.name
        dest.write_bytes(f.read_bytes())

    table = build_table(data)
    out = {
        "table": table,
        "trends": data.get("trends_summary"),
        "world": data.get("world_context"),
        "figures": [f.name for f in figs],
        "method": data.get("meta", {}).get("method_note"),
    }
    (root / "data" / "processed" / "antennas_since_2015_analysis.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Markdown summary
    lines = [
        "# Antennes LoRaWAN vs capacité NB-IoT — France depuis 2015",
        "",
        data["meta"]["method_note"].strip(),
        "",
        "## Tableau annuel",
        "",
        "| Année | Orange LoRa | Objenious LoRa | Total LoRa public | Proxy NB-IoT (sites 4G) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in table:
        def fmt(v):
            return "—" if v is None else f"{int(v):,}".replace(",", " ")

        lines.append(
            f"| {r['year']} | {fmt(r['lora_orange'])} | {fmt(r['lora_objenious'])} | "
            f"{fmt(r['lora_total_public'])} | {fmt(r['nbiot_proxy_sites'])} |"
        )
    lines += [
        "",
        "## Tendances",
        "",
        "### LoRaWAN (antennes dédiées)",
        f"- 2015–2019 : {data['trends_summary']['lora']['phase_2015_2019']}",
        f"- 2019–2024 : {data['trends_summary']['lora']['phase_2019_2024']}",
        f"- 2025–2026 : {data['trends_summary']['lora']['phase_2025_2026']}",
        "",
        "### NB-IoT (proxy sites 4G)",
        f"- 2015–2018 : {data['trends_summary']['nbiot']['phase_2015_2018']}",
        f"- 2019–2021 : {data['trends_summary']['nbiot']['phase_2019_2021']}",
        f"- 2022–2026 : {data['trends_summary']['nbiot']['phase_2022_2026']}",
        "",
        "## Graphiques",
        "",
    ]
    for name in out["figures"]:
        lines.append(f"![{name}](figures/{name})")
        lines.append("")
    md = root / "reports" / "analyse_antennes_depuis_2015.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    out["report"] = str(md)
    return out


if __name__ == "__main__":
    result = run(Path(__file__).resolve().parents[2])
    print(json.dumps({k: result[k] for k in ("figures", "trends", "report")}, indent=2, ensure_ascii=False))
