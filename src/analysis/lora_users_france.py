"""Inventaire communes / sociétés LoRa France + tendances depuis 2015."""

from __future__ import annotations

import json
from collections import Counter
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


def plot_collectivites_cumul(data: dict[str, Any], out: Path) -> Path:
    series = data["tendances_depuis_2015"]["series"]
    years = [r["year"] for r in series]
    cumul = [r["collectivites_documentees_cumul"] for r in series]
    fig, ax = plt.subplots(figsize=(11, 5.0))
    ax.plot(years, cumul, "o-", color="#1f6f5b", lw=2.5, markersize=7)
    ax.fill_between(years, cumul, color="#1f6f5b", alpha=0.15)
    ax.axvline(2016, color="#333", ls=":", lw=1)
    ax.text(2016.1, 4, "Ouverture\nnationale", fontsize=8)
    ax.axvline(2018, color="#333", ls=":", lw=1)
    ax.text(2018.1, 12, "Birdz\neau", fontsize=8)
    ax.axvline(2024, color="#a00", ls=":", lw=1)
    ax.text(2024.05, 18, "Fin\nObjenious", fontsize=8, color="#a00")
    ax.set_title("France — Collectivités LoRa documentées (cumul inventaire)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Collectivités / territoires (cumul)")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    path = out / "lora_collectivites_cumul_depuis_2015.png"
    _save(fig, path)
    return path


def plot_objets_marqueurs(data: dict[str, Any], out: Path) -> Path:
    series = data["tendances_depuis_2015"]["series"]
    years, vals, labels = [], [], []
    for r in series:
        if r.get("objets_marqueurs"):
            years.append(r["year"])
            vals.append(r["objets_marqueurs"])
            labels.append(r.get("objets_note") or "")
    fig, ax = plt.subplots(figsize=(11, 5.2))
    colors = ["#c45c26" if "Objenious" in l else "#1f6f5b" if "Birdz" in l or "Alliance" in l else "#0b3d91" for l in labels]
    bars = ax.bar([str(y) for y in years], vals, color=colors)
    ax.set_yscale("log")
    ax.set_title("France — Marqueurs d'objets LoRaWAN (sources ponctuelles, échelle log)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Objets (ordre de grandeur)")
    ax.grid(True, alpha=0.3, which="both", axis="y")
    for bar, lab in zip(bars, labels):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.15,
            lab[:42] + ("…" if len(lab) > 42 else ""),
            ha="center",
            va="bottom",
            fontsize=7,
            rotation=15,
        )
    path = out / "lora_objets_marqueurs_depuis_2015.png"
    _save(fig, path)
    return path


