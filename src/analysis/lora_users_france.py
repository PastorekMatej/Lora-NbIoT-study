"""Quantification collectivités / sociétés LoRa France + tendances depuis 2015."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
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


def _is_metier(c: dict[str, Any]) -> bool:
    if c.get("usage_level") == "projet_metier":
        return True
    uses = set(c.get("use_cases") or [])
    return bool(uses - {"couverture_operateur"})


def _type_bucket(t: str | None) -> str:
    t = (t or "autre").lower()
    if t in {"ville", "commune"}:
        return "villes_communes"
    if t in {"metropole", "eurometropole", "agglomeration", "intercommunalite"}:
        return "intercommunalites"
    if t in {"departement", "departements", "syndicats_mixtes", "syndicat"}:
        return "departements_syndicats"
    return "autre"


def _role_bucket(role: str | None) -> str:
    r = role or "autre"
    if r in {"operateur", "operateur_communautaire", "operateur_dsp", "reseau_depin"}:
        return "operateurs_reseaux"
    if r.startswith("vendor") or r == "vendor_chip":
        return "vendors"
    if r in {"utilisateur", "utilisateur_massif", "utilisateur_fournisseur"}:
        return "utilisateurs"
    if r == "integrateur":
        return "integrateurs"
    return "autre"


def compute_quantification(data: dict[str, Any]) -> dict[str, Any]:
    cols = data["collectivites"]
    socs = data["societes"]

    new_all = Counter()
    new_metier = Counter()
    new_by_type = defaultdict(Counter)
    objets_new = Counter()
    for c in cols:
        y = c.get("year_start")
        if y is None or y < 2015:
            continue
        y = int(y)
        new_all[y] += 1
        if _is_metier(c):
            new_metier[y] += 1
            new_by_type[_type_bucket(c.get("type"))][y] += 1
            if c.get("objets_approx"):
                oy = int(c.get("objets_year") or y)
                if oy >= 2015:
                    objets_new[oy] += int(c["objets_approx"])

    new_soc = Counter()
    end_soc = Counter()
    for s in socs:
        ys = s.get("year_start")
        if ys is not None and int(ys) >= 2015:
            new_soc[int(ys)] += 1
        elif ys is not None and int(ys) < 2015:
            new_soc[2015] += 1  # déjà présentes au début de la période
        ye = s.get("year_end")
        if ye is not None:
            end_soc[int(ye)] += 1

    rows = []
    cumul_all = cumul_metier = cumul_soc_seen = 0
    cumul_objets_doc = 0
    cumul_type = {"villes_communes": 0, "intercommunalites": 0, "departements_syndicats": 0, "autre": 0}

    for y in YEARS:
        cumul_all += new_all[y]
        cumul_metier += new_metier[y]
        cumul_soc_seen += new_soc[y]
        cumul_objets_doc += objets_new[y]
        for b in cumul_type:
            cumul_type[b] += new_by_type[b][y]

        active_soc = 0
        active_by_role = Counter()
        for s in socs:
            ys = int(s.get("year_start") or 9999)
            ye = s.get("year_end")
            if ys <= y and (ye is None or int(ye) >= y):
                active_soc += 1
                active_by_role[_role_bucket(s.get("role"))] += 1

        prev_metier = rows[-1]["cumul_projets_metier"] if rows else 0
        growth = None
        if prev_metier > 0 and new_metier[y] is not None:
            growth = round(100.0 * (cumul_metier - prev_metier) / prev_metier, 1)

        rows.append(
            {
                "year": y,
                "nouveaux_inventaire": new_all[y],
                "nouveaux_projets_metier": new_metier[y],
                "cumul_inventaire": cumul_all,
                "cumul_projets_metier": cumul_metier,
                "croissance_cumul_metier_pct": growth,
                "cumul_villes_communes_metier": cumul_type["villes_communes"],
                "cumul_intercommunalites_metier": cumul_type["intercommunalites"],
                "cumul_departements_syndicats_metier": cumul_type["departements_syndicats"],
                "nouvelles_societes": new_soc[y],
                "societes_actives": active_soc,
                "societes_actives_operateurs": active_by_role["operateurs_reseaux"],
                "societes_actives_vendors": active_by_role["vendors"],
                "societes_actives_utilisateurs": active_by_role["utilisateurs"],
                "societes_actives_integrateurs": active_by_role["integrateurs"],
                "objets_documentes_nouveaux": objets_new[y],
                "objets_documentes_cumul": cumul_objets_doc,
            }
        )

    # Phase growth summary
    def cumul_at(year: int) -> int:
        return next(r["cumul_projets_metier"] for r in rows if r["year"] == year)

    growth_phases = [
        {
            "periode": "2015–2017",
            "projets_metier_debut": cumul_at(2015),
            "projets_metier_fin": cumul_at(2017),
            "variation_pct": round(100 * (cumul_at(2017) - cumul_at(2015)) / max(cumul_at(2015), 1), 1),
            "lecture": "Amorçage + ouverture nationale ; peu de projets métier hors pilotes/grandes villes",
        },
        {
            "periode": "2018–2022",
            "projets_metier_debut": cumul_at(2017),
            "projets_metier_fin": cumul_at(2022),
            "variation_pct": round(100 * (cumul_at(2022) - cumul_at(2017)) / max(cumul_at(2017), 1), 1),
            "lecture": "CROISSANCE forte : eau, smart city, départements (Sarthe, Finistère), déchets",
        },
        {
            "periode": "2023–2026",
            "projets_metier_debut": cumul_at(2022),
            "projets_metier_fin": cumul_at(2026),
            "variation_pct": round(100 * (cumul_at(2026) - cumul_at(2022)) / max(cumul_at(2022), 1), 1),
            "lecture": "CROISSANCE continue des projets métier privés malgré fin Objenious",
        },
    ]

    return {
        "annual": rows,
        "growth_phases": growth_phases,
        "totals": {
            "collectivites_inventaire": len(cols),
            "projets_metier": sum(1 for c in cols if _is_metier(c)),
            "couverture_operateur_seule": sum(1 for c in cols if not _is_metier(c)),
            "societes": len(socs),
            "objets_documentes_cumul": rows[-1]["objets_documentes_cumul"],
        },
        "marqueurs_externes": data.get("marqueurs_quantitatifs", {}),
    }


def plot_flux_cumul(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(11.5, 5.2))
    ax1.bar(
        [y - 0.15 for y in years],
        [r["nouveaux_projets_metier"] for r in rows],
        width=0.3,
        color="#1f6f5b",
        label="Nouveaux projets métier",
    )
    ax1.bar(
        [y + 0.15 for y in years],
        [r["nouveaux_inventaire"] - r["nouveaux_projets_metier"] for r in rows],
        width=0.3,
        color="#9e9e9e",
        label="Nouveaux couverture seule",
    )
    ax1.set_ylabel("Nouveaux / an")
    ax1.set_xlabel("Année")
    ax2 = ax1.twinx()
    ax2.plot(
        years,
        [r["cumul_projets_metier"] for r in rows],
        "o-",
        color="#0b3d91",
        lw=2.5,
        label="Cumul projets métier",
    )
    ax2.plot(
        years,
        [r["cumul_inventaire"] for r in rows],
        "s--",
        color="#6d4c41",
        lw=1.8,
        label="Cumul inventaire total",
    )
    ax2.set_ylabel("Cumul")
    ax1.set_xticks(years)
    ax1.set_title("France — Quantification collectivités LoRa (flux + cumul) depuis 2015")
    ax1.grid(True, alpha=0.3, axis="y")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    ax1.axvline(2024, color="#a00", ls=":", lw=1)
    ax1.text(2024.05, ax1.get_ylim()[1] * 0.85 if ax1.get_ylim()[1] else 1, "Fin\nObjenious", color="#a00", fontsize=8)
    path = out / "lora_quantif_collectivites_flux_cumul.png"
    _save(fig, path)
    return path


def plot_types_stack(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]
    v = [r["cumul_villes_communes_metier"] for r in rows]
    i = [r["cumul_intercommunalites_metier"] for r in rows]
    d = [r["cumul_departements_syndicats_metier"] for r in rows]
    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.stackplot(
        years,
        v,
        i,
        d,
        labels=["Villes / communes", "Métropoles / agglo / EPCI", "Départements / syndicats"],
        colors=["#1f6f5b", "#0b3d91", "#c45c26"],
        alpha=0.85,
    )
    ax.set_title("France — Cumul projets métier LoRa par type de collectivité")
    ax.set_xlabel("Année")
    ax.set_ylabel("Cumul (projets métier)")
    ax.set_xticks(years)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    path = out / "lora_quantif_types_collectivites.png"
    _save(fig, path)
    return path


def plot_societes_actives(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]
    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.plot(years, [r["societes_actives"] for r in rows], "o-", color="#222", lw=2.5, label="Total actives")
    ax.plot(years, [r["societes_actives_operateurs"] for r in rows], "s-", color="#c62828", label="Opérateurs / réseaux")
    ax.plot(years, [r["societes_actives_vendors"] for r in rows], "^-", color="#1565c0", label="Vendors")
    ax.plot(years, [r["societes_actives_utilisateurs"] for r in rows], "D-", color="#1f6f5b", label="Utilisateurs")
    ax.plot(years, [r["societes_actives_integrateurs"] for r in rows], "v-", color="#ef6c00", label="Intégrateurs")
    ax.axvline(2024, color="#a00", ls=":", lw=1)
    ax.text(2024.05, 2, "Objenious\n↓", color="#a00", fontsize=8)
    ax.set_title("France — Sociétés LoRa actives (inventaire) depuis 2015")
    ax.set_xlabel("Année")
    ax.set_ylabel("Sociétés actives")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    path = out / "lora_quantif_societes_actives.png"
    _save(fig, path)
    return path


def plot_croissance_phases(q: dict[str, Any], out: Path) -> Path:
    phases = q["growth_phases"]
    labels = [p["periode"] for p in phases]
    vals = [p["variation_pct"] for p in phases]
    colors = ["#8d6e63", "#1f6f5b", "#0b3d91"]
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    bars = ax.bar(labels, vals, color=colors)
    ax.axhline(0, color="#333", lw=0.8)
    ax.set_title("France — Croissance du cumul de projets métier LoRa par période")
    ax.set_ylabel("Variation du cumul (%)")
    for bar, p in zip(bars, phases):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (3 if bar.get_height() >= 0 else -8),
            f"{p['projets_metier_debut']} → {p['projets_metier_fin']}",
            ha="center",
            fontsize=9,
        )
    ax.grid(True, alpha=0.3, axis="y")
    path = out / "lora_quantif_croissance_phases.png"
    _save(fig, path)
    return path


def plot_objets_doc(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(11.5, 5.0))
    ax1.bar(years, [r["objets_documentes_nouveaux"] for r in rows], color="#0b3d91", alpha=0.85, label="Nouveaux objets documentés")
    ax2 = ax1.twinx()
    ax2.plot(years, [r["objets_documentes_cumul"] for r in rows], "o-", color="#c45c26", lw=2.5, label="Cumul objets documentés")
    ax1.set_yscale("log")
    ax2.set_yscale("log")
    ax1.set_title("France — Objets LoRa des projets documentés (inventaire, log)")
    ax1.set_xlabel("Année")
    ax1.set_ylabel("Nouveaux / an")
    ax2.set_ylabel("Cumul")
    ax1.set_xticks(years)
    ax1.grid(True, alpha=0.3, which="both", axis="y")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")
    path = out / "lora_quantif_objets_documentes.png"
    _save(fig, path)
    return path


def plot_triple_tendance(q: dict[str, Any], out: Path) -> Path:
    """Vue synthétique : projets métier, sociétés actives, objets doc (normés 100)."""
    rows = q["annual"]
    years = [r["year"] for r in rows]
    def norm(key):
        vals = [r[key] for r in rows]
        m = max(vals) or 1
        return [100 * v / m for v in vals]

    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.plot(years, norm("cumul_projets_metier"), "o-", color="#1f6f5b", lw=2.5, label="Cumul projets métier (index)")
    ax.plot(years, norm("societes_actives"), "s-", color="#0b3d91", lw=2.5, label="Sociétés actives (index)")
    ax.plot(years, norm("objets_documentes_cumul"), "^-", color="#c45c26", lw=2.5, label="Objets documentés cumul (index)")
    ax.set_ylim(0, 110)
    ax.set_title("France — Tendances comparées depuis 2015 (index 100 = max)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Index")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    ax.axvline(2018, color="#333", ls=":", lw=1)
    ax.text(2018.1, 20, "Birdz", fontsize=8)
    ax.axvline(2024, color="#a00", ls=":", lw=1)
    ax.text(2024.05, 30, "Fin\nObjenious", color="#a00", fontsize=8)
    path = out / "lora_quantif_tendances_index.png"
    _save(fig, path)
    return path


def build_report(data: dict[str, Any], q: dict[str, Any], figures: list[Path]) -> str:
    t = q["totals"]
    lines = [
        "# Quantification LoRa France — collectivités, villes, sociétés depuis 2015",
        "",
        data["meta"]["method_note"].strip(),
        "",
        "## Synthèse chiffrée (inventaire)",
        "",
        f"- Collectivités inventoriées : **{t['collectivites_inventaire']}**",
        f"- dont projets métier : **{t['projets_metier']}**",
        f"- dont couverture opérateur seule : **{t['couverture_operateur_seule']}**",
        f"- Sociétés inventoriées : **{t['societes']}**",
        f"- Objets documentés (somme des projets ayant un chiffre) : **{t['objets_documentes_cumul']:,}**".replace(",", " "),
        "",
        "## Tendances (croissance du cumul projets métier)",
        "",
        "| Période | Début | Fin | Variation | Lecture |",
        "|---|---:|---:|---:|---|",
    ]
    for p in q["growth_phases"]:
        lines.append(
            f"| {p['periode']} | {p['projets_metier_debut']} | {p['projets_metier_fin']} | "
            f"**{p['variation_pct']}%** | {p['lecture']} |"
        )

    lines += ["", "## Tableau annuel quantifié", "", 
              "| Année | + inventaire | + projets métier | Cumul métier | Croissance cumul métier | Cumul inventaire | Sociétés actives | Objets doc. cumul |",
              "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in q["annual"]:
        g = "—" if r["croissance_cumul_metier_pct"] is None else f"{r['croissance_cumul_metier_pct']}%"
        lines.append(
            f"| {r['year']} | {r['nouveaux_inventaire']} | {r['nouveaux_projets_metier']} | "
            f"{r['cumul_projets_metier']} | {g} | {r['cumul_inventaire']} | "
            f"{r['societes_actives']} | {r['objets_documentes_cumul']:,} |".replace(",", " ")
        )

    lines += ["", "### Lecture", ""]
    for b in data["tendances_depuis_2015"]["resume"]:
        lines.append(f"- {b}")

    lines += [
        "",
        "## Marqueurs externes (hors inventaire nominatif)",
        "",
        "| Année | Métrique | Valeur | Confiance |",
        "|---:|---|---:|---|",
    ]
    for m in (q.get("marqueurs_externes") or {}).get("series") or []:
        lines.append(
            f"| {m['year']} | {m['metric']} | {m['value']:,} | {m.get('confidence','')} |".replace(",", " ")
        )

    lines += ["", "## Graphiques", ""]
    for f in figures:
        lines.append(f"![{f.name}](figures/{f.name})")
        lines.append("")

    lines += [
        "## Collectivités (projets métier)",
        "",
        "| Collectivité | Type | Début | Objets |",
        "|---|---|---:|---:|",
    ]
    for c in sorted(data["collectivites"], key=lambda x: (x.get("year_start") or 9999, x["name"])):
        if not _is_metier(c):
            continue
        obj = c.get("objets_approx")
        obj_s = f"{int(obj):,}".replace(",", " ") if obj else "—"
        lines.append(f"| {c['name']} | {c.get('type','')} | {c.get('year_start','')} | {obj_s} |")

    lines += [
        "",
        "## Sociétés",
        "",
        "| Société | Rôle | Début | Fin |",
        "|---|---|---:|---:|",
    ]
    for s in sorted(data["societes"], key=lambda x: (x.get("year_start") or 9999, x["name"])):
        lines.append(
            f"| {s['name']} | {s.get('role','')} | {s.get('year_start','')} | {s.get('year_end') or '—'} |"
        )

    lines += [
        "",
        "## Limites",
        "",
        "- Inventaire **non exhaustif** : la croissance mesurée est celle de l’échantillon documenté.",
        "- Couverture radio (~30 000 communes) ≠ projets métier.",
        "- Claim « 500 collectivités (2021) » : marqueur secondaire à **faible confiance**.",
        "- Objets documentés = somme des projets ayant publié un chiffre (sous-estime le parc réel).",
        "",
    ]
    return "\n".join(lines)


def run(root: Path) -> dict[str, Any]:
    data = load_yaml(root / "data" / "curated" / "lora_users_france.yaml")
    q = compute_quantification(data)
    fig_dir = root / "reports" / "figures"
    art_dir = Path("/opt/cursor/artifacts/figures")
    art_dir.mkdir(parents=True, exist_ok=True)

    figs = [
        plot_flux_cumul(q, fig_dir),
        plot_types_stack(q, fig_dir),
        plot_societes_actives(q, fig_dir),
        plot_croissance_phases(q, fig_dir),
        plot_objets_doc(q, fig_dir),
        plot_triple_tendance(q, fig_dir),
    ]
    for f in figs:
        (art_dir / f.name).write_bytes(f.read_bytes())

    report_path = root / "reports" / "lora_usagers_france_depuis_2015.md"
    report_path.write_text(build_report(data, q, figs), encoding="utf-8")

    out = {
        "quantification": q,
        "figures": [f.name for f in figs],
        "report": str(report_path),
    }
    (root / "data" / "processed" / "lora_users_france_analysis.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    result = run(Path(__file__).resolve().parents[2])
    q = result["quantification"]
    print(json.dumps({
        "totals": q["totals"],
        "growth_phases": q["growth_phases"],
        "annual_tail": q["annual"][-5:],
        "figures": result["figures"],
    }, indent=2, ensure_ascii=False))
