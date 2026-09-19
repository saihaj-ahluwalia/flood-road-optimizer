# 🌊 AquaRoute AI — Flood Disaster Road Criticality & Evacuation Optimization Platform

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-blue?style=for-the-badge&logo=github)](https://saihaj-ahluwalia.github.io/flood-road-optimizer/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Leaflet.js](https://img.shields.io/badge/Leaflet.js-1.9.4-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0%2B-blueviolet?style=for-the-badge)](https://networkx.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> **AquaRoute AI** is an intelligent, physics-informed disaster decision-support platform designed for Emergency Operations Centers (EOC), municipal transit authorities, and first responders. It simulates urban flood inundation, predicts dynamic panic evacuation flows, isolates critical bridge bottlenecks, and computes a multi-factor **Road Criticality Score (RCS)** to prioritize emergency interventions (mobile pumps, sandbag barriers, contraflow corridors) across **Mumbai**, **Jakarta**, and **Houston**.

---

## 📸 Interactive Web Command Center

![AquaRoute AI Command Center](web/assets/preview.png)
*(Open `web/index.html` or `docs/index.html` locally or deploy directly via GitHub Pages)*

---

## 🌟 Why AquaRoute AI?

During catastrophic flood events (e.g. Mumbai's monsoon deluges, Jakarta's coastal *Banjir Rob*, Houston's Hurricane Harvey):
1. **Static navigation apps fail**: Google Maps or Waze route thousands of fleeing vehicles directly into 0.6m+ submerged arterial underpasses, causing massive gridlock and vehicle abandonment.
2. **First responders lack actionable prioritization**: Disaster commanders cannot easily determine which specific bridge or highway will cause a catastrophic network partition if left unprotected.
3. **AquaRoute AI solves this** via a 4-step mathematical simulation pipeline combining hydrology, topological graph theory, and dynamic traffic assignment.

---

## 🏛️ Supported Cities & Scenarios (9 Pre-Computed Scenarios)

| City | Country | Primary Hydrological Hazards | Precomputed Scenarios |
| :--- | :--- | :--- | :--- |
| **Mumbai** 🇮🇳 | India | Mithi River overtopping, Arabian Sea tidal surge, Hindmata/Kurla/Milan subway depressions | Mild (10-Yr), Moderate (50-Yr), Severe (100-Yr) |
| **Jakarta** 🇮🇩 | Indonesia | Land subsidence, Ciliwung River basin flooding, North Jakarta *Banjir Rob* coastal surge | Mild (10-Yr), Moderate (50-Yr), Severe (100-Yr) |
| **Houston** 🇺🇸 | USA | Hurricane Harvey-scale extreme pluvial deluge, Buffalo/White Oak/Brays bayou overtopping | Mild (10-Yr), Moderate (50-Yr), Severe (500-Yr) |

---

## 🔬 The 4-Step Simulation Engine

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     STEP 1      │     │     STEP 2      │     │     STEP 3      │     │     STEP 4      │
│  HAZARD LAYER   │ ──> │   FLOW FIELD    │ ──> │   BOTTLENECK    │ ──> │  ROAD SCORING   │
│ Inundation & DEM│     │ Evacuation Flow │     │ Detection & CVR │     │   & Mitigation  │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1. Step 1: Hazard Layer & Speed Degradation
- Integrates rainfall intensity ($R\text{ mm/hr}$), coastal storm surge ($S_{surge}\text{ m}$), and elevation above sea level ($z\text{ m}$):
  $$h(x,y) = \max\left(0, h_{base}(R) + S_{surge} \cdot e^{-d_{water}/\lambda} \cdot \text{ElevAdj}(z)\right)$$
- Non-linear vehicle speed degradation model:
  $$v_{eff}(e) = v_{max}(e) \cdot \max\left(0, 1 - \left(\frac{h_e}{h_{crit}}\right)^2\right)$$
  *(where $h_{crit} = 0.35\text{ m}$ for passenger cars and $0.60\text{ m}$ for emergency 4x4 vehicles)*

### 2. Step 2: Evacuation Flow Field & Dynamic Demand
- Generates origin centroids weighted by residential vulnerability and water depth.
- Solves multi-destination shortest-path cost minimization to designated emergency shelters subject to capacity constraints:
  $$Z(e) = t_{travel}(e) + \alpha \cdot (h_e)^{\beta}$$

### 3. Step 3: Capacity vs Volume Bottleneck Detection
- Evaluates Capacity-to-Volume Ratio ($CVR = \frac{F_e}{\text{Cap}_e}$).
- Isolates single-point-of-failure bridges and computes topological degree loss ($I_{cutoff}$) when submerged links fail.

### 4. Step 4: Multi-Criteria Road Criticality Scoring (RCS)
- Computes a unified 0–100 Criticality Index:
  $$RCS(e) = w_1 \cdot C_B(e) + w_2 \cdot \min(2.5, CVR(e)) + w_3 \cdot V(e) + w_4 \cdot I_{cutoff}(e)$$
  * **Tier 1 (Critical Lifeline, RCS $\ge 75$)**: Immediate Sandbag Barriers & Mobile Dewatering Pumps.
  * **Tier 2 (High Priority, $55 \le RCS < 75$)**: Traffic Contraflow & Outbound Redirection.
  * **Tier 3 (Moderate, $35 \le RCS < 55$)**: Dynamic Signage Warning & Patrol.
  * **Tier 4 (Resilient, $RCS < 35$)**: Normal Operations.

---

## 💻 Tech Stack

- **Backend**: Python 3.10+, NetworkX (graph algorithms), NumPy, SciPy (spatial math), Requests, Matplotlib.
- **Frontend**: Vanilla JavaScript (ES6+), Leaflet.js (v1.9.4), Chart.js (v4.4.1), Lucide Icons, html2pdf.js.
- **Architecture**: **Path 2.5 Hybrid** (Full Python simulation engine + pre-computed static JSON scenarios for instant GitHub Pages hosting).

---

## 📁 Repository Structure

```
flood-road-optimizer/
│
├── .github/
│   └── workflows/
│       └── gh-pages.yml          # GitHub Actions auto-deployment
│
├── data/
│   ├── raw/                      # OSM & elevation cache
│   └── scenarios/                # 9 Pre-computed scenario JSON files
│       ├── mumbai_mild.json, mumbai_moderate.json, mumbai_severe.json
│       ├── jakarta_mild.json, jakarta_moderate.json, jakarta_severe.json
│       └── houston_mild.json, houston_moderate.json, houston_severe.json
│
├── src/                          # Real Python Simulation Engine
│   ├── __init__.py
│   ├── config.py                 # City bounding boxes, shelters, scenarios
│   ├── osm_fetcher.py            # Overpass API & topological graph builder
│   ├── step1_hazard.py           # Inundation depth & DEM generator
│   ├── step2_flow_field.py       # Evacuation demand & flow accumulation
│   ├── step3_bottlenecks.py      # CVR & choke point detector
│   ├── step4_road_scoring.py     # RCS scoring & actionable interventions
│   ├── pipeline.py               # 4-step pipeline orchestrator
│   └── export_geojson.py         # Web GeoJSON serializer
│
├── web/                          # High-Tech Interactive Web Dashboard
│   ├── index.html                # Main EOC Command Center
│   ├── css/style.css             # Glassmorphism dark-slate styling
│   ├── js/
│   │   ├── app.js                # State coordinator & UI manager
│   │   ├── map.js                # Leaflet map & layers manager
│   │   ├── charts.js             # Real-time Chart.js analytics
│   │   ├── intervention.js       # What-If mitigation sandbox
│   │   └── layers/               # Hazard, Roads, Bottlenecks, Shelters, Flows
│   └── data/                     # Web scenario JSON mirror
│
├── notebooks/
│   └── flood_road_optimization_walkthrough.ipynb # Step-by-step Jupyter Notebook
│
├── tests/
│   └── test_pipeline.py          # Automated verification test suite
│
├── scripts/
│   ├── run_all_scenarios.py      # CLI batch runner
│   └── serve_local.py            # Local zero-config web server
│
├── docs/                         # GitHub Pages static mirror
├── index.html                    # Root web entrypoint
├── requirements.txt              # Dependencies
└── README.md
```

---

## ⚡ Quickstart Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/saihaj-ahluwalia/flood-road-optimizer.git
cd flood-road-optimizer
pip install -r requirements.txt
```

### 2. Launch Local Interactive Web Command Center
```bash
python scripts/serve_local.py
```
Open **`http://localhost:8000/web/index.html`** in your browser!

### 3. Run a New Simulation Scenario via CLI
```bash
# Syntax: python -m src.pipeline <city_id> <scenario>
# Example: Run Severe Catastrophic Deluge for Mumbai
python -m src.pipeline mumbai severe

# Example: Run Moderate Scenario for Houston
python -m src.pipeline houston moderate
```

### 4. Run Automated Test Suite
```bash
python -m unittest tests/test_pipeline.py
```

### 5. Explore Jupyter Notebook
```bash
jupyter notebook notebooks/flood_road_optimization_walkthrough.ipynb
```

---

## 🎛️ Interactive Dashboard Features

1. **City & Scenario Switcher**: Toggle seamlessly between Mumbai, Jakarta, and Houston across Mild, Moderate, and Severe flood events.
2. **Dynamic Layer Toggles**:
   - 🌊 **Flood Hazard Depth Grid**: Color-coded water depth heatmap ($0.1\text{m}$ to $2.0\text{m}+$ with elevation tooltips).
   - 🛣️ **Road Criticality Network**: Interactive color-coded polylines (Green, Yellow, Orange, Pulsing Red).
   - ⚠️ **Bottleneck & Choke Points**: Pulsing alert markers highlighting single-point-of-failure bridges.
   - 🛡️ **Emergency Shelters**: Active safe hubs with capacity gauges.
   - ⚡ **Evacuation Flow Corridors**: Animated directional flow arrows.
3. **Road Inspector Card**: Click any road on the map to inspect its RCS score, flood depth, operating speed, and recommended action.
4. **What-If Mitigation Sandbox**: Test deploying high-capacity mobile pumps ($3,000\text{ m}^3\text{/h}$), inflatable flood barriers, or 2-lane contraflows in real-time.
5. **EOC Intelligence PDF Briefing**: 1-click generation of professional incident intelligence reports for field commanders.

---

## 🌐 Deploying to GitHub Pages

1. Push this repository to GitHub under your account:
   ```bash
   git init
   git add .
   git commit -m "feat: Initial AquaRoute AI release"
   git remote add origin https://github.com/saihaj-ahluwalia/flood-road-optimizer.git
   git branch -M main
   git push -u origin main
   ```
2. In your GitHub repository settings:
   - Navigate to **Settings** ➔ **Pages**.
   - Under **Build and deployment** ➔ **Source**, select **GitHub Actions** (the included `.github/workflows/gh-pages.yml` will automatically deploy the site) or select **Deploy from a branch** (`main` / `docs` folder).
3. Your live dashboard is now live at: `https://saihaj-ahluwalia.github.io/flood-road-optimizer/`

---

## 🤝 Contributing & License

Built with ❤️ for disaster resilience and emergency logistics optimization.
Distributed under the **MIT License**.
Developed by **Saihaj Ahluwalia** (`saihaj-ahluwalia`).
