"""Focus grandes métropoles — LoRa vs NB-IoT projets métier + objets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

YEARS = list(range(2015, 2027))


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_objets_metropoles(data: dict[str, Any], out: Path) -> Path:
    rows = [p for p in data["projets"] if p.get("objets")]
    rows = sorted(rows, key=lambda x: int(x["objets"]), reverse=True)
    labels = [f"{p['metropole'][:28]}\n({p['tech']})" for p in rows]
    vals = [int(p["objets"]) for p in rows]
    colors = ["#1f6f5b" if p["tech"] == "LoRa" else "#0b3d91" for p in rows]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.barh(labels[::-1], vals[::-1], color=colors[::-1])
    ax.set_xscale("log")
    ax.set_xlabel("Objets déployés (échelle log)")
    ax.set_title("Grandes métropoles — Objets LoRa / NB-IoT documentés")
    ax.grid(True, alpha=0.3, axis="x", which="both")
    path = out / "metropoles_objets_lora_nbiot.png"
    _save(fig, path)
    return path


def plot_timeline_metropoles(data: dict[str, Any], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    y_pos = 0
    yticks, ylabels = [], []
    for p in sorted(data["projets"], key=lambda x: (x.get("year_start") or 9999, x["metropole"])):
        y0 = p.get("year_start") or 2015
        y1 = p.get("year_objets") or y0
        color = "#1f6f5b" if p["tech"] == "LoRa" else "#0b3d91"
        ax.plot([y0, y1], [y_pos, y_pos], "-", color=color, lw=3, solid_capstyle="round")
        ax.plot(y0, y_pos, "o", color=color, ms=7)
        if p.get("objets"):
            ax.plot(y1, y_pos, "D", color=color, ms=7)
            ax.text(y1 + 0.15, y_pos, f"{int(p['objets']):,}".replace(",", " "), va="center", fontsize=8)
        else:
            ax.text(y0 + 0.2, y_pos + 0.15, "sans volume", fontsize=7, color="#666")
        yticks.append(y_pos)
        short = p["metropole"].split("/")[0].strip()[:32]
        ylabels.append(f"{short} ({p['tech']})")
        y_pos += 1
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_xlim(2014.5, 2027)
    ax.set_xlabel("Année")
    ax.set_title("Grandes métropoles — Chronologie projets métier (○ démarrage, ◆ volume constaté)")
    ax.grid(True, alpha=0.3, axis="x")
    path = out / "metropoles_timeline_projets.png"
    _save(fig, path)
    return path


def build_report(data: dict[str, Any], figures: list[Path]) -> str:
    lines = [
        "# Grandes métropoles — projets métier LoRa vs NB-IoT",
        "",
        data["meta"]["method_note"].strip(),
        "",
        "## Tableau (métropoles avec projet métier documenté)",
        "",
        "| Métropole | Techno | Début | Objets | Détail objets | Statut |",
        "|---|---|---:|---:|---|---|",
    ]
    for p in sorted(data["projets"], key=lambda x: (-(x.get("objets") or 0), x["metropole"])):
        obj = "—" if not p.get("objets") else f"{int(p['objets']):,}".replace(",", " ")
        lines.append(
            f"| {p['metropole']} | {p['tech']} | {p.get('year_start','')} | {obj} | "
            f"{(p.get('objets_detail') or '')[:80]} | {p.get('status','')} |"
        )

    lines += [
        "",
        "## Métropoles sans projet métier documenté (dans nos sources)",
        "",
    ]
    for m in data.get("metropoles_sans_projet_metier_documente", {}).get("list") or []:
        lines.append(f"- {m}")

    lines += ["", "## Tendances", ""]
    for b in data["tendances_metropoles"]["resume"]:
        lines.append(f"- {b}")
    lines += ["", data["tendances_metropoles"]["ecart_lora_nbiot"].strip(), "", "## Graphiques", ""]
    for f in figures:
        lines.append(f"![{f.name}](figures/{f.name})")
        lines.append("")
    return "\n".join(lines)


def run(root: Path) -> dict[str, Any]:
    data = load_yaml(root / "data" / "curated" / "metropoles_lora_nbiot.yaml")
    fig_dir = root / "reports" / "figures"
    art = Path("/opt/cursor/artifacts/figures")
    art.mkdir(parents=True, exist_ok=True)
    figs = [plot_objets_metropoles(data, fig_dir), plot_timeline_metropoles(data, fig_dir)]
    for f in figs:
        (art / f.name).write_bytes(f.read_bytes())
    report = root / "reports" / "metropoles_lora_nbiot.md"
    report.write_text(build_report(data, figs), encoding="utf-8")
    out = {
        "n_projets": len(data["projets"]),
        "avec_objets": sum(1 for p in data["projets"] if p.get("objets")),
        "somme_objets_lora": sum(int(p["objets"]) for p in data["projets"] if p["tech"] == "LoRa" and p.get("objets")),
        "somme_objets_nbiot": sum(int(p["objets"]) for p in data["projets"] if p["tech"] == "NB-IoT" and p.get("objets")),
        "figures": [f.name for f in figs],
        "report": str(report),
        "projets": data["projets"],
    }
    (root / "data" / "processed" / "metropoles_lora_nbiot.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    print(json.dumps(run(Path(__file__).resolve().parents[2]), indent=2, ensure_ascii=False))
