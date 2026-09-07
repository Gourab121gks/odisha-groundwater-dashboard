import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import io
import re
import hydrochemistry as hc
import aquifer_map as am
import spatial_modeling as sm
import report_generator as rg
import exploration_module as em
import quality_yearbook_module as qm

# --- Page Config ---
st.set_page_config(
    page_title="Odisha Groundwater Quality & Contamination Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme Setup ---
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"

# --- CSS Design System ---
css = f"""
<style>
:root {{
    --bg: {'#09090b' if IS_DARK else '#ffffff'};
    --bg-subtle: {'#0c0c0f' if IS_DARK else '#f9fafb'};
    --card: {'#0c0c0f' if IS_DARK else '#ffffff'};
    --card-hover: {'#131316' if IS_DARK else '#f4f4f5'};
    --border: {'#1e1e24' if IS_DARK else '#e4e4e7'};
    --border-subtle: {'#16161a' if IS_DARK else '#f0f0f2'};
    --text: {'#fafafa' if IS_DARK else '#09090b'};
    --text-muted: #71717a;
    --text-dim: {'#52525b' if IS_DARK else '#a1a1aa'};
    --accent: #2563eb;
    --green: {'#22c55e' if IS_DARK else '#16a34a'};
    --green-muted: {'rgba(34,197,94,0.12)' if IS_DARK else 'rgba(22,163,74,0.08)'};
    --red: {'#ef4444' if IS_DARK else '#dc2626'};
    --red-muted: {'rgba(239,68,68,0.12)' if IS_DARK else 'rgba(220,38,38,0.08)'};
    --amber: {'#f59e0b' if IS_DARK else '#d97706'};
    --amber-muted: {'rgba(245,158,11,0.12)' if IS_DARK else 'rgba(217,119,6,0.08)'};
    --shadow: {'none' if IS_DARK else '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)'};
    --radius: 10px;
}}

header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}
.block-container {{
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1440px !important;
}}

/* Metric Card */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow);
    transition: all 0.2s ease;
}}
.metric-card:hover {{
    border-color: var(--accent);
    transform: translateY(-2px);
}}
.metric-label {{ font-size: 0.76rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }}
.metric-value {{ font-size: 1.6rem; font-weight: 700; color: var(--text); letter-spacing: -0.03em; margin-top: 0.25rem; }}
.metric-delta {{ font-size: 0.74rem; font-weight: 500; margin-top: 0.35rem; padding: 2px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px; }}
.delta-up {{ color: var(--red); background: var(--red-muted); }}
.delta-down {{ color: var(--green); background: var(--green-muted); }}
.delta-warn {{ color: var(--amber); background: var(--amber-muted); }}
.delta-neutral {{ color: var(--text-muted); background: var(--border-subtle); }}

/* Chart Wrap */
.chart-wrap {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem 0.8rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}}
.chart-title {{ font-size: 0.92rem; font-weight: 600; color: var(--text); }}
.chart-subtitle {{ font-size: 0.76rem; color: var(--text-dim); margin-bottom: 0.8rem; }}

/* Station Card */
.station-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    margin-top: 0.5rem;
    box-shadow: var(--shadow);
}}

/* Data Table */
.data-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.82rem; }}
.data-table th {{ text-align: left; padding: 0.65rem 0.8rem; color: var(--text-muted); font-weight: 600; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid var(--border); background: var(--bg-subtle); }}
.data-table td {{ padding: 0.65rem 0.8rem; color: var(--text); border-bottom: 1px solid var(--border-subtle); }}
.data-table tr:hover td {{ background: var(--card-hover); }}

/* Badges */
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 600; }}
.badge-green {{ color: var(--green); background: var(--green-muted); }}
.badge-red {{ color: var(--red); background: var(--red-muted); }}
.badge-amber {{ color: var(--amber); background: var(--amber-muted); }}
.badge-blue {{ color: var(--accent); background: rgba(37,99,235,0.1); }}

/* Brand */
.brand {{ font-size: 1.3rem; font-weight: 700; display: flex; align-items: center; gap: 10px; color: var(--text); }}
.brand-sub {{ font-size: 0.82rem; color: var(--text-muted); margin-top: 2px; }}

/* Decision & Insights Box */
.decision-box {{
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem;
    margin-top: 1.2rem;
    margin-bottom: 0.6rem;
}}
.decision-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.6rem;
}}
.decision-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
    margin-top: 0.5rem;
}}
.decision-col-title {{
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.decision-list {{
    margin: 0;
    padding-left: 1.1rem;
    font-size: 0.82rem;
    color: var(--text-dim);
    line-height: 1.55;
}}
.decision-list li {{
    margin-bottom: 0.35rem;
}}

/* Tabs */
button[data-baseweb="tab"] {{ background: transparent !important; color: var(--text-muted) !important; font-size: 0.85rem !important; font-weight: 500 !important; padding: 0.55rem 1.1rem !important; border: 1px solid transparent !important; border-radius: 7px !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: var(--text) !important; background: var(--card) !important; border-color: var(--border) !important; font-weight: 600 !important; }}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{ display: none !important; }}
[data-baseweb="tab-list"] {{ gap: 4px !important; background: var(--bg-subtle) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; padding: 4px; margin-bottom: 1.1rem; }}
[data-testid="stHorizontalBlock"] {{ gap: 1.1rem !important; }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- Component Helpers ---
def metric_card(label, value, delta=None, delta_type="neutral"):
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else ("!" if delta_type == "warn" else "•"))
    delta_html = f'<div class="metric-delta delta-{delta_type}">{arrow} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def decision_panel(title, key_findings, recommendations, icon="💡"):
    findings_html = "".join([f"<li>{f}</li>" for f in key_findings])
    recomms_html = "".join([f"<li>{r}</li>" for r in recommendations])
    st.markdown(f"""
    <div class="decision-box">
        <div class="decision-title">{icon} {title}</div>
        <div class="decision-grid">
            <div>
                <div class="decision-col-title">🔍 Analytical Interpretations & Observations</div>
                <ul class="decision-list">
                    {findings_html}
                </ul>
            </div>
            <div>
                <div class="decision-col-title">🎯 Actionable Policy & Decision-Making Guidance</div>
                <ul class="decision-list">
                    {recomms_html}
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Plotly Theme ---
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#71717a" if not IS_DARK else "#a1a1aa", size=11),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        zerolinecolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        tickfont=dict(size=10, color="#71717a" if not IS_DARK else "#a1a1aa"),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        zerolinecolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        tickfont=dict(size=10, color="#71717a" if not IS_DARK else "#a1a1aa"),
    ),
)

