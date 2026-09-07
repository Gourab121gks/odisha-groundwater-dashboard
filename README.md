# 💧 Odisha Groundwater Quality & Decision Support System (DSS)

An advanced, research-grade hydrogeological and water quality analytics platform for the State of Odisha, India. Built with **Streamlit**, **Plotly**, and **GeoPandas**, synthesizing statewide groundwater monitoring data from the **Central Ground Water Board (CGWB)** and **Jal Jeevan Mission (JJM)**.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 10 Integrated Hydrogeological Modules

1. **🗺️ Aquifer & Basin GIS Map**: Multi-layer vector GIS mapping of 12 Principal Aquifer formations, 11 major River Basins, 1,081 river segments, and 772 monitoring stations.
2. **🏗️ CGWB Deep Aquifer Exploration**: Synthesis of CGWB's landmark report (*Oct 2024*) — 3,190 exploratory boreholes, coastal saline hazard geometry (8,875 sq. km across 42 blocks), deep freshwater horizons (120–350 m), and artesian auto-flow belts.
3. **🔬 CGWB Published Quality Year Book**: Official AAP 2024–25 survey (July 2025) — Pre/Post-monsoon recharge dilution dynamics, 8-year temporal trends (2017–2024), toxic heavy metals (Uranium, Lead, Arsenic, Fe, Mn), and 1,280 published station records.
4. **🧪 WQI Potability & Pipe Corrosivity**: Single-composite Weighted Arithmetic WQI scoring alongside Langelier Saturation Index (LSI) and Ryznar Stability Index (RSI) for pipe material selection.
5. **⚠️ Contamination & BIS Exceedances**: Hotspot quantification and health risk screening against Indian Drinking Water Standards (BIS IS 10500:2012).
6. **📊 Geochemical Facies Modeling**: Interactive Piper Trilinear, 9-field Extended Durov with pH/TDS integration, and Schoeller semi-logarithmic flowpath plots.
7. **🌾 Irrigation & Agronomic Quality**: Wilcox (%Na vs EC) and US Salinity Laboratory (USSL: SAR vs EC) agricultural suitability classifications.
8. **🗺️ Spatial IDW Plumes & 🧊 3D Profiler**: Continuous 2D Inverse Distance Weighting (IDW) contamination plume surfaces and interactive 3D subsurface depth stratigraphy (10–150 mbgl).
9. **🔬 Gibbs Ratios & Ionic Scatter**: Gibbs Boomerang I & II mechanisms (rock-water interaction vs evaporation) and customizable bivariate scatter with 1:1 equilines.
10. **🏛️ District Rankings & 📄 PDF Dossier**: Severity rankings across all 30 districts, one-click automated executive PDF report generator, and enriched CSV export.

---

## 🚀 One-Click Cloud Deployment (Streamlit Community Cloud)

1. Fork or clone this repository to your GitHub account.
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **New app**, select this repository and branch (`main`), set **Main file path** to `app.py`.
4. Click **Deploy!**

---

## 💻 Local Installation & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/odisha-groundwater-dashboard.git
cd odisha-groundwater-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

---

## 📊 Datasets & Sources
- **Central Ground Water Board (CGWB)**, Ministry of Jal Shakti, Government of India.
- *Ground Water Exploration in Odisha* (October 2024).
- *Groundwater Quality Year Book of Odisha State AAP 2024–25* (July 2025).
- Bureau of Indian Standards (BIS IS 10500:2012 Drinking Water Specifications).
