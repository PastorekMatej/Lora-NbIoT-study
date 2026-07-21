# Étude comparative LoRaWAN vs NB-IoT — France

Pipeline open-source pour une étude **quantitative et qualitative** du déploiement LPWAN en France, basée sur des **données réelles** (APIs + open data + sources opérateurs sourcées).

## Résultats clés (collecte du 2026-07-21)

| Dimension | LoRaWAN | NB-IoT |
|---|---|---|
| Opérateurs nationaux publics | **Orange** (seul après arrêt Objenious fin 2024) | **SFR** + **Bouygues** (Orange non positionné FR) |
| Couverture pop. déclarée | ~**95 %** (Orange) | ~**99 %** (SFR / Bouygues) |
| Infrastructure dédiée | ~**4 800** antennes Orange | Mutualisée sur RAN **4G** (in-band) |
| Communautaire mesuré | **2 734** GW Packet Broker FR (dont **413** online) | n/a |
| Helium IoT (estim.) | ~**11 869** hotspots FR (échantillon) | n/a |
| Tendance 2024–2026 | Consolidation + réseaux privés | Accélération (sunset 2G/3G) |

Rapport généré : [`reports/etude_comparative_lora_nbiot_france.md`](reports/etude_comparative_lora_nbiot_france.md)

## Sources de données

### Mesurées (API / open data)

| Source | Contenu | Script |
|---|---|---|
| [Packet Broker Mapper](https://mapper.packetbroker.net/api/v2/gateways) | Gateways LoRaWAN fédérés (TTN/TTS…) | `src/collectors/packetbroker.py` |
| [Helium Entity API](https://entities.nft.helium.io/v2/hotspots) | Hotspots Helium IoT | `src/collectors/helium.py` |
| [Arcep — Mon Réseau Mobile](https://data.arcep.fr/mobile/sites/) | Sites 2G/3G/4G/5G (proxy densification cellulaire) | `src/collectors/arcep_sites.py` |

### Contours géographiques

- `data/curated/france_regions.geojson` — polygones régions (filtre point-in-polygon)

### Déclaratives / marché (curated YAML)

- Couverture opérateurs : `data/curated/operator_coverage_france.yaml`
- Chronologie & axes qualitatifs : `data/curated/timeline_france.yaml`
- GSMA Mobile IoT launches, IoT Analytics LPWAN 2024, communiqués Orange / Objenious

> **Limite importante** : l'Arcep ne publie pas de couches NB-IoT / LTE-M / LoRaWAN. Les % population sont des déclarations opérateurs.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Moulinettes

### Pipeline complet

```bash
python -m scripts.run_study --collect --spatial --analyze --report
```

### Options

```bash
# Réanalyse sans re-télécharger
python -m scripts.run_study --analyze --report

# Collecte ciblée
python -m scripts.run_study --collect --skip-helium --analyze --report
python -m scripts.run_study --collect --helium-pages 20 --analyze --report
```

### Collecteurs individuels

```bash
python -m src.collectors.packetbroker
python -m src.collectors.helium
python -m src.collectors.arcep_sites
```

## Structure

```
data/
  curated/     # YAML sourcés (couverture, timeline, axes qualitatifs)
  raw/         # JSON/CSV bruts (APIs, Arcep)
  processed/   # Agrégats + comparative_analysis.json
src/
  collectors/  # Automates de collecte
  analysis/    # KPI, comparatif, graphiques, rapport MD
scripts/
  run_study.py # CLI unique
reports/       # Rapport + figures
```

## Méthodologie

1. **Quantitatif** : densités d'infrastructure (gateways LoRa, sites 4G Arcep), couverture déclarée, parts de marché LPWAN (IoT Analytics).
2. **Qualitatif** : spectre, indoor, roaming, risque écosystème, cas d'usage, chronologie des bascules (Objenious, sunset 2G/3G).
3. **Triangulation** : croisement déclarations opérateurs × APIs communautaires × open data régulateur.

## Extensions possibles

- Cartographie Folium / GeoJSON des gateways Packet Broker par département
- Scraping / archivage périodique des cartes de couverture opérateurs (SFR, Bouygues)
- Intégration mesures crowdsourcing Arcep (qualité) comme proxy indoor cellulaire
- Panel d'entretiens opérateurs / intégrateurs (volet qualitatif enrichi)
