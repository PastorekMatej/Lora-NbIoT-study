"""Quantification projets métier NB-IoT France + tendances depuis 2015."""

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
    if t in {"metropole", "eurometropole", "agglomeration", "intercommunalite", "communaute_agglomeration"}:
        return "intercommunalites"
    if t in {"departement", "departements", "syndicats_mixtes", "syndicat"}:
        return "departements_syndicats"
    return "autre"


def _role_bucket(role: str | None) -> str:
    r = role or "autre"
    if r in {"operateur", "operateur_communautaire", "operateur_dsp", "reseau_depin"}:
        return "operateurs_reseaux"
    if str(r).startswith("vendor"):
        return "vendors"
    if r in {"utilisateur", "utilisateur_massif", "utilisateur_fournisseur"}:
        return "utilisateurs"
    if r == "integrateur":
        return "integrateurs"
    return "autre"


def _all_metier_projects(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Collectivités métier + projets anonymes (usage documenté)."""
    items = [c for c in data.get("collectivites") or [] if _is_metier(c)]
    for p in data.get("projets_metier_anonymes") or []:
        items.append({**p, "type": p.get("type") or "projet_anonyme", "name": p["name"]})
    return items


def compute_quantification(data: dict[str, Any]) -> dict[str, Any]:
    cols = data.get("collectivites") or []
    metier_all = _all_metier_projects(data)
    socs = data.get("societes") or []

    new_named = Counter()
    new_metier = Counter()
    new_by_type = defaultdict(Counter)
    objets_new = Counter()

    for c in cols:
        y = c.get("year_start")
        if y is None or int(y) < 2015:
            continue
        y = int(y)
        new_named[y] += 1

    for c in metier_all:
        y = c.get("year_start")
        if y is None or int(y) < 2015:
            continue
        y = int(y)
        new_metier[y] += 1
        new_by_type[_type_bucket(c.get("type"))][y] += 1
        if c.get("objets_approx"):
            oy = int(c.get("objets_year") or y)
            if oy >= 2015:
                objets_new[oy] += int(c["objets_approx"])

    new_soc = Counter()
    for s in socs:
        ys = s.get("year_start")
        if ys is None:
            continue
        ys = int(ys)
        if ys < 2015:
            new_soc[2015] += 1
        else:
            new_soc[ys] += 1

    rows = []
    cumul_named = cumul_metier = 0
    cumul_objets = 0
    cumul_type = {
        "villes_communes": 0,
        "intercommunalites": 0,
        "departements_syndicats": 0,
        "autre": 0,
    }

    for y in YEARS:
        cumul_named += new_named[y]
        cumul_metier += new_metier[y]
        cumul_objets += objets_new[y]
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

        prev = rows[-1]["cumul_projets_metier"] if rows else 0
        growth = None
        if prev > 0:
            growth = round(100.0 * (cumul_metier - prev) / prev, 1)

        rows.append(
            {
                "year": y,
                "nouveaux_collectivites_nommees": new_named[y],
                "nouveaux_projets_metier": new_metier[y],
                "cumul_collectivites_nommees": cumul_named,
                "cumul_projets_metier": cumul_metier,
                "croissance_cumul_metier_pct": growth,
                "cumul_villes_communes_metier": cumul_type["villes_communes"],
                "cumul_intercommunalites_metier": cumul_type["intercommunalites"],
                "cumul_departements_syndicats_metier": cumul_type["departements_syndicats"],
                "cumul_autre_metier": cumul_type["autre"],
                "nouvelles_societes": new_soc[y],
                "societes_actives": active_soc,
                "societes_actives_operateurs": active_by_role["operateurs_reseaux"],
                "societes_actives_vendors": active_by_role["vendors"],
                "societes_actives_utilisateurs": active_by_role["utilisateurs"],
                "societes_actives_integrateurs": active_by_role["integrateurs"],
                "objets_documentes_nouveaux": objets_new[y],
                "objets_documentes_cumul": cumul_objets,
            }
        )

    def cumul_at(year: int) -> int:
        return next(r["cumul_projets_metier"] for r in rows if r["year"] == year)

    growth_phases = [
        {
            "periode": "2015–2018",
            "projets_metier_debut": cumul_at(2015),
            "projets_metier_fin": cumul_at(2018),
            "variation_pct": None,
            "lecture": "NÉANT commercial NB-IoT FR — 0 projet métier inventorié",
        },
        {
            "periode": "2019–2021",
            "projets_metier_debut": cumul_at(2018),
            "projets_metier_fin": cumul_at(2021),
            "variation_pct": None,
            "lecture": "Lancement opérateurs (SFR, Objenious) ; écosystème sociétés ↑ ; projets métier encore 0",
        },
        {
            "periode": "2022–2026",
            "projets_metier_debut": max(cumul_at(2021), 1),
            "projets_metier_fin": cumul_at(2026),
            "variation_pct": round(100 * (cumul_at(2026) - cumul_at(2021)) / max(cumul_at(2021), 1), 1)
            if cumul_at(2021)
            else None,
            "lecture": "Premiers projets métier eau (fuites) ; couverture nationale déjà dense",
        },
    ]
    # Fix 2022-2026 growth when start is 0
    if cumul_at(2021) == 0 and cumul_at(2026) > 0:
        growth_phases[2]["projets_metier_debut"] = 0
        growth_phases[2]["variation_pct"] = None
        growth_phases[2]["lecture"] = (
            f"Passage de 0 → {cumul_at(2026)} projets métier documentés (eau/fuites) "
            "alors que la couverture opérateur est déjà nationale"
        )

    return {
        "annual": rows,
        "growth_phases": growth_phases,
        "totals": {
            "collectivites_nommees": len(cols),
            "projets_metier": len(metier_all),
            "projets_metier_collectivites": sum(1 for c in cols if _is_metier(c)),
            "projets_metier_anonymes": len(data.get("projets_metier_anonymes") or []),
            "societes": len(socs),
            "objets_documentes_cumul": rows[-1]["objets_documentes_cumul"],
        },
        "marqueurs_externes": data.get("marqueurs_quantitatifs", {}),
        "national_facts": data.get("national_facts", []),
    }


def plot_flux_cumul(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(11.5, 5.2))
    ax1.bar(
        years,
        [r["nouveaux_projets_metier"] for r in rows],
        color="#0b3d91",
        width=0.6,
        label="Nouveaux projets métier",
    )
    ax1.set_ylabel("Nouveaux / an")
    ax1.set_xlabel("Année")
    ax2 = ax1.twinx()
    ax2.plot(
        years,
        [r["cumul_projets_metier"] for r in rows],
        "o-",
        color="#c45c26",
        lw=2.5,
        label="Cumul projets métier",
    )
    ax2.set_ylabel("Cumul")
    ax1.set_xticks(years)
    ax1.set_title("France — Quantification projets métier NB-IoT (flux + cumul) depuis 2015")
    ax1.grid(True, alpha=0.3, axis="y")
    ax1.axvline(2019, color="#333", ls=":", lw=1)
    ax1.text(2019.1, max(1, ax1.get_ylim()[1] * 0.7), "SFR\nNB-IoT", fontsize=8)
    ax1.axvline(2021, color="#333", ls=":", lw=1)
    ax1.text(2021.1, max(1, ax1.get_ylim()[1] * 0.45), "Objenious\nNB-IoT", fontsize=8)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    path = out / "nbiot_quantif_projets_metier_flux_cumul.png"
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
    ax.axvline(2019, color="#333", ls=":", lw=1)
    ax.text(2019.1, 1, "SFR", fontsize=8)
    ax.axvline(2021, color="#333", ls=":", lw=1)
    ax.text(2021.1, 2, "Objenious", fontsize=8)
    ax.set_title("France — Sociétés NB-IoT actives (inventaire) depuis 2015")
    ax.set_xlabel("Année")
    ax.set_ylabel("Sociétés actives")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    path = out / "nbiot_quantif_societes_actives.png"
    _save(fig, path)
    return path


def plot_tendances_index(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]

    def norm(key: str) -> list[float]:
        vals = [r[key] for r in rows]
        m = max(vals) or 1
        return [100 * v / m for v in vals]

    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.plot(years, norm("cumul_projets_metier"), "o-", color="#0b3d91", lw=2.5, label="Cumul projets métier (index)")
    ax.plot(years, norm("societes_actives"), "s-", color="#c62828", lw=2.5, label="Sociétés actives (index)")
    ax.plot(years, norm("objets_documentes_cumul"), "^-", color="#c45c26", lw=2.5, label="Objets documentés cumul (index)")
    ax.set_ylim(0, 110)
    ax.set_title("France — Tendances NB-IoT comparées depuis 2015 (index 100 = max)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Index")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    ax.axvline(2019, color="#333", ls=":", lw=1)
    ax.text(2019.1, 15, "SFR", fontsize=8)
    ax.axvline(2022, color="#333", ls=":", lw=1)
    ax.text(2022.1, 25, "1ers\nprojets", fontsize=8)
    path = out / "nbiot_quantif_tendances_index.png"
    _save(fig, path)
    return path


def plot_objets(q: dict[str, Any], out: Path) -> Path:
    rows = q["annual"]
    years = [r["year"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(11.5, 5.0))
    ax1.bar(years, [r["objets_documentes_nouveaux"] for r in rows], color="#0b3d91", alpha=0.85, label="Nouveaux")
    ax2 = ax1.twinx()
    ax2.plot(years, [r["objets_documentes_cumul"] for r in rows], "o-", color="#c45c26", lw=2.5, label="Cumul")
    ax1.set_title("France — Objets NB-IoT des projets documentés (inventaire)")
    ax1.set_xlabel("Année")
    ax1.set_ylabel("Nouveaux / an")
    ax2.set_ylabel("Cumul")
    ax1.set_xticks(years)
    ax1.grid(True, alpha=0.3, axis="y")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")
    path = out / "nbiot_quantif_objets_documentes.png"
    _save(fig, path)
    return path


def plot_cover_vs_metier(data: dict[str, Any], q: dict[str, Any], out: Path) -> Path:
    """Contraste couverture (communes Objenious 2021) vs projets métier cumul."""
    rows = q["annual"]
    years = [r["year"] for r in rows]
    cover = []
    for y in years:
        if y < 2021:
            cover.append(0)
        elif y == 2021:
            cover.append(1000)
        else:
            cover.append(1000)  # borne basse connue ; couverture réelle >> ensuite
    fig, ax1 = plt.subplots(figsize=(11.5, 5.2))
    ax1.plot(years, cover, "s--", color="#9e9e9e", lw=2, label="Couverture (borne : ~1000 communes Objenious 2021)")
    ax2 = ax1.twinx()
    ax2.plot(
        years,
        [r["cumul_projets_metier"] for r in rows],
        "o-",
        color="#0b3d91",
        lw=2.5,
        label="Cumul projets métier",
    )
    ax1.set_ylabel("Communes couvertes (ordre de grandeur)")
    ax2.set_ylabel("Projets métier (cumul)")
    ax1.set_xlabel("Année")
    ax1.set_title("France — NB-IoT : couverture opérateur ≫ projets métier documentés")
    ax1.set_xticks(years)
    ax1.grid(True, alpha=0.3)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    path = out / "nbiot_couverture_vs_projets_metier.png"
    _save(fig, path)
    return path


def plot_compare_lora_nbiot(root: Path, nbiot_q: dict[str, Any], out: Path) -> Path | None:
    lora_path = root / "data" / "processed" / "lora_users_france_analysis.json"
    if not lora_path.exists():
        return None
    lora = json.loads(lora_path.read_text(encoding="utf-8"))
    lora_annual = (lora.get("quantification") or {}).get("annual") or []
    if not lora_annual:
        return None
    years = YEARS
    lora_cumul = {r["year"]: r["cumul_projets_metier"] for r in lora_annual}
    nbiot_cumul = {r["year"]: r["cumul_projets_metier"] for r in nbiot_q["annual"]}
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.plot(years, [lora_cumul.get(y, 0) for y in years], "o-", color="#1f6f5b", lw=2.5, label="LoRa — cumul projets métier")
    ax.plot(years, [nbiot_cumul.get(y, 0) for y in years], "s-", color="#0b3d91", lw=2.5, label="NB-IoT — cumul projets métier")
    ax.set_title("France — Cumul projets métier documentés : LoRa vs NB-IoT")
    ax.set_xlabel("Année")
    ax.set_ylabel("Cumul projets métier (inventaire)")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    ax.axvline(2016, color="#1f6f5b", ls=":", lw=1)
    ax.text(2016.1, 2, "LoRa\nnational", fontsize=8, color="#1f6f5b")
    ax.axvline(2019, color="#0b3d91", ls=":", lw=1)
    ax.text(2019.1, 8, "NB-IoT\nSFR", fontsize=8, color="#0b3d91")
    path = out / "compare_lora_nbiot_projets_metier.png"
    _save(fig, path)
    return path


def build_report(data: dict[str, Any], q: dict[str, Any], figures: list[Path]) -> str:
    t = q["totals"]
    lines = [
        "# Quantification NB-IoT France — projets métier depuis 2015",
        "",
        data["meta"]["method_note"].strip(),
        "",
        "## Synthèse chiffrée (inventaire)",
        "",
        f"- Collectivités nommées : **{t['collectivites_nommees']}**",
        f"- Projets métier (total) : **{t['projets_metier']}** "
        f"(dont {t['projets_metier_collectivites']} collectivités + {t['projets_metier_anonymes']} anonyme)",
        f"- Sociétés inventoriées : **{t['societes']}**",
        f"- Objets documentés (somme projets chiffrés) : **{t['objets_documentes_cumul']:,}**".replace(",", " "),
        "",
        "### Faits nationaux",
        "",
    ]
    for f in q.get("national_facts") or []:
        lines.append(f"- {f}")

    lines += ["", "## Tendances", ""]
    for b in data["tendances_depuis_2015"]["resume"]:
        lines.append(f"- {b}")

    lines += [
        "",
        "## Croissance par période",
        "",
        "| Période | Début | Fin | Variation | Lecture |",
        "|---|---:|---:|---|---|",
    ]
    for p in q["growth_phases"]:
        var = "—" if p["variation_pct"] is None else f"{p['variation_pct']}%"
        lines.append(
            f"| {p['periode']} | {p['projets_metier_debut']} | {p['projets_metier_fin']} | "
            f"{var} | {p['lecture']} |"
        )

    lines += [
        "",
        "## Tableau annuel quantifié",
        "",
        "| Année | + projets métier | Cumul métier | Sociétés actives | Objets doc. cumul |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in q["annual"]:
        lines.append(
            f"| {r['year']} | {r['nouveaux_projets_metier']} | {r['cumul_projets_metier']} | "
            f"{r['societes_actives']} | {r['objets_documentes_cumul']:,} |".replace(",", " ")
        )

    lines += [
        "",
        "## Projets métier documentés",
        "",
        "| Projet / collectivité | Type | Début | Objets | Confiance |",
        "|---|---|---:|---:|---|",
    ]
    for c in _all_metier_projects(data):
        obj = c.get("objets_approx")
        obj_s = f"{int(obj):,}".replace(",", " ") if obj else "—"
        lines.append(
            f"| {c['name']} | {c.get('type','')} | {c.get('year_start','')} | "
            f"{obj_s} | {c.get('confidence','')} |"
        )

    lines += [
        "",
        "## Sociétés",
        "",
        "| Société | Rôle | Début | Note |",
        "|---|---|---:|---|",
    ]
    for s in sorted(data["societes"], key=lambda x: (x.get("year_start") or 9999, x["name"])):
        note = (s.get("note") or "").replace("|", "/")
        lines.append(f"| {s['name']} | {s.get('role','')} | {s.get('year_start','')} | {note} |")

    lines += ["", "## Graphiques", ""]
    for f in figures:
        lines.append(f"![{f.name}](figures/{f.name})")
        lines.append("")

    lines += [
        "## Limites",
        "",
        "- Inventaire **beaucoup plus mince** que LoRa pour les collectivités : biais réel du marché FR (eau = LoRa).",
        "- Couverture ~99 % pop. ≠ dizaines de projets smart city documentés.",
        "- Projets anonymes (SFR×Gutermann) inclus dans le cumul métier mais sans collectivité nommée.",
        "",
    ]
    return "\n".join(lines)


def run(root: Path) -> dict[str, Any]:
    data = load_yaml(root / "data" / "curated" / "nbiot_users_france.yaml")
    q = compute_quantification(data)
    fig_dir = root / "reports" / "figures"
    art_dir = Path("/opt/cursor/artifacts/figures")
    art_dir.mkdir(parents=True, exist_ok=True)

    figs: list[Path] = [
        plot_flux_cumul(q, fig_dir),
        plot_societes_actives(q, fig_dir),
        plot_tendances_index(q, fig_dir),
        plot_objets(q, fig_dir),
        plot_cover_vs_metier(data, q, fig_dir),
    ]
    cmp = plot_compare_lora_nbiot(root, q, fig_dir)
    if cmp:
        figs.append(cmp)

    for f in figs:
        (art_dir / f.name).write_bytes(f.read_bytes())

    report_path = root / "reports" / "nbiot_usagers_france_depuis_2015.md"
    report_path.write_text(build_report(data, q, figs), encoding="utf-8")

    out = {
        "quantification": q,
        "figures": [f.name for f in figs],
        "report": str(report_path),
    }
    (root / "data" / "processed" / "nbiot_users_france_analysis.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    result = run(Path(__file__).resolve().parents[2])
    q = result["quantification"]
    print(
        json.dumps(
            {
                "totals": q["totals"],
                "growth_phases": q["growth_phases"],
                "annual_tail": q["annual"][-6:],
                "figures": result["figures"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
