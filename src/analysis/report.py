"""Génération de graphiques et rapport Markdown — focus croissance / décroissance."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_coverage_declared(analysis: dict[str, Any], out: Path) -> Path | None:
    rows = [
        r
        for r in analysis["kpis"]
        if r.get("indicateur") in {"Couverture population", "Couverture population déclarée"}
        and isinstance(r.get("valeur"), (int, float))
    ]
    if not rows:
        return None
    labels = [f"{r['technologie']}\n{r['acteur']}" for r in rows]
    values = [r["valeur"] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4.8))
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


def plot_lora_antennas_trend(analysis: dict[str, Any], out: Path) -> Path | None:
    series = (analysis.get("growth_metrics") or {}).get("lora_antenna_series") or []
    years, orange, obj, total = [], [], [], []
    for row in series:
        y = row.get("year")
        if y is None:
            continue
        years.append(y)
        orange.append(row.get("orange"))
        obj.append(row.get("objenious"))
        total.append(row.get("total_public_estime"))
    if not years:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(years, orange, "o-", color="#1f6f5b", label="Orange LoRaWAN", linewidth=2)
    ax.plot(years, obj, "s-", color="#c45c26", label="Objenious LoRaWAN", linewidth=2)
    ax.plot(years, total, "D--", color="#222", label="Total public estimé", linewidth=2)
    ax.axvline(2024.9, color="#a00", ls=":", lw=1.5)
    ax.text(2025.05, max(v for v in total if v) * 0.55, "Arrêt\nObjenious\n(-47%)", color="#a00", fontsize=9)
    ax.set_title("Tendance antennes LoRaWAN publiques — France (CROISSANCE puis DÉCROISSANCE)")
    ax.set_ylabel("Antennes / gateways")
    ax.set_xlabel("Année")
    ax.grid(True, alpha=0.3)
    ax.legend()
    path = out / "tendance_antennes_lorawan.png"
    _save(fig, path)
    return path


def plot_nbiot_proxy_growth(analysis: dict[str, Any], out: Path) -> Path | None:
    rows = analysis.get("arcep_4g_trend") or []
    if not rows:
        return None
    df = pd.DataFrame(rows)
    # Only NB-IoT operators
    df = df[df["operator"].isin(["Orange", "SFR", "Bouygues Telecom"])]
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for op, g in df.groupby("operator"):
        g = g.sort_values("quarter")
        ax.plot(g["quarter"], g["sites_4g"], marker="o", label=op, linewidth=2)
    ax.set_title("Tendance sites 4G (proxy densification NB-IoT in-band) — CROISSANCE")
    ax.set_ylabel("Sites 4G Arcep")
    ax.legend()
    ax.grid(True, alpha=0.3)
    # annotate growth
    growth = ((analysis.get("growth_metrics") or {}).get("nbiot_proxy_4g_sites") or {}).get(
        "growth_2023_2026_pct"
    ) or {}
    if growth:
        txt = "Δ 2023→2026 : " + ", ".join(f"{k} +{v}%" for k, v in growth.items() if k != "free")
        ax.text(0.02, 0.98, txt, transform=ax.transAxes, va="top", fontsize=8, color="#0b3d91")
    path = out / "tendance_sites_4g_proxy_nbiot.png"
    _save(fig, path)
    return path


def plot_users_trend(analysis: dict[str, Any], out: Path) -> Path | None:
    series = (analysis.get("growth_metrics") or {}).get("users_series") or []
    years_o, vals_o, years_b, vals_b = [], [], [], []
    for row in series:
        y = row.get("year")
        if row.get("objenious_lora_objects") is not None:
            years_o.append(y)
            vals_o.append(row["objenious_lora_objects"])
        if row.get("birdz_lora_meters_fr") is not None:
            years_b.append(y)
            vals_b.append(row["birdz_lora_meters_fr"])
        if row.get("birdz_sensors_connected") is not None:
            years_b.append(y)
            vals_b.append(row["birdz_sensors_connected"])
    if not years_o and not years_b:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    if years_o:
        ax.plot(years_o, vals_o, "s-", color="#c45c26", label="Objenious objets LoRaWAN", linewidth=2)
    if years_b:
        ax.plot(years_b, vals_b, "o-", color="#1f6f5b", label="Birdz / Veolia (LoRaWAN Orange)", linewidth=2)
    ax.set_yscale("log")
    ax.set_title("Tendance utilisateurs / objets LoRaWAN — France")
    ax.set_ylabel("Objets (échelle log)")
    ax.set_xlabel("Année")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend()
    ax.text(
        0.98,
        0.05,
        "Objenious → 0 en 2025 (migration)\nOrange/Birdz → croissance (millions)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#333",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
    )
    path = out / "tendance_utilisateurs_lorawan.png"
    _save(fig, path)
    return path


def plot_growth_vs_decline_summary(analysis: dict[str, Any], out: Path) -> Path | None:
    """Barres comparatives directionnelles."""
    gm = analysis.get("growth_metrics") or {}
    lora_delta = (gm.get("lora_public_antennas") or {}).get("delta_pct")
    nbiot_growth = (gm.get("nbiot_proxy_4g_sites") or {}).get("growth_2023_2026_pct") or {}
    # average of Orange/SFR/Bouygues
    vals = [nbiot_growth.get("orange"), nbiot_growth.get("sfr"), nbiot_growth.get("bouygues")]
    vals = [v for v in vals if isinstance(v, (int, float))]
    nbiot_avg = sum(vals) / len(vals) if vals else None
    if lora_delta is None and nbiot_avg is None:
        return None
    labels = ["Antennes LoRaWAN\npublic (pic→2025)", "Sites 4G proxy NB-IoT\n(moy. opérateurs, 2023→2026)"]
    values = [lora_delta or 0, nbiot_avg or 0]
    colors = ["#a02020" if values[0] < 0 else "#1f6f5b", "#0b3d91" if values[1] > 0 else "#a02020"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, values, color=colors, width=0.55)
    ax.axhline(0, color="#333", lw=1)
    ax.set_ylabel("Variation (%)")
    ax.set_title("Croissance vs décroissance — déploiement France")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + (1 if v >= 0 else -3), f"{v:+.1f}%", ha="center", fontsize=11)
    path = out / "croissance_vs_decroissance.png"
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
    ax.set_title("Infrastructure LoRaWAN mesurée / déclarée — France (snapshot)")
    for i, v in enumerate(values):
        ax.text(v, i, f" {int(v):,}".replace(",", " "), va="center", fontsize=8)
    path = out / "infra_lorawan.png"
    _save(fig, path)
    return path


def plot_timeline(analysis: dict[str, Any], out: Path) -> Path | None:
    events = analysis.get("timeline_events") or []
    if not events:
        return None
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
    gm = analysis.get("growth_metrics") or {}
    lora_a = gm.get("lora_public_antennas") or {}
    nbiot_s = gm.get("nbiot_proxy_4g_sites") or {}
    users = gm.get("users") or {}

    lines = [
        "# Étude comparative — déploiement LoRaWAN vs NB-IoT en France",
        "",
        "> Analyse quantitative et qualitative basée sur données open (APIs) et sources opérateurs / GSMA / IoT Analytics.",
        f"> Généré automatiquement — inputs: `{json.dumps(analysis.get('inputs'))}`.",
        "",
        "## Verdict — croissance vs décroissance",
        "",
        dm.get("structural_shift", ""),
        "",
        "### Antennes / infrastructure",
        "",
        f"- **LoRaWAN public** : {lora_a.get('direction', '').upper()} — pic ~{lora_a.get('peak')} antennes ({lora_a.get('peak_year')}) → ~{lora_a.get('after_objenious_shutdown')} après arrêt Objenious (**{lora_a.get('delta_pct')}%**).",
        f"- **NB-IoT (proxy sites 4G)** : CROISSANCE — Orange **+{((nbiot_s.get('growth_2023_2026_pct') or {}).get('orange'))}%**, SFR **+{(nbiot_s.get('growth_2023_2026_pct') or {}).get('sfr')}%**, Bouygues **+{(nbiot_s.get('growth_2023_2026_pct') or {}).get('bouygues')}%** (2023→2026).",
        "",
        "### Utilisateurs / objets",
        "",
        f"- **LoRaWAN** : {(users.get('lora_trend') or '').strip()}",
        f"- **NB-IoT / cellulaire LPWA** : {(users.get('nbiot_trend') or '').strip()}",
        f"- **Synthèse** : {(users.get('net_france') or '').strip()}",
        "",
        f"- Opérateurs LoRaWAN public national : **1** (Orange).",
        f"- Opérateurs NB-IoT national : **3** (Orange ~{dm.get('nbiot_orange_pop_pct')} %, SFR ~{dm.get('nbiot_sfr_pop_pct')} %, Bouygues ~{dm.get('nbiot_bouygues_pop_pct')} %).",
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

    lines += ["", "## Graphiques (tendances)", ""]
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
        "- L'Arcep ne publie pas de couches NB-IoT / LTE-M / LoRaWAN : les % population sont déclaratifs.",
        "- Les sites 4G sont un **proxy** de densification cellulaire (NB-IoT in-band), pas un inventaire d'antennes NB-IoT dédiées.",
        "- Séries utilisateurs LoRaWAN partielles (Objenious, Birdz, déclarations Orange) — pas de recensement exhaustif Arcep.",
        "- Packet Broker ne capture pas le réseau LoRaWAN Orange opéré (~4800 antennes).",
        "",
        "## Reproductibilité",
        "",
        "```bash",
        "pip install -r requirements.txt",
        "python -m scripts.run_study --collect --spatial --analyze --report",
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
    for fn in (
        plot_growth_vs_decline_summary,
        plot_lora_antennas_trend,
        plot_nbiot_proxy_growth,
        plot_users_trend,
        plot_coverage_declared,
        plot_infrastructure_counts,
        plot_timeline,
    ):
        p = fn(analysis, fig_dir)
        if p:
            figures.append(p)
    rel_figs = [Path("figures") / f.name for f in figures]
    return render_markdown(analysis, rel_figs, root / "reports" / "etude_comparative_lora_nbiot_france.md")


if __name__ == "__main__":
    print(generate_report(Path(__file__).resolve().parents[2]))
