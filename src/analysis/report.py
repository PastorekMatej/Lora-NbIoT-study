"""Génération de graphiques et rapport Markdown."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_coverage_declared(analysis: dict[str, Any], out: Path) -> Path | None:
    rows = [
        r
        for r in analysis["kpis"]
        if r.get("indicateur") == "Couverture population" or r.get("indicateur") == "Couverture population déclarée"
    ]
    if not rows:
        return None
    labels = [f"{r['technologie']}\n{r['acteur']}" for r in rows if isinstance(r.get("valeur"), (int, float))]
    values = [r["valeur"] for r in rows if isinstance(r.get("valeur"), (int, float))]
    if not values:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["#1f6f5b" if "LoRa" in l else "#0b3d91" for l in labels]
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("% population (déclaratif)")
    ax.set_title("Couverture population déclarée — LoRaWAN vs NB-IoT (France)")
    ax.set_ylim(0, 105)
    ax.axhline(95, color="#888", ls="--", lw=0.8, label="réf. 95%")
    ax.legend(loc="lower right")
    path = out / "couverture_population_declaree.png"
    _save(fig, path)
    return path


def plot_infrastructure_counts(analysis: dict[str, Any], out: Path) -> Path | None:
    want = {
        ("LoRaWAN", "Orange (réseau opéré)", "Antennes / gateways"),
        ("LoRaWAN", "Communautaire (Packet Broker)", "Gateways géolocalisés FR métropole"),
        ("LoRaWAN", "Communautaire (Packet Broker)", "Gateways online"),
        ("LoRaWAN", "Helium IoT", "Hotspots estimés FR (échantillon)"),
    }
    rows = [r for r in analysis["kpis"] if (r["technologie"], r["acteur"], r["indicateur"]) in want]
    rows = [r for r in rows if isinstance(r.get("valeur"), (int, float))]
    if not rows:
        return None
    labels = [r["indicateur"][:42] for r in rows]
    values = [r["valeur"] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.barh(labels, values, color="#1f6f5b")
    ax.set_xlabel("Nombre")
    ax.set_title("Infrastructure LoRaWAN mesurée / déclarée — France")
    for i, v in enumerate(values):
        ax.text(v, i, f" {int(v):,}".replace(",", " "), va="center", fontsize=8)
    path = out / "infra_lorawan.png"
    _save(fig, path)
    return path


def plot_arcep_4g_trend(analysis: dict[str, Any], out: Path) -> Path | None:
    rows = analysis.get("arcep_4g_trend") or []
    if not rows:
        return None
    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for op, g in df.groupby("operator"):
        g = g.sort_values("quarter")
        ax.plot(g["quarter"], g["sites_4g"], marker="o", label=op)
    ax.set_title("Sites 4G Arcep (proxy densification cellulaire / NB-IoT in-band)")
    ax.set_ylabel("Sites 4G")
    ax.legend()
    ax.grid(True, alpha=0.3)
    path = out / "arcep_sites_4g_trend.png"
    _save(fig, path)
    return path


def plot_timeline(analysis: dict[str, Any], out: Path) -> Path | None:
    events = analysis.get("timeline_events") or []
    if not events:
        return None
    # Simple categorical timeline by year-ish
    buckets: dict[str, list[str]] = defaultdict(list)
    for e in events:
        year = str(e.get("date", ""))[:4]
        buckets[year].append(f"{e.get('actor')}: {e.get('event')[:60]}")
    years = sorted(buckets.keys())
    fig, ax = plt.subplots(figsize=(11, max(3.5, 0.55 * sum(len(v) for v in buckets.values()))))
    y = 0
    yticks, ylabels = [], []
    colors = {"LoRaWAN": "#1f6f5b", "NB-IoT": "#0b3d91", "LTE-M": "#0b3d91"}
    for year in years:
        for text in buckets[year]:
            tech = "LoRaWAN" if "LoRa" in text else ("NB-IoT" if "NB" in text or "LTE" in text else "autre")
            ax.barh(y, 1, left=years.index(year), color=colors.get(tech, "#666"), alpha=0.85)
            yticks.append(y)
            ylabels.append(f"{year} — {text}")
            y += 1
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=7)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years)
    ax.set_title("Chronologie qualitative — déploiement LPWAN France")
    ax.set_xlabel("Année (bucket)")
    path = out / "timeline_evenements.png"
    _save(fig, path)
    return path


def render_markdown(analysis: dict[str, Any], figures: list[Path], out_md: Path) -> Path:
    dm = analysis.get("deployment_models") or {}
    lines = [
        "# Étude comparative — déploiement LoRaWAN vs NB-IoT en France",
        "",
        "> Analyse quantitative et qualitative basée sur données open (APIs) et sources opérateurs / GSMA / IoT Analytics.",
        f"> Généré automatiquement — inputs: `{json.dumps(analysis.get('inputs'))}`.",
        "",
        "## Verdict synthétique",
        "",
        dm.get("structural_shift", ""),
        "",
        f"- **LoRaWAN public national** : 1 opérateur (Orange), ~{dm.get('lora_orange_antennas')} antennes, ~{dm.get('lora_orange_pop_pct')} % population.",
        f"- **NB-IoT national** : 2 opérateurs (SFR ~{dm.get('nbiot_sfr_pop_pct')} %, Bouygues ~{dm.get('nbiot_bouygues_pop_pct')} %) ; Orange non positionné en France (LTE-M + LoRaWAN).",
        "",
        "## Indicateurs clés (KPI)",
        "",
        "| Technologie | Acteur | Indicateur | Valeur | Unité | Type | Source |",
        "|---|---|---|---:|---|---|---|",
    ]
    for r in analysis.get("kpis") or []:
        val = r.get("valeur")
        if isinstance(val, float):
            val_s = f"{val:.4g}"
        elif val is None:
            val_s = "—"
        else:
            val_s = str(val)
        lines.append(
            f"| {r.get('technologie')} | {r.get('acteur')} | {r.get('indicateur')} | {val_s} | {r.get('unite','')} | {r.get('type')} | {r.get('source')} |"
        )

    lines += ["", "## Graphiques", ""]
    for fig in figures:
        rel = fig.as_posix()
        lines.append(f"![{fig.stem}]({rel})")
        lines.append("")

    lines += ["", "## Axes qualitatifs", ""]
    for ax_item in analysis.get("qualitative_axes") or []:
        lines.append(f"### {ax_item.get('title')}")
        lines.append(f"- **LoRaWAN** : {ax_item.get('lora')}")
        lines.append(f"- **NB-IoT** : {ax_item.get('nbiot')}")
        lines.append("")

    lines += [
        "## Chronologie",
        "",
        "| Date | Techno | Acteur | Événement | Type |",
        "|---|---|---|---|---|",
    ]
    for e in analysis.get("timeline_events") or []:
        lines.append(
            f"| {e.get('date')} | {e.get('technology')} | {e.get('actor')} | {e.get('event')} | {e.get('type')} |"
        )

    lines += [
        "",
        "## Limites méthodologiques",
        "",
        "- L'Arcep ne publie pas (encore) de couches open data NB-IoT / LTE-M / LoRaWAN.",
        "- Les % population opérateurs sont déclaratifs ; les mesures Packet Broker / Helium / Arcep 4G sont objectives mais partielles.",
        "- Packet Broker ne capture pas le réseau LoRaWAN privé Orange (~4800 antennes).",
        "- Helium : estimation par échantillonnage ; coordonnées obfuscées ; statut `is_active` peu fiable hors contexte epoch.",
        "- Orange NB-IoT : divergences possibles entre listing GSMA et déclaration Orange Business — documentées dans `data/curated/`.",
        "",
        "## Reproductibilité",
        "",
        "```bash",
        "pip install -r requirements.txt",
        "python -m scripts.run_study --collect --analyze --report",
        "```",
        "",
    ]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md


def generate_report(root: Path) -> Path:
    analysis_path = root / "data" / "processed" / "comparative_analysis.json"
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    fig_dir = root / "reports" / "figures"
    figures = []
    for fn in (plot_coverage_declared, plot_infrastructure_counts, plot_arcep_4g_trend, plot_timeline):
        p = fn(analysis, fig_dir)
        if p:
            figures.append(p)
    # Chemins relatifs depuis reports/*.md vers reports/figures/*
    rel_figs = [Path("figures") / f.name for f in figures]
    return render_markdown(analysis, rel_figs, root / "reports" / "etude_comparative_lora_nbiot_france.md")


if __name__ == "__main__":
    print(generate_report(Path(__file__).resolve().parents[2]))
