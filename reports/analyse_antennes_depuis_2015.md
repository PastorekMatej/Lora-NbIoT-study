# Antennes LoRaWAN vs capacité NB-IoT — France depuis 2015

Comparer des gateways LoRaWAN à des sites 4G n'est pas un comptage homogène :
un site 4G NB-IoT mutualise voix/data/IoT ; une antenne LoRa est dédiée LPWAN.
L'analyse porte sur la DYNAMIQUE (croissance/décroissance) et les ordres de grandeur.

## Tableau annuel

| Année | Orange LoRa | Objenious LoRa | Total LoRa public | Proxy NB-IoT (sites 4G) |
|---:|---:|---:|---:|---:|
| 2015 | 0 | 0 | 0 | 0 |
| 2016 | — | — | — | 0 |
| 2017 | 4 000 | 4 020 | 8 020 | 0 |
| 2018 | 4 500 | 4 300 | 8 800 | 0 |
| 2019 | 4 800 | 4 300 | 9 100 | 17 700 |
| 2020 | 4 800 | 4 300 | 9 100 | 20 000 |
| 2021 | 4 800 | 4 300 | 9 100 | 27 000 |
| 2022 | 4 800 | 4 300 | 9 100 | 78 193 |
| 2023 | 4 800 | 4 300 | 9 100 | 78 997 |
| 2024 | 4 800 | 4 300 | 9 100 | 84 521 |
| 2025 | 4 800 | 0 | 4 800 | 89 474 |
| 2026 | 4 800 | 0 | 4 800 | 93 516 |

## Tendances

### LoRaWAN (antennes dédiées)
- 2015–2019 : CROISSANCE forte (0 → ~9100 antennes publiques)
- 2019–2024 : PLATEAU duopole Orange+Objenious (~9100)
- 2025–2026 : DÉCROISSANCE brutale (-47%) après arrêt Objenious → ~4800

### NB-IoT (proxy sites 4G)
- 2015–2018 : NÉANT commercial FR (0 site NB-IoT actif)
- 2019–2021 : CROISSANCE (SFR puis début Bouygues)
- 2022–2026 : CROISSANCE continue de la densification 4G sous-jacente (+20% SFR+Bouygues 2022→2026)

## Graphiques

![phases_deploiement_antennes_2015.png](figures/phases_deploiement_antennes_2015.png)

![antennes_lora_depuis_2015.png](figures/antennes_lora_depuis_2015.png)

![antennes_nbiot_proxy_depuis_2015.png](figures/antennes_nbiot_proxy_depuis_2015.png)

![comparaison_antennes_lora_vs_nbiot_2015.png](figures/comparaison_antennes_lora_vs_nbiot_2015.png)