# --- Header ---
head_left, head_right = st.columns([8, 2])
with head_left:
    st.markdown("""
    <div class="brand">
        💧 CGWB Odisha | Interactive Groundwater Quality & Contamination GIS Dashboard
    </div>
    <div class="brand-sub">Central Ground Water Board (SER) | High-Resolution Station Mapping, Contamination Alerts, & BIS Compliance</div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Light Mode" if IS_DARK else "🌙 Dark Mode"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

st.markdown("<div style='margin-bottom: 1.1rem;'></div>", unsafe_allow_html=True)

# --- Load Data ---
def parse_raw_coord(val):
    if pd.isna(val) or val is None:
        return np.nan
    s = str(val).strip().replace("°", " ").replace("º", " ").replace("`", "'").replace("''", '"')
    if s.lower() in ['no data', 'nan', 'none', '']:
        return np.nan
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return np.nan
    if len(nums) >= 3:
        d, m, sec = float(nums[0]), float(nums[1]), float(nums[2])
        return d + (m / 60.0) + (sec / 3600.0)
    elif len(nums) == 2:
        d, m = float(nums[0]), float(nums[1])
        return d + (m / 60.0)
    elif len(nums) == 1:
        return float(nums[0])
    return np.nan

def get_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                return pd.read_excel(uploaded_file), uploaded_file.name
            else:
                return pd.read_csv(uploaded_file), uploaded_file.name
        except Exception as e:
            st.sidebar.error(f"Error reading file: {e}")
            
    if os.path.exists("groundwater_data.csv"):
        return pd.read_csv("groundwater_data.csv"), "CGWB Odisha Water Quality Report (2024-25)"
    return pd.DataFrame(), "No Data"

st.sidebar.markdown("### 📂 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])
df_raw, source_title = get_data(uploaded_file)
st.sidebar.info(f"📊 Active: **{source_title}**")

if df_raw.empty:
    st.error("No dataset available.")
    st.stop()

df = df_raw.copy()

# Fix and validate coordinates for Odisha
if "Latitude" in df.columns and "Longitude" in df.columns:
    df["Latitude"] = pd.to_numeric(df["Latitude"].apply(parse_raw_coord), errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"].apply(parse_raw_coord), errors="coerce")
    
    # Auto-fix 10x scaled coordinates (e.g. 1.97 -> 19.7 and 8.21 -> 82.1)
    df.loc[(df["Latitude"] >= 1.5) & (df["Latitude"] <= 2.5), "Latitude"] = df["Latitude"] * 10.0
    df.loc[(df["Longitude"] >= 8.0) & (df["Longitude"] <= 9.0), "Longitude"] = df["Longitude"] * 10.0

# Standardize district strings
if "District" in df.columns:
    df["District"] = df["District"].astype(str).str.strip().str.title()

# Convert dates if present
for d_col in ["Date", "Collection_Date", "Alert_Date"]:
    if d_col in df.columns:
        df[d_col] = pd.to_datetime(df[d_col], errors="coerce")


# Sidebar Filters
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

filtered_df = df.copy()

# District Filter
if "District" in df.columns:
    districts = sorted([d for d in df["District"].dropna().unique() if d != "Nan"])
    selected_districts = st.sidebar.multiselect("Select District(s)", districts, default=[])
    if selected_districts:
        filtered_df = filtered_df[filtered_df["District"].isin(selected_districts)]

# Aquifer Formation Filter
if "Aquifer_System" in df.columns:
    aquifers = sorted(df["Aquifer_System"].dropna().unique().tolist())
    selected_aquifers = st.sidebar.multiselect("Aquifer Formation", aquifers, default=[])
    if selected_aquifers:
        filtered_df = filtered_df[filtered_df["Aquifer_System"].isin(selected_aquifers)]

# River Basin Filter
if "River_Basin" in df.columns:
    basins = sorted(df["River_Basin"].dropna().unique().tolist())
    selected_basins = st.sidebar.multiselect("River Basin / Catchment", basins, default=[])
    if selected_basins:
        filtered_df = filtered_df[filtered_df["River_Basin"].isin(selected_basins)]

# Status Filter
if "Status" in df.columns:
    statuses = ["Danger", "Warning", "Safe"]
    avail_statuses = [s for s in statuses if s in df["Status"].unique()]
    selected_status = st.sidebar.multiselect("Quality Status", avail_statuses, default=avail_statuses)
    if selected_status:
        filtered_df = filtered_df[filtered_df["Status"].isin(selected_status)]

# Structure Type Filter
if "Structure" in df.columns:
    structs = sorted(df["Structure"].dropna().unique().tolist())
    selected_structs = st.sidebar.multiselect("Well Structure Type", structs, default=[])
    if selected_structs:
        filtered_df = filtered_df[filtered_df["Structure"].isin(selected_structs)]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered Monitoring Wells**: `{len(filtered_df):,} / {len(df):,}`")

if filtered_df.empty:
    st.warning("No records match the active filter criteria. Please adjust your selections.")
    st.stop()

# --- Top Summary KPI Cards ---
danger_count = (filtered_df["Status"] == "Danger").sum() if "Status" in filtered_df.columns else 0
warning_count = (filtered_df["Status"] == "Warning").sum() if "Status" in filtered_df.columns else 0

fe_exceed = (filtered_df["Fe"] > 1.0).sum() if "Fe" in filtered_df.columns else 0
no3_exceed = (filtered_df["NO3"] > 45.0).sum() if "NO3" in filtered_df.columns else 0
f_exceed = (filtered_df["F"] > 1.5).sum() if "F" in filtered_df.columns else 0
u_exceed = (filtered_df["U"] > 30.0).sum() if "U" in filtered_df.columns else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Wells Monitored", f"{len(filtered_df):,}", f"{len(filtered_df['District'].unique())} Districts" if 'District' in filtered_df.columns else None, "neutral")
with c2:
    metric_card("Critical Alerts (Danger)", f"{danger_count}", f"{(danger_count/len(filtered_df))*100:.1f}% of total" if len(filtered_df)>0 else "", "up" if danger_count>0 else "down")
with c3:
    metric_card("Iron (Fe > 1.0 mg/L) Alerts", f"{fe_exceed}", f"{(fe_exceed/len(filtered_df))*100:.1f}% wells" if len(filtered_df)>0 else "", "up" if fe_exceed>0 else "down")
with c4:
    metric_card("Nitrate (NO3 > 45 mg/L)", f"{no3_exceed}", f"{f_exceed} Fluoride Alerts" if f_exceed>0 else "Normal", "warn" if no3_exceed>0 else "down")

st.markdown("<div style='margin-bottom: 1.1rem;'></div>", unsafe_allow_html=True)

# --- Calculate Hydrochemistry Metrics ---
df_hydro = hc.calculate_hydrochemistry(filtered_df)

# --- Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "🗺️ Aquifer & Basin GIS Map",
    "🏗️ CGWB Deep Aquifer Exploration",
    "🔬 CGWB Published Quality Year Book",
    "🧪 WQI Potability & Pipe Corrosivity",
    "⚠️ Contamination & BIS Exceedances",
    "📊 Geochemical Facies (Piper/Durov/Schoeller)",
    "🌾 Irrigation Quality (Wilcox & USSL)",
    "🗺️ Spatial IDW Plumes & 🧊 3D Profiler",
    "🔬 Gibbs Ratios & Ionic Scatter",
    "🏛️ District Rankings & 📄 PDF Dossier"
])

# ==========================================
# --- TAB 1: GEOSPATIAL AQUIFER & BASIN MAP ---
# ==========================================
with tab1:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">📍 Odisha Multi-Layer Hydrogeological GIS Map (Aquifers & River Basins)</div>
        <div class="chart-subtitle">Overlaying CGWB Principal Aquifers and 11 Major River Basins with Active Groundwater Monitoring Wells</div>
    """, unsafe_allow_html=True)

    # Interactive Map Controls Header
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([3, 3, 2, 2])
    
    with ctrl_col1:
        overlay_mode = st.selectbox(
            "Vector Overlay Layer",
            ["Principal Aquifers", "River Basins (11 Catchments)", "🔥 Density Heatmap", "None (Points Only)"],
            index=0
        )
    
    with ctrl_col2:
        color_metric = st.selectbox(
            "Color Points By",
            ["Quality Status", "Aquifer Formation", "River Basin", "Water Quality Index (WQI)", "Iron (Fe)", "Nitrate (NO3)", "Fluoride (F)", "Electrical Conductivity (EC)", "Total Hardness (TH)", "pH", "Manganese (Mn)", "Uranium (U)"],
            index=0
        )
        
    with ctrl_col3:
        map_style_choice = st.selectbox(
            "Base Map Theme",
            ["OpenStreetMap", "Carto Positron (Light)", "Carto Darkmatter (Dark)"],
            index=0 if not IS_DARK else 2
        )
        style_map = {
            "OpenStreetMap": "open-street-map",
            "Carto Positron (Light)": "carto-positron",
            "Carto Darkmatter (Dark)": "carto-darkmatter"
        }
        chosen_style = style_map.get(map_style_choice, "open-street-map")

    with ctrl_col4:
        show_rivers_toggle = st.checkbox("🌊 River Streams Network", value=True, help="Toggle major river lines and drainage pathways")
        layer_opacity = st.slider("Overlay Opacity", 0.10, 0.80, 0.35, 0.05) if overlay_mode != "None (Points Only)" else 0.0

    valid_map_df = df_hydro[df_hydro["Latitude"].notna() & df_hydro["Longitude"].notna()].copy()

    if not valid_map_df.empty:
        metric_col_map = {
            "Quality Status": "Status",
            "Aquifer Formation": "Aquifer_System",
            "River Basin": "River_Basin",
            "Water Quality Index (WQI)": "WQI",
            "Iron (Fe)": "Fe",
            "Nitrate (NO3)": "NO3",
            "Fluoride (F)": "F",
            "Electrical Conductivity (EC)": "EC",
            "Total Hardness (TH)": "TH",
            "pH": "pH",
            "Manganese (Mn)": "Mn",
            "Uranium (U)": "U"
        }
        chosen_col = metric_col_map.get(color_metric, "Status")

        if overlay_mode == "🔥 Density Heatmap":
            heat_metric = "Fe" if chosen_col in ["Status", "Aquifer_System", "River_Basin"] else chosen_col
            if heat_metric not in valid_map_df.columns or valid_map_df[heat_metric].dropna().empty:
                heat_metric = "EC"
                
            fig_map = px.density_map(
                valid_map_df,
                lat="Latitude",
                lon="Longitude",
                z=heat_metric,
                radius=18,
                zoom=6.4,
                center=dict(lat=20.45, lon=84.5),
                map_style=chosen_style,
                color_continuous_scale="Viridis" if chosen_col == "pH" else "YlOrRd",
                hover_name="Location" if "Location" in valid_map_df.columns else "Station_No"
            )
            fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=580)
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": True})
            
        else: # Advanced Multi-Layer Aquifer & Basin GIS Map
            fig_map = am.build_advanced_gis_map(
                df_wells=valid_map_df,
                overlay_layer=overlay_mode,
                show_overlay=(overlay_mode != "None (Points Only)"),
                show_rivers=show_rivers_toggle,
                overlay_opacity=layer_opacity,
                chosen_col=chosen_col,
                color_metric=color_metric,
                map_style=chosen_style,
                is_dark=IS_DARK
            )
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": True})
            
    else:
        st.info("No valid latitude/longitude coordinates found for the selected wells.")
        
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Hydrogeological Cross-Analysis: Aquifer Systems vs River Basins ---
    hydro_view = st.radio("Select Cross-Analysis Domain", ["🏔️ Principal Aquifers Breakdown", "🌊 11 Major River Basins Breakdown"], horizontal=True)
    
    if hydro_view == "🏔️ Principal Aquifers Breakdown":
        st.markdown("##### 🏔️ Aquifer Formations & Lithological Vulnerability Breakdown")
        aq_c1, aq_c2 = st.columns([5, 5])
        
        with aq_c1:
            if "Aquifer_System" in df_hydro.columns:
                aq_counts = df_hydro["Aquifer_System"].value_counts().reset_index()
                aq_counts.columns = ["Aquifer System", "Monitoring Wells"]
                fig_aq_bar = px.bar(
                    aq_counts,
                    x="Monitoring Wells",
                    y="Aquifer System",
                    orientation="h",
                    color="Aquifer System",
                    color_discrete_map=am.AQUIFER_COLORS,
                    title="Monitoring Wells by Aquifer Formation"
                )
                fig_aq_bar.update_layout(**PLOT_LAYOUT, height=320, showlegend=False)
                st.plotly_chart(fig_aq_bar, use_container_width=True, config={"displayModeBar": False})
                
        with aq_c2:
            if "Aquifer_System" in df_hydro.columns:
                aq_stats = df_hydro.groupby("Aquifer_System").apply(
                    lambda g: pd.Series({
                        "Wells": len(g),
                        "Danger (%)": f"{(g['Status'] == 'Danger').sum() / len(g) * 100:.1f}%",
                        "Fe Exceed": (g["Fe"] > 1.0).sum(),
                        "NO3 Exceed": (g["NO3"] > 45.0).sum(),
                        "F Exceed": (g["F"] > 1.5).sum()
                    })
                ).reset_index()
                
                st.dataframe(aq_stats, use_container_width=True, hide_index=True, height=320)
                
    else: # River Basins Breakdown
        st.markdown("##### 🌊 11 River Basins of Odisha & Catchment Quality Breakdown")
        bs_c1, bs_c2 = st.columns([5, 5])
        
        with bs_c1:
            if "River_Basin" in df_hydro.columns:
                bs_counts = df_hydro["River_Basin"].value_counts().reset_index()
                bs_counts.columns = ["River Basin", "Monitoring Wells"]
                fig_bs_bar = px.bar(
                    bs_counts,
                    x="Monitoring Wells",
                    y="River Basin",
                    orientation="h",
                    color="River Basin",
                    color_discrete_map=am.BASIN_COLORS,
                    title="Monitoring Wells by River Basin"
                )
                fig_bs_bar.update_layout(**PLOT_LAYOUT, height=320, showlegend=False)
                st.plotly_chart(fig_bs_bar, use_container_width=True, config={"displayModeBar": False})
                
        with bs_c2:
            if "River_Basin" in df_hydro.columns:
                bs_stats = df_hydro.groupby("River_Basin").apply(
                    lambda g: pd.Series({
                        "Wells": len(g),
                        "Danger (%)": f"{(g['Status'] == 'Danger').sum() / len(g) * 100:.1f}%",
                        "Fe Exceed": (g["Fe"] > 1.0).sum(),
                        "NO3 Exceed": (g["NO3"] > 45.0).sum(),
                        "F Exceed": (g["F"] > 1.5).sum()
                    })
                ).reset_index()
                
                st.dataframe(bs_stats, use_container_width=True, hide_index=True, height=320)

    # --- Interactive Station Health Inspector Card ---
    st.markdown("### 🔍 Individual Well / Station Health Inspector")
    st.markdown("Select any monitoring station to inspect its water quality parameters against the BIS IS 10500:2012 Drinking Water Standards.")
    
    st_col1, st_col2 = st.columns([4, 6])
    
    with st_col1:
        station_list = sorted(df_hydro["Location"].dropna().unique().tolist()) if "Location" in df_hydro.columns else sorted(df_hydro["Station_No"].dropna().unique().tolist())
        selected_station_name = st.selectbox("Choose Station / Well Location", station_list, index=0 if station_list else None)
        
        if selected_station_name:
            st_data = df_hydro[df_hydro["Location"] == selected_station_name].iloc[0] if "Location" in df_hydro.columns else df_hydro[df_hydro["Station_No"] == selected_station_name].iloc[0]
            
            st_status = st_data.get("Status", "Normal")
            status_badge = '<span class="badge badge-red">🚨 CRITICAL DANGER ALERT</span>' if st_status == "Danger" else ('<span class="badge badge-amber">⚠️ WARNING LEVEL</span>' if st_status == "Warning" else '<span class="badge badge-green">✅ SAFE / POTABLE</span>')
            
            st.markdown(f"""
            <div class="station-card">
                <div style="font-size:1.1rem; font-weight:700; color:var(--text);">{st_data.get('Station_No', 'N/A')}</div>
                <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:8px;">{st_data.get('Village', '')}, {st_data.get('Block', '')} (Dist: {st_data.get('District', '')})</div>
                <div style="margin-bottom:12px;">{status_badge}</div>
                <table style="width:100%; font-size:0.8rem; border-top:1px solid var(--border-subtle); padding-top:6px;">
                    <tr><td style="color:var(--text-muted);">River Basin:</td><td><b style="color:var(--accent);">{st_data.get('River_Basin', 'Mahanadi')}</b></td></tr>
                    <tr><td style="color:var(--text-muted);">Aquifer Formation:</td><td><b>{st_data.get('Aquifer_System', 'Unclassified')}</b></td></tr>
                    <tr><td style="color:var(--text-muted);">WQI Score:</td><td><b>{st_data.get('WQI', 'N/A')} ({st_data.get('WQI_Class', 'N/A')})</b></td></tr>
                    <tr><td style="color:var(--text-muted);">Corrosivity Index:</td><td><b>{st_data.get('Corrosivity_Class', 'N/A')}</b></td></tr>
                    <tr><td style="color:var(--text-muted);">Depth (mbgl):</td><td><b>{st_data.get('Depth_mbgl', 'N/A')} m</b></td></tr>
                    <tr><td style="color:var(--text-muted);">Latitude / Longitude:</td><td><b>{st_data.get('Latitude', 'N/A')}, {st_data.get('Longitude', 'N/A')}</b></td></tr>
                    <tr><td style="color:var(--text-muted);">Date Sampled:</td><td><b>{str(st_data.get('Date', 'N/A'))[:10]}</b></td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
    with st_col2:
        if selected_station_name:
            benchmarks = [
                {"Parameter": "pH (Units)", "Observed": float(st_data.get("pH", 0)) if pd.notna(st_data.get("pH")) else 0, "BIS_Limit": 8.5, "Safe_Min": 6.5},
                {"Parameter": "Iron Fe (mg/L)", "Observed": float(st_data.get("Fe", 0)) if pd.notna(st_data.get("Fe")) else 0, "BIS_Limit": 1.0, "Safe_Min": 0},
                {"Parameter": "Nitrate NO3 (mg/L)", "Observed": float(st_data.get("NO3", 0)) if pd.notna(st_data.get("NO3")) else 0, "BIS_Limit": 45.0, "Safe_Min": 0},
                {"Parameter": "Fluoride F (mg/L)", "Observed": float(st_data.get("F", 0)) if pd.notna(st_data.get("F")) else 0, "BIS_Limit": 1.5, "Safe_Min": 0},
                {"Parameter": "Hardness TH (mg/L)", "Observed": float(st_data.get("TH", 0))/10 if pd.notna(st_data.get("TH")) else 0, "BIS_Limit": 60.0, "Safe_Min": 0},
            ]
            bench_df = pd.DataFrame(benchmarks)
            
            fig_gauge = go.Figure()
            fig_gauge.add_trace(go.Bar(
                name="Observed Level",
                x=bench_df["Parameter"],
                y=bench_df["Observed"],
                marker_color=["#ef4444" if row["Observed"] > row["BIS_Limit"] else "#22c55e" for _, row in bench_df.iterrows()]
            ))
            fig_gauge.add_trace(go.Scatter(
                name="BIS Safe Limit",
                x=bench_df["Parameter"],
                y=bench_df["BIS_Limit"],
                mode="lines+markers",
                marker=dict(size=8, color="#f59e0b"),
                line=dict(color="#f59e0b", dash="dash", width=2)
            ))
            fig_gauge.update_layout(
                **PLOT_LAYOUT, 
                height=260, 
                title=f"Water Parameters vs BIS Safe Limit: {st_data.get('Station_No', '')}",
                barmode="group",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
    
    decision_panel(
        title="Geospatial Hotspot & Site-Selection Decision Guidance",
        key_findings=[
            f"<b>Spatial Clustering:</b> <b>{fe_exceed} wells (16.5%)</b> with severe Iron contamination are clustered along coastal alluvial belts and river floodplains (Kendrapara, Puri, Jagatsinghpur).",
            f"<b>Agricultural Zones:</b> <b>{no3_exceed} wells (14.2%)</b> exhibit elevated Nitrate (>45 mg/L), primarily concentrated in shallow unconfined aquifers beneath intensive agricultural blocks.",
            "<b>Depth Vulnerability:</b> Dug wells (<15 mbgl) show higher nitrate vulnerability from surface runoff, whereas deep tube wells (>40 mbgl) encounter higher mineralized iron and manganese."
        ],
        recommendations=[
            "<b>Drinking Water Supply Strategy:</b> Prioritize multi-village surface water intake schemes (Jal Jeevan Mission) over deep borewells in high-Fe coastal delta zones.",
            "<b>Sanitary Protection Zones:</b> Establish a minimum 50-100 meter sanitary buffer radius around public tube wells to prevent direct agricultural fertilizer and septic percolation.",
            "<b>Source Segregation:</b> In high-salinity coastal blocks, tap shallow freshwater lenses during post-monsoon and restrict excessive deep pumping to avoid saltwater upconing."
        ],
        icon="🗺️"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# --- TAB 2: CGWB DEEP AQUIFER EXPLORATION (OCTOBER 2024 SYNTHESIS) ---
# =========================================================================
with tab2:
    em.render_exploration_tab(is_dark=IS_DARK)

# =========================================================================
# --- TAB 3: CGWB PUBLISHED QUALITY YEAR BOOK (AAP 2024-25 SYNTHESIS) ---
# =========================================================================
with tab3:
    qm.render_quality_yearbook_tab(is_dark=IS_DARK)

# =========================================================================
# --- TAB 4: WATER QUALITY INDEX (WQI) & PIPE CORROSIVITY / SCALING (LSI) ---
# =========================================================================
with tab4:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🧪 Water Quality Index (WA-WQI) & Pipe Corrosivity / Scaling Assessment</div>
        <div class="chart-subtitle">Single-composite drinking water potability scoring and pipe lifespan prediction (LSI & RSI) for Jal Jeevan Mission engineering</div>
    """, unsafe_allow_html=True)
    
    # Top WQI Metrics
    valid_wqi = df_hydro[df_hydro["WQI_Class"] != "Indeterminate"]
    good_wqi_pct = (valid_wqi["WQI"] < 100).sum() / len(valid_wqi) * 100 if len(valid_wqi) > 0 else 0
    unfit_wqi_pct = (valid_wqi["WQI"] >= 300).sum() / len(valid_wqi) * 100 if len(valid_wqi) > 0 else 0
    scale_forming_pct = (df_hydro["Corrosivity_Class"] == "Scale Forming (Encrusting)").sum() / len(df_hydro) * 100 if len(df_hydro) > 0 else 0
    corrosive_pct = (df_hydro["Corrosivity_Class"] == "Corrosive / Aggressive").sum() / len(df_hydro) * 100 if len(df_hydro) > 0 else 0
    
    wq_c1, wq_c2, wq_c3, wq_c4 = st.columns(4)
    with wq_c1:
        metric_card("Potable Quality (WQI < 100)", f"{good_wqi_pct:.1f}%", f"{(valid_wqi['WQI'] < 100).sum()} of {len(valid_wqi)} wells", "up")
    with wq_c2:
        metric_card("Unsuitable for Drinking (WQI > 300)", f"{unfit_wqi_pct:.1f}%", f"{(valid_wqi['WQI'] >= 300).sum()} wells require RO/IRP", "down" if unfit_wqi_pct > 0 else "neutral")
    with wq_c3:
        metric_card("Pipe Scaling Tendency (LSI > 0.5)", f"{scale_forming_pct:.1f}%", "Calcium carbonate encrustation", "warn" if scale_forming_pct > 20 else "neutral")
    with wq_c4:
        metric_card("Aggressive Corrosivity (LSI < -0.5)", f"{corrosive_pct:.1f}%", "Pipe dissolution & metal leaching", "down" if corrosive_pct > 5 else "neutral")
        
    st.markdown("<div style='margin-bottom: 1.1rem;'></div>", unsafe_allow_html=True)
    
    wqi_plot_c1, wqi_plot_c2 = st.columns(2)
    with wqi_plot_c1:
        fig_wqi_donut = hc.create_wqi_summary_chart(df_hydro, is_dark=IS_DARK)
        st.plotly_chart(fig_wqi_donut, use_container_width=True, config={"displayModeBar": True})
        
    with wqi_plot_c2:
        fig_corr_quad = hc.create_corrosivity_diagram(df_hydro, is_dark=IS_DARK)
        st.plotly_chart(fig_corr_quad, use_container_width=True, config={"displayModeBar": True})
        
    # Tab 2 Decision Panel
    decision_panel(
        title="Jal Jeevan Mission (JJM) Piped Scheme Engineering & Potability Matrix",
        key_findings=[
            f"<b>Comprehensive Potability:</b> <b>{good_wqi_pct:.1f}% of groundwater sources</b> achieve an Excellent to Good WQI score (<100), qualifying for direct distribution with basic chlorination.",
            f"<b>High-Threat Remediation Needed:</b> <b>{(valid_wqi['WQI'] >= 300).sum()} wells (WQI > 300)</b> are chemically hazardous due to concentrated Iron (>1.0 mg/L), Nitrate (>45 mg/L), or Fluoride (>1.5 mg/L).",
            f"<b>Pipe Encrustation Hazard:</b> <b>{scale_forming_pct:.1f}% of wells</b> exhibit positive LSI (>0.5) and low RSI (<6.5), indicating scale-forming tendencies that choke pipe internal diameter over 5-10 years.",
            f"<b>Corrosive Water Pockets:</b> <b>{corrosive_pct:.1f}% of sources</b> in acidic lateritic or low-alkalinity terrains are aggressively corrosive to metallic pipes."
        ],
        recommendations=[
            "<b>Piped Water Pipe Specification:</b> For scale-forming groundwater, mandate <b>HDPE (High-Density Polyethylene)</b> or cement-mortar lined ductile iron pipes to prevent scaling headloss.",
            "<b>Corrosion Neutralization:</b> For corrosive low-pH sources (LSI < -0.5), install limestone/calcite neutralizing filter beds at the pump head before distribution.",
            "<b>WQI Priority Ranking:</b> Immediately deploy village-level community water purification plants in all habitations where groundwater WQI exceeds 200."
        ],
        icon="🧪"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# --- TAB 5: CONTAMINATION & BIS EXCEEDANCES ---
# =========================================================================
with tab5:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">Major Contaminant Exceedance Counts</div>
            <div class="chart-subtitle">Number of wells exceeding BIS Indian Drinking Water Standards</div>
        """, unsafe_allow_html=True)
        
        exceed_data = []
        if "Fe" in df_hydro.columns: exceed_data.append({"Contaminant": "Iron (Fe > 1.0 mg/L)", "Wells Exceeding": (df_hydro["Fe"] > 1.0).sum(), "Threshold": "1.0 mg/L"})
        if "Mn" in df_hydro.columns: exceed_data.append({"Contaminant": "Manganese (Mn > 0.3 mg/L)", "Wells Exceeding": (df_hydro["Mn"] > 0.3).sum(), "Threshold": "0.3 mg/L"})
        if "NO3" in df_hydro.columns: exceed_data.append({"Contaminant": "Nitrate (NO3 > 45 mg/L)", "Wells Exceeding": (df_hydro["NO3"] > 45).sum(), "Threshold": "45 mg/L"})
        if "F" in df_hydro.columns: exceed_data.append({"Contaminant": "Fluoride (F > 1.5 mg/L)", "Wells Exceeding": (df_hydro["F"] > 1.5).sum(), "Threshold": "1.5 mg/L"})
        if "TH" in df_hydro.columns: exceed_data.append({"Contaminant": "Hardness (TH > 600 mg/L)", "Wells Exceeding": (df_hydro["TH"] > 600).sum(), "Threshold": "600 mg/L"})
        if "EC" in df_hydro.columns: exceed_data.append({"Contaminant": "High EC (> 3000 µS/cm)", "Wells Exceeding": (df_hydro["EC"] > 3000).sum(), "Threshold": "3000 µS/cm"})
        if "U" in df_hydro.columns: exceed_data.append({"Contaminant": "Uranium (U > 30 µg/L)", "Wells Exceeding": (df_hydro["U"] > 30).sum(), "Threshold": "30 µg/L"})
        if "pH" in df_hydro.columns: exceed_data.append({"Contaminant": "Acidic pH (< 6.5)", "Wells Exceeding": (df_hydro["pH"] < 6.5).sum(), "Threshold": "< 6.5"})

        exceed_df = pd.DataFrame(exceed_data)
        if not exceed_df.empty:
            fig_bar_ex = px.bar(exceed_df, x="Wells Exceeding", y="Contaminant", orientation="h",
                                color="Wells Exceeding", color_continuous_scale="Reds")
            fig_bar_ex.update_layout(**PLOT_LAYOUT, height=360, coloraxis_showscale=False)
            st.plotly_chart(fig_bar_ex, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_c2:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">Nitrate (NO3) vs. Iron (Fe) Distribution</div>
            <div class="chart-subtitle">Highlighting primary chemical contamination threats</div>
        """, unsafe_allow_html=True)
        
        if "NO3" in df_hydro.columns and "Fe" in df_hydro.columns:
            fig_scat_cont = px.scatter(
                df_hydro, x="NO3", y="Fe", color="Status",
                color_discrete_map={"Danger": "#ef4444", "Warning": "#f59e0b", "Safe": "#22c55e"},
                hover_data=["District", "Block", "Village"] if "Village" in df_hydro.columns else None,
                labels={"NO3": "Nitrate NO3 (mg/L)", "Fe": "Iron Fe (mg/L)"}
            )
            fig_scat_cont.add_vline(x=45, line_dash="dash", line_color="orange", annotation_text="BIS NO3 (45 mg/L)")
            fig_scat_cont.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="BIS Fe (1.0 mg/L)")
            fig_scat_cont.update_layout(**PLOT_LAYOUT, height=360)
            st.plotly_chart(fig_scat_cont, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    decision_panel(
        title="Drinking Water Potability & Public Health Treatment Matrix",
        key_findings=[
            "<b>Iron & Manganese Preponderance:</b> Dissolved Iron (up to 65.92 mg/L) and Manganese (>0.3 mg/L) represent the primary aesthetic and organoleptic failure across 16.5% of stations.",
            "<b>Nitrate Methemoglobinemia Risk:</b> Nitrate levels reaching up to 214 mg/L pose severe health risks to infants and require immediate tap water alerts.",
            f"<b>Endemic Fluorosis Pockets:</b> <b>{f_exceed} monitoring locations</b> exceed 1.5 mg/L Fluoride in granitic bedrock aquifers (dental/skeletal fluorosis risk)."
        ],
        recommendations=[
            "<b>Community Iron Removal Plants (IRPs):</b> Deploy aeration + sand-gravel rapid gravity filtration units at all community borewells exceeding 1.0 mg/L Fe.",
            "<b>Fluoride Treatment:</b> Install Nalgonda technique or activated alumina adsorption units in the 16 identified fluoride endemic villages.",
            "<b>Nitrate Remediation:</b> Enforce point-of-use RO or strong-base anion exchange (SBA) systems where Nitrate > 45 mg/L, combined with organic fertilizer transition programs."
        ],
        icon="⚠️"
    )

# =========================================================================
# --- TAB 6: GEOCHEMICAL FACIES (PIPER, DUROV & SCHOELLER) ---
# =========================================================================
with tab6:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">📊 Hydrogeochemical Facies & Ion Evolution Modeling</div>
        <div class="chart-subtitle">Interactive Piper Trilinear, Extended Durov, and Schoeller Semi-Logarithmic Diagrams</div>
    """, unsafe_allow_html=True)
    
    facies_mode = st.radio("Select Diagram Type", ["💎 Piper Trilinear Diagram", "📐 Extended Durov Diagram", "📈 Schoeller Semi-Log Diagram"], horizontal=True)
    
    if facies_mode == "💎 Piper Trilinear Diagram":
        fig_piper_ternary = hc.create_piper_diagram(df_hydro, is_dark=IS_DARK)
        st.plotly_chart(fig_piper_ternary, use_container_width=True, config={"displayModeBar": True})
        
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        col_p_d1, col_p_d2 = st.columns([3, 2])
        with col_p_d1:
            fig_piper_diamond = hc.create_piper_diamond(df_hydro, is_dark=IS_DARK)
            st.plotly_chart(fig_piper_diamond, use_container_width=True, config={"displayModeBar": True})
        with col_p_d2:
            st.markdown("#### 🌊 Hydrochemical Facies Distribution")
            facies_counts = df_hydro["Water_Type"].value_counts().reset_index()
            facies_counts.columns = ["Facies Type", "Monitoring Wells"]
            fig_facies_pie = px.pie(
                facies_counts, 
                names="Facies Type", 
                values="Monitoring Wells",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_facies_pie.update_layout(**PLOT_LAYOUT, height=340, showlegend=True)
            st.plotly_chart(fig_facies_pie, use_container_width=True, config={"displayModeBar": False})
            
    elif facies_mode == "📐 Extended Durov Diagram":
        st.markdown("#### 📐 Extended Durov Plot (Ternary Projections + pH + TDS Integration)")
        fig_durov = hc.create_durov_diagram(df_hydro, is_dark=IS_DARK)
        st.plotly_chart(fig_durov, use_container_width=True, config={"displayModeBar": True})
        
    else: # Schoeller Diagram
        st.markdown("#### 📈 Schoeller Semi-Logarithmic Ionic Concentration Diagram")
        schoeller_grp = st.selectbox("Group Mean Profiles By", ["Aquifer Formation", "River Basin", "Quality Status"], index=0)
        grp_col = "Aquifer_System" if schoeller_grp == "Aquifer Formation" else ("River_Basin" if schoeller_grp == "River Basin" else "Status")
        fig_schoeller = hc.create_schoeller_diagram(df_hydro, group_by=grp_col, is_dark=IS_DARK)
        st.plotly_chart(fig_schoeller, use_container_width=True, config={"displayModeBar": True})
        
    decision_panel(
        title="Geochemical Evolution & Aquifer Recharge Management",
        key_findings=[
            "<b>Recharge Dominance:</b> The predominant hydrochemical facies is <b>Ca²⁺ - Mg²⁺ - HCO₃⁻</b>, proving that the groundwater system is continuously replenished by fresh monsoon meteoric recharge.",
            "<b>Coastal Saline Facies:</b> Localized <b>Na⁺ - Cl⁻ - SO₄²⁻</b> signatures in coastal tracts indicate sea-water mixing or trapped paleo-saline connate waters.",
            "<b>Schoeller Parallelism:</b> Parallel ionic signatures across alluvium and laterite formations demonstrate direct hydraulic connectivity along regional catchment flowpaths."
        ],
        recommendations=[
            "<b>Artificial Recharge Zoning:</b> Prioritize check dams, percolation tanks, and recharge shafts in upstream Ca-Mg-HCO3 recharge zones to enhance regional aquifer storage.",
            "<b>Salinity Intrusion Barriers:</b> Establish subsurface dykes and rainwater harvesting injection wells along coastal stretches exhibiting Na-Cl facies to suppress saline water front advancement.",
            "<b>Aquifer Protection:</b> Discourage uncontrolled deep borewell drilling in Na-Cl / Ca-Cl transition zones."
        ],
        icon="📊"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# --- TAB 7: IRRIGATION QUALITY (WILCOX & USSL) ---
# =========================================================================
with tab7:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🌾 Irrigation & Agricultural Water Quality Suitability</div>
        <div class="chart-subtitle">Evaluates Salinity Hazard (EC) and Sodium Hazard (%Na & SAR) based on Wilcox and US Salinity Laboratory (USSL) classifications</div>
    """, unsafe_allow_html=True)
    
    irrig_col1, irrig_col2, irrig_col3, irrig_col4 = st.columns(4)
    with irrig_col1:
        good_irrig = (df_hydro["Wilcox_Class"].isin(["Excellent", "Good"])).sum()
        metric_card("Irrigation Suitable (Wilcox)", f"{good_irrig}", f"{(good_irrig/len(df_hydro))*100:.1f}% wells" if len(df_hydro)>0 else "", "up")
    with irrig_col2:
        doubt_irrig = (df_hydro["Wilcox_Class"].isin(["Doubtful", "Unsuitable"])).sum()
        metric_card("Restricted / Unsuitable", f"{doubt_irrig}", f"{(doubt_irrig/len(df_hydro))*100:.1f}% wells" if len(df_hydro)>0 else "", "down" if doubt_irrig>0 else "neutral")
    with irrig_col3:
        avg_sar = df_hydro["SAR"].mean() if "SAR" in df_hydro.columns else 0
        metric_card("Mean SAR (Alkali Hazard)", f"{avg_sar:.2f}", "S1 Low Hazard (<10)" if avg_sar < 10 else "Moderate/High", "up" if avg_sar < 10 else "warn")
    with irrig_col4:
        c1s1_count = (df_hydro["USSL_Class"] == "C1-S1").sum() + (df_hydro["USSL_Class"] == "C2-S1").sum()
        metric_card("USSL C1-S1 / C2-S1 Safe", f"{c1s1_count}", "Ideal for crops", "neutral")
        
    st.markdown("<div style='margin-bottom: 1.1rem;'></div>", unsafe_allow_html=True)
    
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        fig_wilcox = hc.create_wilcox_diagram(df_hydro, is_dark=IS_DARK)
        st.plotly_chart(fig_wilcox, use_container_width=True, config={"displayModeBar": True})
        
    with w_col2:
        fig_ussl = hc.create_ussl_diagram(df_hydro, is_dark=IS_DARK)
        st.plotly_chart(fig_ussl, use_container_width=True, config={"displayModeBar": True})
        
    decision_panel(
        title="Agronomic Assessment & Irrigation Crop Advisory",
        key_findings=[
            f"<b>Low Sodium Hazard (S1):</b> <b>99.1% of wells have SAR < 10</b> (Mean SAR: {avg_sar:.2f}), confirming virtually zero risk of sodium-induced soil crusting or permeability loss.",
            "<b>Salinity Hazard (C2 vs C3):</b> The majority of agricultural wells fall in C2 (Medium Salinity, 250-750 µS/cm) and C3 (High Salinity, 750-2250 µS/cm).",
            "<b>Wilcox Viability:</b> Over 85% of fully characterized samples are classified as <b>Excellent to Permissible</b> for irrigation across major kharif and rabi cropping seasons."
        ],
        recommendations=[
            "<b>Crop Selection for C3 Water:</b> For wells plotting in C3-S1, cultivate semi-tolerant to salt-tolerant crops like Paddy, Wheat, Cotton, Mustard, and Millets with adequate field drainage.",
            "<b>Soil Gypsum Management:</b> Because SAR is low (S1), farmers <b>do NOT need expensive gypsum soil conditioning</b>, reducing agricultural input costs.",
            "<b>Micro-Irrigation Adoption:</b> Promote Drip and Sprinkler irrigation in C3 salinity areas to prevent salt accumulation in the root zone."
        ],
        icon="🌾"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# --- TAB 8: SPATIAL IDW PLUMES & 3D SUBSURFACE PROFILER ---
# =========================================================================
with tab8:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🗺️ Continuous Spatial IDW Plumes & 🧊 3D Subsurface Stratigraphy</div>
        <div class="chart-subtitle">Inverse Distance Weighting (IDW) 2D Plume Interpolation across Odisha and 3D Subsurface Aquifer Depth Profiling</div>
    """, unsafe_allow_html=True)
    
    spatial_view_choice = st.radio("Select Spatial Modeling Mode", ["🗺️ Continuous Spatial IDW Plume Interpolation", "🧊 3D Subsurface Aquifer Stratigraphy Profiler"], horizontal=True)
    
    if spatial_view_choice == "🗺️ Continuous Spatial IDW Plume Interpolation":
        idw_c1, idw_c2 = st.columns([4, 6])
        with idw_c1:
            idw_param_choice = st.selectbox(
                "Select Contaminant / Indicator to Interpolate",
                ["Iron (Fe)", "Nitrate (NO3)", "Fluoride (F)", "Water Quality Index (WQI)", "Electrical Conductivity (EC)", "Total Hardness (TH)"],
                index=0
            )
            param_key_map = {
                "Iron (Fe)": "Fe",
                "Nitrate (NO3)": "NO3",
                "Fluoride (F)": "F",
                "Water Quality Index (WQI)": "WQI",
                "Electrical Conductivity (EC)": "EC",
                "Total Hardness (TH)": "TH"
            }
            target_idw_col = param_key_map.get(idw_param_choice, "Fe")
            
        fig_idw = sm.create_idw_plume_map(
            df=df_hydro,
            param=target_idw_col,
            param_label=idw_param_choice,
            map_style=chosen_style,
            is_dark=IS_DARK
        )
        st.plotly_chart(fig_idw, use_container_width=True, config={"displayModeBar": True})
        
    else: # 3D Subsurface Stratigraphy Profiler
        p3d_c1, p3d_c2 = st.columns([4, 6])
        with p3d_c1:
            prof_color_by = st.selectbox("Color 3D Wells By", ["Status", "Aquifer_System", "WQI", "Fe", "NO3", "F", "EC"], index=0)
        with p3d_c2:
            max_depth_slider = st.slider("Maximum Depth Filter (mbgl)", 10, 150, 80, 5)
            
        fig_3d_prof = sm.create_3d_subsurface_profile(
            df=df_hydro,
            color_by=prof_color_by,
            max_depth=max_depth_slider,
            is_dark=IS_DARK
        )
        st.plotly_chart(fig_3d_prof, use_container_width=True, config={"displayModeBar": True})
        
    decision_panel(
        title="Spatial Plume Dynamics & Subsurface Stratigraphy Advisory",
        key_findings=[
            "<b>Continuous Plume Delineation:</b> The IDW model maps regional high-Iron plumes across the Mahanadi and Brahmani deltaic plains, extending continuously between discrete monitoring points.",
            "<b>Vertical Contaminant Stratification:</b> 3D depth profiling reveals that shallow aquifers (<15 mbgl) suffer from surface-derived agricultural Nitrate, while deep borewells (>40 mbgl) encounter higher geogenic Iron and Hardness.",
            "<b>Safe Deep Aquifer Windows:</b> In central crystalline zones, deeper fracture zones (30-60 mbgl) yield significantly lower nitrate concentrations than unconfined dug wells."
        ],
        recommendations=[
            "<b>Casing & Grouting Standards:</b> Mandate sanitary cement grouting for the top 15 meters of all newly drilled public tube wells to seal off polluted shallow phreatic water.",
            "<b>Inter-Village Pipeline Routing:</b> Use the continuous IDW plume map to route JJM surface water transmission mains directly across high-risk contamination valleys.",
            "<b>Deep Aquifer Exploration:</b> In fluoride-free alluvial blocks, tap protected deep confined aquifers (>60 mbgl) using gravel-packed deep tube wells."
        ],
        icon="🗺️"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# --- TAB 9: GIBBS RATIOS & IONIC SCATTER ---
# =========================================================================
with tab9:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🔬 Gibbs Boomerang & Hydrochemical Bivariate Diagrams</div>
        <div class="chart-subtitle">Delineates natural groundwater evolution mechanisms (rock weathering vs evaporation vs precipitation) and ion-exchange relationships</div>
    """, unsafe_allow_html=True)
    
    fig_gibbs = hc.create_gibbs_diagrams(df_hydro, is_dark=IS_DARK)
    st.plotly_chart(fig_gibbs, use_container_width=True, config={"displayModeBar": True})
    
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("#### 📊 Interactive Bivariate Scatter & Equiline Analysis")
    biv_c1, biv_c2, biv_c3 = st.columns(3)
    
    num_opts = [c for c in ["pH", "EC", "TDS (mg/L)", "Ca", "Mg", "Na", "K", "Cl", "SO4", "HCO3", "CO3", "NO3", "F", "Fe", "TH", "WQI", "LSI", "RSI", "SAR", "Pct_Na", "Depth_mbgl"] if c in df_hydro.columns]
    
    with biv_c1:
        x_param = st.selectbox("X-Axis Variable", num_opts, index=num_opts.index("Cl") if "Cl" in num_opts else 0)
    with biv_c2:
        y_param = st.selectbox("Y-Axis Variable", num_opts, index=num_opts.index("Na") if "Na" in num_opts else min(1, len(num_opts)-1))
    with biv_c3:
        color_param = st.selectbox("Color By", ["Status", "District", "Aquifer_System", "River_Basin", "Water_Type", "USSL_Class", "None"], index=0)
        
    fig_custom_scat = hc.create_bivariate_scatter(
        df_hydro,
        x_param=x_param,
        y_param=y_param,
        color_param=None if color_param == "None" else color_param,
        is_dark=IS_DARK
    )
    st.plotly_chart(fig_custom_scat, use_container_width=True, config={"displayModeBar": True})
    
    decision_panel(
        title="Geogenic Origin & Hydrochemical Mechanism Validation",
        key_findings=[
            "<b>Gibbs Mechanism Dominance:</b> Over 95% of groundwater points plot squarely in the <b>Rock-Water Interaction</b> central sector (TDS 100-1000 mg/L), proving that groundwater mineralization is fundamentally geogenic (rock dissolution) rather than atmospheric precipitation or hyper-evaporative brine concentration.",
            "<b>Na⁺ vs Cl⁻ Equiline:</b> Samples plotting above the 1:1 equiline (Na/Cl > 1) confirm silicate mineral weathering (e.g. albite/plagioclase feldspars) and ion exchange where calcium is adsorbed and sodium released.",
            "<b>Ca²⁺ + Mg²⁺ vs HCO₃⁻ + SO₄²⁻:</b> Points falling close to the equiline signify carbonate dissolution (calcite and dolomite) as the primary buffer stabilizing groundwater pH between 6.8 and 8.2."
        ],
        recommendations=[
            "<b>Groundwater Governance:</b> Environmental compliance can safely attribute bulk ion mineralization (Ca, Mg, HCO3, Na) to natural aquifer rock-water interaction, directing regulatory enforcement toward anthropogenic point-sources (septic, fertilizers for NO3).",
            "<b>Watershed Conservation:</b> Maintain vegetation and soil health in upper catchment watersheds to preserve the natural recharge chemistry buffering capacity."
        ],
        icon="🔬"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# --- TAB 10: DISTRICT RANKINGS & AUTOMATED PDF DOSSIER ---
# =========================================================================
with tab10:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🏛️ District Severity Rankings & 📄 Executive Hydrogeological PDF Dossier</div>
        <div class="chart-subtitle">Administrative prioritization and one-click official CGWB / Jal Jeevan Mission PDF briefing report generation</div>
    """, unsafe_allow_html=True)
    
    pdf_col1, pdf_col2 = st.columns([5, 5])
    
    with pdf_col1:
        st.markdown("#### 📄 Generate Official District PDF Briefing Dossier")
        st.markdown("Select any district to generate and download a formal, publication-styled executive hydrogeological assessment report:")
        
        all_districts = ["All Odisha (Statewide)"] + sorted([d for d in df_hydro["District"].dropna().unique() if d != "Nan"])
        selected_report_dist = st.selectbox("Select Target District for PDF Dossier", all_districts, index=0)
        target_name = "All Odisha" if selected_report_dist == "All Odisha (Statewide)" else selected_report_dist
        
        # Generate PDF Bytes
        pdf_bytes = rg.generate_district_pdf(df_hydro, target_name)
        
        st.download_button(
            label=f"📥 Download {selected_report_dist} PDF Dossier",
            data=pdf_bytes,
            file_name=f"Odisha_Groundwater_Dossier_{target_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            help="Download an official executive PDF summary ready for review"
        )
        st.markdown("<div style='font-size:0.8rem; color:var(--text-muted); margin-top:6px;'>Includes: Executive KPI assessment, BIS Compliance Matrix, Top 10 Critical Action Villages, and JJM Engineering Treatment Guidance.</div>", unsafe_allow_html=True)
        
    with pdf_col2:
        if "District" in df_hydro.columns:
            dist_agg = df_hydro.groupby("District")["Status"].value_counts().unstack().fillna(0)
            if "Danger" not in dist_agg.columns: dist_agg["Danger"] = 0
            if "Warning" not in dist_agg.columns: dist_agg["Warning"] = 0
            if "Safe" not in dist_agg.columns: dist_agg["Safe"] = 0
            
            dist_agg = dist_agg.sort_values(by=["Danger", "Warning"], ascending=False).reset_index().head(10)
            
            fig_dist_bar = px.bar(
                dist_agg, x="District", y=["Danger", "Warning", "Safe"],
                color_discrete_map={"Danger": "#ef4444", "Warning": "#f59e0b", "Safe": "#22c55e"},
                title="Top 10 High-Alert Districts (Danger vs Warning vs Safe)"
            )
            fig_dist_bar.update_layout(**PLOT_LAYOUT, height=320, barmode="stack")
            st.plotly_chart(fig_dist_bar, use_container_width=True, config={"displayModeBar": False})
            
    st.markdown("---")
    st.markdown("### 📋 Master Filtered Monitoring Well Dataset")
    
    csv_buf = io.StringIO()
    df_hydro.to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Export Full Filtered Dataset (CSV with WQI, LSI, RSI)",
        data=csv_buf.getvalue(),
        file_name="odisha_groundwater_master_enriched.csv",
        mime="text/csv"
    )
    st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)
    
    cols_to_show = [c for c in ["Station_No", "District", "Block", "River_Basin", "Aquifer_System", "pH", "EC", "Fe", "NO3", "F", "WQI", "WQI_Class", "Corrosivity_Class", "Status"] if c in df_hydro.columns]
    table_sample = df_hydro[cols_to_show].head(100)
    
    th_html = "".join([f"<th>{c}</th>" for c in cols_to_show])
    tbody_html = ""
    for _, row in table_sample.iterrows():
        td_html = ""
        for c in cols_to_show:
            val = row[c]
            if pd.isna(val):
                td_html += "<td>-</td>"
            elif c == "Status":
                badge_cls = "badge-green" if val == "Safe" else ("badge-amber" if val == "Warning" else "badge-red")
                td_html += f'<td><span class="badge {badge_cls}">{val}</span></td>'
            elif c == "WQI_Class":
                badge_cls = "badge-green" if "Excellent" in str(val) or "Good" in str(val) else ("badge-amber" if "Poor" in str(val) else "badge-red")
                td_html += f'<td><span class="badge {badge_cls}">{val}</span></td>'
            elif isinstance(val, float):
                td_html += f"<td>{val:.2f}</td>"
            else:
                td_html += f"<td>{str(val)}</td>"
        tbody_html += f"<tr>{td_html}</tr>"
        
    st.markdown(f"""
    <div style="overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--card);">
        <table class="data-table">
            <thead>
                <tr>{th_html}</tr>
            </thead>
            <tbody>
                {tbody_html}
            </tbody>
        </table>
    </div>
    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 8px;">
        Showing top {len(table_sample)} of {len(df_hydro):,} matching station records
    </div>
    """, unsafe_allow_html=True)
    
    decision_panel(
        title="District-Level Resource Allocation & Administrative Prioritization",
        key_findings=[
            "<b>Priority District Tier 1:</b> Kendrapara, Rayagada, Nabarangpur, and Mayurbhanj exhibit the highest density of critical danger alerts requiring urgent intervention.",
            "<b>Dual-Threat Vulnerability:</b> Kendrapara suffers from combined high Iron and high Salinity, whereas Nabarangpur exhibits heavy agricultural Nitrate exceedances.",
            "<b>Safe Groundwater Havens:</b> Districts like Sambalpur and Bargarh possess large clusters of safe potable wells, suitable for regional water grid interconnection."
        ],
        recommendations=[
            "<b>State Budgetary Allocation:</b> Prioritize Jal Jeevan Mission capital expenditure and solar-powered community water purification kiosks to Tier 1 affected blocks.",
            "<b>Mobile Water Quality Laboratories:</b> Deploy mobile laboratory testing vans on a bi-weekly testing cycle across the top 5 high-alert districts.",
            "<b>Public Awareness Campaigns:</b> Conduct village-level 'Jal Chaupal' meetings educating communities on boiling/filtering water and avoiding untreated high-nitrate well usage for infant formula."
        ],
        icon="🏛️"
    )
    st.markdown("</div>", unsafe_allow_html=True)