def plot_roles_societes(data: dict[str, Any], out: Path) -> Path:
    roles = Counter(s.get("role", "autre") for s in data["societes"])
    labels = {
        "operateur": "Opérateurs",
        "operateur_communautaire": "Opérateurs communautaires",
        "reseau_depin": "DePIN (Helium)",
        "vendor_plateforme": "Plateformes",
        "vendor_gateways": "Gateways",
        "vendor_capteurs": "Capteurs",
        "vendor_trackers": "Trackers",
        "vendor_logiciel": "Logiciel",
        "vendor_chip": "Chip / radio",
        "utilisateur": "Utilisateurs",
        "utilisateur_massif": "Utilisateurs massifs",
        "utilisateur_fournisseur": "User / fournisseur",
        "integrateur": "Intégrateurs",
    }
    items = sorted(roles.items(), key=lambda x: -x[1])
    names = [labels.get(k, k) for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.barh(names[::-1], vals[::-1], color="#1f6f5b")
    ax.set_title("France — Sociétés LoRa inventoriées par rôle")
    ax.set_xlabel("Nombre (inventaire documenté)")
    ax.grid(True, alpha=0.3, axis="x")
    path = out / "lora_societes_par_role.png"
    _save(fig, path)
    return path


def plot_usecases_collectivites(data: dict[str, Any], out: Path) -> Path:
    c = Counter()
    for col in data["collectivites"]:
        for u in col.get("use_cases") or []:
            if u == "couverture_operateur":
                continue  # bruit : ouverture radio ≠ projet métier
            c[u] += 1
    labels_fr = {
        "teleleve_eau": "Télérelève eau",
        "dechets": "Déchets",
        "eclairage": "Éclairage",
        "stationnement": "Stationnement",
        "batiments": "Bâtiments",
        "mobilite": "Mobilité",
        "environnement": "Environnement",
        "hydrologie": "Hydrologie",
        "air": "Qualité air",
        "ilots_fraicheur": "Îlots de fraîcheur",
        "ecoles": "Écoles / confort",
        "qualite_air": "Qualité air",
        "frequentation": "Fréquentation",
        "bornes_ve": "Bornes VE",
        "patrimoine": "Patrimoine",
        "recherche": "Recherche",
        "pilote_reseau": "Pilote réseau",
        "smart_city": "Smart city (générique)",
    }
    items = sorted(c.items(), key=lambda x: -x[1])[:12]
    names = [labels_fr.get(k, k) for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.barh(names[::-1], vals[::-1], color="#0b3d91")
    ax.set_title("France — Cas d'usage LoRa des collectivités documentées")
    ax.set_xlabel("Mentions (hors simple couverture opérateur)")
    ax.grid(True, alpha=0.3, axis="x")
    path = out / "lora_usecases_collectivites.png"
    _save(fig, path)
    return path


def plot_phases_timeline(data: dict[str, Any], out: Path) -> Path:
    series = data["tendances_depuis_2015"]["series"]
    phase_colors = {
        "naissance": "#8d6e63",
        "ouverture_nationale": "#1f6f5b",
        "densification": "#2e7d32",
        "metering_massif": "#1565c0",
        "smart_city": "#6a1b9a",
        "consolidation": "#455a64",
        "expansion_verticales": "#ef6c00",
        "leadership_marche": "#00838f",
        "bascule_operateurs": "#c62828",
        "rupture_duopole": "#b71c1c",
        "prives_departementaux": "#33691e",
        "dual_track": "#1a237e",
    }
    fig, ax = plt.subplots(figsize=(12, 4.2))
    for r in series:
        ax.barh(
            0,
            0.9,
            left=r["year"] - 0.45,
            height=0.55,
            color=phase_colors.get(r["phase"], "#777"),
            edgecolor="white",
        )
        ax.text(r["year"], 0.35, str(r["year"]), ha="center", fontsize=8, color="#222")
    ax.set_yticks([])
    ax.set_xlim(2014.4, 2026.6)
    ax.set_ylim(-0.5, 1.2)
    ax.set_title("France — Phases LoRaWAN depuis 2015")
    # legend condensed
    seen = []
    for r in series:
        p = r["phase"]
        if p not in seen:
            seen.append(p)
            ax.scatter([], [], color=phase_colors.get(p, "#777"), label=p.replace("_", " "), s=40)
    ax.legend(loc="upper center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.08))
    path = out / "lora_phases_depuis_2015.png"
    _save(fig, path)
    return path


def build_report(data: dict[str, Any], figures: list[Path], root: Path) -> str:
    lines = [
        "# Usagers LoRa / LoRaWAN en France — communes, villes, sociétés",
        "",
        data["meta"]["method_note"].strip(),
        "",
        "## Tendances depuis 2015",
        "",
    ]
    for b in data["tendances_depuis_2015"]["resume"]:
        lines.append(f"- {b}")
    lines += ["", "### Chronologie", ""]
    for r in data["tendances_depuis_2015"]["series"]:
        lines.append(f"- **{r['year']}** ({r['phase'].replace('_', ' ')}) — {r['highlight']}")

    lines += [
        "",
        "## Collectivités / villes documentées",
        "",
        "| Collectivité | Type | Début | Cas d'usage | Réseau | Objets (approx.) |",
        "|---|---|---:|---|---|---:|",
    ]
    for c in sorted(data["collectivites"], key=lambda x: (x.get("year_start") or 9999, x["name"])):
        uses = ", ".join((c.get("use_cases") or [])[:4])
        obj = c.get("objets_approx")
        obj_s = f"{obj:,}".replace(",", " ") if obj else "—"
        lines.append(
            f"| {c['name']} | {c.get('type','')} | {c.get('year_start','')} | {uses} | "
            f"{c.get('network','')} | {obj_s} |"
        )

    lines += [
        "",
        f"> Zones d'ouverture Orange 2016 : {', '.join(data['orange_launch_2016_zones']['cities'])}.",
        "",
        "## Sociétés",
        "",
        "| Société | Rôle | Verticale | Début | Note |",
        "|---|---|---|---:|---|",
    ]
    for s in sorted(data["societes"], key=lambda x: (x.get("year_start") or 9999, x["name"])):
        note = (s.get("note") or "").replace("|", "/")
        end = f"–{s['year_end']}" if s.get("year_end") else ""
        lines.append(
            f"| {s['name']} | {s.get('role','')} | {s.get('vertical','')} | "
            f"{s.get('year_start','')}{end} | {note} |"
        )

    lines += ["", "## Graphiques", ""]
    for f in figures:
        lines.append(f"![{f.name}](figures/{f.name})")
        lines.append("")

    lines += [
        "## Limites",
        "",
        "- Inventaire **non exhaustif** (presse / CP / REX).",
        "- « 30 000 communes couvertes » = éligibilité radio, pas 30 000 projets.",
        "- Les volumes d'objets sont des **marqueurs sourcés** (pas une série homogène).",
        "",
    ]
    return "\n".join(lines)


def run(root: Path) -> dict[str, Any]:
    data = load_yaml(root / "data" / "curated" / "lora_users_france.yaml")
    fig_dir = root / "reports" / "figures"
    art_dir = Path("/opt/cursor/artifacts/figures")
    art_dir.mkdir(parents=True, exist_ok=True)

    figs = [
        plot_phases_timeline(data, fig_dir),
        plot_collectivites_cumul(data, fig_dir),
        plot_objets_marqueurs(data, fig_dir),
        plot_usecases_collectivites(data, fig_dir),
        plot_roles_societes(data, fig_dir),
    ]
    for f in figs:
        (art_dir / f.name).write_bytes(f.read_bytes())

    md = build_report(data, figs, root)
    report_path = root / "reports" / "lora_usagers_france_depuis_2015.md"
    report_path.write_text(md, encoding="utf-8")

    out = {
        "n_collectivites": len(data["collectivites"]),
        "n_societes": len(data["societes"]),
        "figures": [f.name for f in figs],
        "report": str(report_path),
        "tendances": data["tendances_depuis_2015"]["resume"],
        "verticales": data["tendances_depuis_2015"]["verticales_dominantes"],
    }
    (root / "data" / "processed" / "lora_users_france_analysis.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    result = run(Path(__file__).resolve().parents[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))
