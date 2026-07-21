"""Analyse croisée projets métier LoRa vs NB-IoT — France depuis 2015 + audit fiabilité."""

from __future__ import annotations

import json
from collections import Counter
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
    if c.get("reliability_status") == "couverture_seule":
        return False
    uses = set(c.get("use_cases") or [])
    return bool(uses - {"couverture_operateur"})


def _year_metier(c: dict[str, Any]) -> int | None:
    y = c.get("year_projet_metier") or c.get("year_start")
    return int(y) if y is not None else None


def extract_projects(data: dict[str, Any], tech: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for c in data.get("collectivites") or []:
        if not _is_metier(c):
            continue
        if c.get("reliability_status") == "annonce_non_confirmee":
            # keep for audit list but mark
            pass
        y = _year_metier(c)
        if y is None or y < 2015:
            continue
        items.append(
            {
                "tech": tech,
                "name": c["name"],
                "year": y,
                "confidence": c.get("confidence"),
                "reliability_status": c.get("reliability_status"),
                "include_in_fiable": bool(c.get("include_in_fiable")),
                "objets": c.get("objets_approx"),
                "objets_year": int(c["objets_year"]) if c.get("objets_year") else y,
                "use_cases": c.get("use_cases") or [],
                "excluded": c.get("reliability_status") == "annonce_non_confirmee",
            }
        )
    for p in data.get("projets_metier_anonymes") or []:
        y = _year_metier(p)
        if y is None:
            continue
        items.append(
            {
                "tech": tech,
                "name": p["name"],
                "year": y,
                "confidence": p.get("confidence"),
                "reliability_status": p.get("reliability_status") or "claim_operateur",
                "include_in_fiable": bool(p.get("include_in_fiable")),
                "objets": p.get("objets_approx"),
                "objets_year": int(p.get("objets_year") or y),
                "use_cases": p.get("use_cases") or [],
                "excluded": False,
                "anonyme": True,
            }
        )
    return items


def series_from_projects(projects: list[dict[str, Any]], fiable_only: bool) -> list[dict[str, Any]]:
    new = Counter()
    objets_new = Counter()
    for p in projects:
        if p.get("excluded"):
            continue
        if fiable_only and not p.get("include_in_fiable"):
            continue
        new[p["year"]] += 1
        if p.get("objets"):
            objets_new[p["objets_year"]] += int(p["objets"])

    rows = []
    cumul = cumul_obj = 0
    for y in YEARS:
        cumul += new[y]
        cumul_obj += objets_new[y]
        prev = rows[-1]["cumul"] if rows else 0
        growth = None if prev == 0 else round(100.0 * (cumul - prev) / prev, 1)
        rows.append(
            {
                "year": y,
                "nouveaux": new[y],
                "cumul": cumul,
                "croissance_pct": growth,
                "objets_nouveaux": objets_new[y],
                "objets_cumul": cumul_obj,
            }
        )
    return rows


def plot_cross_cumul(lora_d: list, lora_f: list, nb_d: list, nb_f: list, out: Path) -> Path:
    years = YEARS
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.plot(years, [r["cumul"] for r in lora_d], "o-", color="#1f6f5b", lw=2.2, label="LoRa documenté")
    ax.plot(years, [r["cumul"] for r in lora_f], "o--", color="#66bb6a", lw=2.0, label="LoRa fiable (high)")
    ax.plot(years, [r["cumul"] for r in nb_d], "s-", color="#0b3d91", lw=2.2, label="NB-IoT documenté")
    ax.plot(years, [r["cumul"] for r in nb_f], "s--", color="#64b5f6", lw=2.0, label="NB-IoT fiable (high)")
    ax.axvline(2016, color="#1f6f5b", ls=":", lw=1)
    ax.text(2016.05, 1, "LoRa\nnational", fontsize=7, color="#1f6f5b")
    ax.axvline(2019, color="#0b3d91", ls=":", lw=1)
    ax.text(2019.05, 4, "SFR\nNB-IoT", fontsize=7, color="#0b3d91")
    ax.axvline(2024, color="#a00", ls=":", lw=1)
    ax.text(2024.05, 10, "Fin\nObjenious\nLoRa", fontsize=7, color="#a00")
    ax.set_title("France — Cumul projets métier LoRa vs NB-IoT (documenté / fiable)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Cumul projets métier")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    path = out / "croise_projets_metier_cumul_lora_nbiot.png"
    _save(fig, path)
    return path


def plot_cross_flux(lora_d: list, nb_d: list, out: Path) -> Path:
    years = YEARS
    fig, ax = plt.subplots(figsize=(12, 5.2))
    w = 0.35
    ax.bar([y - w / 2 for y in years], [r["nouveaux"] for r in lora_d], width=w, color="#1f6f5b", label="LoRa nouveaux")
    ax.bar([y + w / 2 for y in years], [r["nouveaux"] for r in nb_d], width=w, color="#0b3d91", label="NB-IoT nouveaux")
    ax.set_title("France — Flux annuel de projets métier documentés (LoRa vs NB-IoT)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Nouveaux projets / an")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(loc="upper left")
    path = out / "croise_projets_metier_flux_lora_nbiot.png"
    _save(fig, path)
    return path


def plot_objets_cross(lora_d: list, nb_d: list, out: Path) -> Path:
    years = YEARS
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.plot(years, [r["objets_cumul"] for r in lora_d], "o-", color="#1f6f5b", lw=2.5, label="LoRa objets doc. cumul")
    ax.plot(years, [r["objets_cumul"] for r in nb_d], "s-", color="#0b3d91", lw=2.5, label="NB-IoT objets doc. cumul")
    ax.set_yscale("log")
    ax.set_title("France — Objets documentés cumulés (projets métier, échelle log)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Objets (cumul)")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(loc="upper left")
    ax.text(0.02, 0.05, "NB: objets = somme des projets chiffrés (sous-estime le parc réel)", transform=ax.transAxes, fontsize=7)
    path = out / "croise_objets_documentes_lora_nbiot.png"
    _save(fig, path)
    return path


def plot_reliability_bars(lora_p: list, nb_p: list, out: Path) -> Path:
    def bucket(ps):
        c = Counter()
        for p in ps:
            if p.get("excluded"):
                c["exclu / non confirmé"] += 1
            elif p.get("include_in_fiable"):
                c["fiable (high)"] += 1
            else:
                c["documenté non-high"] += 1
        return c

    lb, nb = bucket(lora_p), bucket(nb_p)
    cats = ["fiable (high)", "documenté non-high", "exclu / non confirmé"]
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    x = range(len(cats))
    ax.bar([i - 0.18 for i in x], [lb[c] for c in cats], width=0.36, color="#1f6f5b", label="LoRa")
    ax.bar([i + 0.18 for i in x], [nb[c] for c in cats], width=0.36, color="#0b3d91", label="NB-IoT")
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats)
    ax.set_ylabel("Nombre de projets")
    ax.set_title("France — Fiabilité des projets métier inventoriés")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    path = out / "croise_fiabilite_projets_metier.png"
    _save(fig, path)
    return path


def plot_index_cross(lora_f: list, nb_f: list, out: Path) -> Path:
    years = YEARS
    def norm(rows):
        vals = [r["cumul"] for r in rows]
        m = max(vals) or 1
        return [100 * v / m for v in vals]

    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.plot(years, norm(lora_f), "o-", color="#1f6f5b", lw=2.5, label="LoRa fiable (index)")
    ax.plot(years, norm(nb_f), "s-", color="#0b3d91", lw=2.5, label="NB-IoT fiable (index)")
    ax.set_ylim(0, 110)
    ax.set_title("France — Tendance projets métier FIABLES (index 100 = max de chaque série)")
    ax.set_xlabel("Année")
    ax.set_ylabel("Index")
    ax.set_xticks(years)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    path = out / "croise_tendances_index_fiable.png"
    _save(fig, path)
    return path


def build_report(
    lora_p: list,
    nb_p: list,
    lora_d: list,
    lora_f: list,
    nb_d: list,
    nb_f: list,
    audits: dict[str, Any],
    figures: list[Path],
) -> str:
    def n_fiable(ps):
        return sum(1 for p in ps if p.get("include_in_fiable") and not p.get("excluded"))

    def n_doc(ps):
        return sum(1 for p in ps if not p.get("excluded"))

    lines = [
        "# Croisement projets métier LoRa vs NB-IoT — France depuis 2015",
        "",
        "## Méthode & fiabilité",
        "",
        "- **Projet métier** = usage concret documenté (pas la seule couverture radio).",
        "- **Documenté** = inventaire nominatif sourcé, hors annonces non confirmées.",
        "- **Fiable** = `confidence: high` + `include_in_fiable: true` (REX collectivité / sources fortes).",
        "- Inventaires **non exhaustifs** : la tendance mesure l’échantillon documenté.",
        "",
        "### Décisions d’audit (2026-07-21)",
        "",
        f"- LoRa : {audits.get('lora', {})}",
        f"- NB-IoT : {audits.get('nbiot', {})}",
        "",
        "## Synthèse croisée",
        "",
        "| Techno | Documentés | Fiables (high) | Objets doc. cumul |",
        "|---|---:|---:|---:|",
        f"| LoRa | {n_doc(lora_p)} | {n_fiable(lora_p)} | {lora_d[-1]['objets_cumul']:,} |".replace(",", " "),
        f"| NB-IoT | {n_doc(nb_p)} | {n_fiable(nb_p)} | {nb_d[-1]['objets_cumul']:,} |".replace(",", " "),
        "",
        "## Tendances (cumul documenté)",
        "",
        "| Année | LoRa + | LoRa cumul | NB-IoT + | NB-IoT cumul | LoRa fiable cumul | NB-IoT fiable cumul |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for i, y in enumerate(YEARS):
        lines.append(
            f"| {y} | {lora_d[i]['nouveaux']} | {lora_d[i]['cumul']} | "
            f"{nb_d[i]['nouveaux']} | {nb_d[i]['cumul']} | "
            f"{lora_f[i]['cumul']} | {nb_f[i]['cumul']} |"
        )

    lines += [
        "",
        "### Lecture des tendances",
        "",
        "- **2015–2018** : LoRa ouvre des projets métier (pilotes puis métropoles) ; NB-IoT = **0** (pas encore commercial FR).",
        "- **2019–2021** : LoRa continue (départements, smart city) ; NB-IoT = lancement opérateurs + écosystème, **toujours 0 projet métier fiable**.",
        "- **2022–2026** : LoRa reste dominant en projets documentés ; NB-IoT n’apparaît qu’avec **peu de cas eau/fuites** (1 fiable : Montluçon).",
        "- **Écart structurel** : couverture NB-IoT dense ≠ projets collectivités ; l’eau FR reste surtout LoRa/Birdz.",
        "",
        "## Tableaux de fiabilité",
        "",
        "### LoRa — projets métier",
        "",
        "| Année | Projet | Fiable | Statut | Objets |",
        "|---:|---|---|---|---:|",
    ]
    for p in sorted(lora_p, key=lambda x: (x["year"], x["name"])):
        fi = "oui" if p.get("include_in_fiable") else "non"
        obj = f"{int(p['objets']):,}".replace(",", " ") if p.get("objets") else "—"
        lines.append(
            f"| {p['year']} | {p['name']} | {fi} | {p.get('reliability_status','')} | {obj} |"
        )

    lines += [
        "",
        "### NB-IoT — projets métier",
        "",
        "| Année | Projet | Fiable | Statut | Objets |",
        "|---:|---|---|---|---:|",
    ]
    for p in sorted(nb_p, key=lambda x: (x["year"], x["name"])):
        fi = "oui" if p.get("include_in_fiable") and not p.get("excluded") else "non"
        obj = f"{int(p['objets']):,}".replace(",", " ") if p.get("objets") else "—"
        mark = " ⚠️" if p.get("excluded") else ""
        lines.append(
            f"| {p['year']} | {p['name']}{mark} | {fi} | {p.get('reliability_status','')} | {obj} |"
        )

    lines += [
        "",
        "## Points de vérification clés",
        "",
        "| Claim | Verdict | Preuve |",
        "|---|---|---|",
        "| Montpellier 50k LoRaWAN | **Confirmé** | Smart City Mag + témoignage métropole |",
        "| Montluçon 390 NB-IoT | **Confirmé** | Aquagir/BdT citation directe |",
        "| SFR×Gutermann 5000 NB-IoT | **Documenté, non localisé** | JDN Valérie Grau (SFR) — collectivité anonyme |",
        "| Lyon 6000 NB-IoT | **Non retenu (faible)** | EIN « prochainement » ; historique 2015 = radio Homerider |",
        "| Couverture NB-IoT ~99% pop. | **Couverture ≠ projets** | CP opérateurs |",
        "",
        "## Graphiques",
        "",
    ]
    for f in figures:
        lines.append(f"![{f.name}](figures/{f.name})")
        lines.append("")

    lines += [
        "## Limites",
        "",
        "- Pas de registre national Arcep des projets LPWAN.",
        "- Sous-dénombrement probable (surtout NB-IoT industriel / tracking non public).",
        "- Les objets chiffrés ne couvrent qu’une partie des projets.",
        "",
    ]
    return "\n".join(lines)


def run(root: Path) -> dict[str, Any]:
    lora_data = load_yaml(root / "data" / "curated" / "lora_users_france.yaml")
    nbiot_data = load_yaml(root / "data" / "curated" / "nbiot_users_france.yaml")

    lora_p = extract_projects(lora_data, "lora")
    nb_p = extract_projects(nbiot_data, "nbiot")

    lora_d = series_from_projects(lora_p, fiable_only=False)
    lora_f = series_from_projects(lora_p, fiable_only=True)
    nb_d = series_from_projects(nb_p, fiable_only=False)
    nb_f = series_from_projects(nb_p, fiable_only=True)

    fig_dir = root / "reports" / "figures"
    art_dir = Path("/opt/cursor/artifacts/figures")
    art_dir.mkdir(parents=True, exist_ok=True)

    figs = [
        plot_cross_cumul(lora_d, lora_f, nb_d, nb_f, fig_dir),
        plot_cross_flux(lora_d, nb_d, fig_dir),
        plot_objets_cross(lora_d, nb_d, fig_dir),
        plot_reliability_bars(lora_p, nb_p, fig_dir),
        plot_index_cross(lora_f, nb_f, fig_dir),
    ]
    for f in figs:
        (art_dir / f.name).write_bytes(f.read_bytes())

    audits = {
        "lora": lora_data.get("reliability_audit"),
        "nbiot": nbiot_data.get("reliability_audit"),
    }
    report_path = root / "reports" / "croisement_projets_metier_lora_nbiot.md"
    report_path.write_text(
        build_report(lora_p, nb_p, lora_d, lora_f, nb_d, nb_f, audits, figs),
        encoding="utf-8",
    )

    out = {
        "totals": {
            "lora_documente": sum(1 for p in lora_p if not p.get("excluded")),
            "lora_fiable": sum(1 for p in lora_p if p.get("include_in_fiable") and not p.get("excluded")),
            "nbiot_documente": sum(1 for p in nb_p if not p.get("excluded")),
            "nbiot_fiable": sum(1 for p in nb_p if p.get("include_in_fiable") and not p.get("excluded")),
            "lora_objets_doc": lora_d[-1]["objets_cumul"],
            "nbiot_objets_doc": nb_d[-1]["objets_cumul"],
        },
        "series": {
            "lora_documente": lora_d,
            "lora_fiable": lora_f,
            "nbiot_documente": nb_d,
            "nbiot_fiable": nb_f,
        },
        "projects": {"lora": lora_p, "nbiot": nb_p},
        "figures": [f.name for f in figs],
        "report": str(report_path),
        "audits": audits,
    }
    (root / "data" / "processed" / "croisement_projets_metier.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # refresh nbiot analysis objets after Lyon exclusion
    return out


if __name__ == "__main__":
    result = run(Path(__file__).resolve().parents[2])
    print(json.dumps({
        "totals": result["totals"],
        "lora_cumul_tail": result["series"]["lora_documente"][-4:],
        "nbiot_cumul_tail": result["series"]["nbiot_documente"][-4:],
        "nbiot_fiable_tail": result["series"]["nbiot_fiable"][-4:],
        "figures": result["figures"],
    }, indent=2, ensure_ascii=False))
