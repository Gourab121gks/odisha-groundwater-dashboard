import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

PLOT_LAYOUT = dict(
    margin=dict(l=20, r=20, t=40, b=20),
    font=dict(family="DM Sans, sans-serif")
)

@st.cache_data
def load_exploration_data():
    dir_path = os.path.dirname(__file__)
    df_drilling = pd.read_csv(os.path.join(dir_path, "cgwb_district_drilling.csv"))
    df_saline = pd.read_csv(os.path.join(dir_path, "cgwb_saline_tracts.csv"))
    df_hyd = pd.read_csv(os.path.join(dir_path, "cgwb_hydraulic_parameters.csv"))
    return df_drilling, df_saline, df_hyd

def render_exploration_tab(is_dark=False):
    df_drilling, df_saline, df_hyd = load_exploration_data()
    
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🏗️ Central Ground Water Board (CGWB) Exploration & Deep Aquifer Potential</div>
        <div class="chart-subtitle">Synthesis of CGWB's Landmark Report <i>"Ground Water Exploration in Odisha" (October 2024)</i> — Delineating 3,190 Exploratory Wells, Deep Productive Aquifers, Coastal Saline-Fresh Interfaces & Hydraulic Parameters</div>
    """, unsafe_allow_html=True)
    
    # Top Exploration KPI Cards
    tot_ew = df_drilling["Total_EW"].sum()
    tot_all_wells = df_drilling["Total_Wells"].sum()
    hr_wells = df_drilling["HardRock_EW"].sum()
    sr_wells = df_drilling["SoftRock_EW"].sum()
    saline_area = df_saline["Saline_Area_SqKm"].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Exploratory Boreholes</div>
            <div class="metric-value">{tot_all_wells:,}</div>
            <div class="metric-sub">{tot_ew:,} EW | 435 OW | 168 PZ</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Hard Rock vs Soft Rock Wells</div>
            <div class="metric-value">{hr_wells:,} / {sr_wells:,}</div>
            <div class="metric-sub">70% Precambrian | 30% Alluvial/Gondwana</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Max Alluvial Yield Recorded</div>
            <div class="metric-value">75.0 lps</div>
            <div class="metric-sub">270 m³/hr (Kendrapara / Bhadrak)</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Coastal Saline Hazard Tract</div>
            <div class="metric-value">{saline_area:,} km²</div>
            <div class="metric-sub">42 Blocks across 7 Coastal Districts</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
    
    # Exploration Navigation Sub-views
    exp_view = st.radio(
        "Select Exploration Domain",
        [
            "📊 District Exploratory Inventory (30 Districts)",
            "🧂 Coastal Saline-Fresh Stratigraphy & Artesian Belts",
            "⚙️ Aquifer Hydraulic Properties (Transmissivity & Storativity)",
            "🏛️ Strategic Implications for Jal Jeevan Mission (JJM)"
        ],
        horizontal=True
    )
    
    if exp_view == "📊 District Exploratory Inventory (30 Districts)":
        st.markdown("#### 📊 District-wise Exploratory Drilling & Potential Yield Breakdown")
        
        # Dual Bar Chart of Hard Rock vs Soft Rock Wells
        fig_drilling_bar = px.bar(
            df_drilling,
            x="District",
            y=["HardRock_EW", "SoftRock_EW"],
            title="<b>Exploratory Wells (EW) Drilled by District (Hard Rock vs Soft Rock)</b>",
            labels={"value": "Exploratory Wells Drilled", "variable": "Lithological Terrain"},
            color_discrete_map={"HardRock_EW": "#3b82f6", "SoftRock_EW": "#10b981"}
        )
        fig_drilling_bar.update_layout(
            paper_bgcolor=theme_bg,
            plot_bgcolor=theme_bg,
            font=dict(family="DM Sans, sans-serif", color=theme_text),
            height=380,
            barmode="stack",
            xaxis=dict(gridcolor=grid_color),
            yaxis=dict(gridcolor=grid_color),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_drilling_bar, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown("##### 📋 Complete District Exploration Summary Table")
        st.dataframe(
            df_drilling[["District", "Category", "Formation", "Area_SqKm", "Total_EW", "Total_Wells", "Avg_Yield_lps", "Max_Depth_m"]],
            use_container_width=True,
            hide_index=True,
            height=320
        )
        
    elif exp_view == "🧂 Coastal Saline-Fresh Stratigraphy & Artesian Belts":
        st.markdown("#### 🧂 Coastal Saline Hazard Tract & Deep Fresh Aquifer Architecture")
        st.markdown("""
        In coastal Odisha, a **$8,875\text{ km}^2$ coastal belt across 42 blocks** suffers from salinity hazard. 
        However, CGWB deep exploratory drilling deciphered that **prolific fresh water aquifers lie protected underneath the upper saline layers** between $100\text{ m}$ and $350\text{ m}$ depth!
        """)
        
        sal_c1, sal_c2 = st.columns([5, 5])
        with sal_c1:
            st.markdown("##### 📋 Coastal Saline Hazard District Distribution")
            st.dataframe(df_saline, use_container_width=True, hide_index=True, height=280)
            
        with sal_c2:
            # Saline Area Bar Chart
            fig_sal_bar = px.bar(
                df_saline,
                x="District",
                y="Saline_Area_SqKm",
                color="Saline_Area_SqKm",
                color_continuous_scale="Reds",
                title="<b>Saline Hazard Area (km²) by Coastal District</b>"
            )
            fig_sal_bar.update_layout(
                paper_bgcolor=theme_bg,
                plot_bgcolor=theme_bg,
                font=dict(family="DM Sans, sans-serif", color=theme_text),
                height=280,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_sal_bar, use_container_width=True, config={"displayModeBar": False})
            
        st.markdown("---")
        st.markdown("##### 🌊 Artesian / Auto-Flow Free-Flowing Aquifer Belts")
        st.markdown("""
        <div style="background:var(--bg-subtle); border:1px solid var(--border); border-radius:8px; padding:12px; font-size:0.85rem; line-height:1.5;">
            <b>Key Findings on Free-Flowing Artesian Wells in Odisha:</b><br/>
            • <b>Mayurbhanj Tertiary Basin (Baripada Beds):</b> Confined fossiliferous sandstones sustain auto-flow wells discharging <b>5 to 15 lps</b> naturally without pumps.<br/>
            • <b>Coastal Deltaic Foothill Margins:</b> Confined gravel aquifers at 120-220 mbgl in Cuttack, Puri, and Balasore exhibit piezometric heads rising <b>1 to 5 meters above ground level</b>.<br/>
            • <b>Conservation Mandate:</b> Uncapped free-flowing artesian borewells waste millions of liters of pristine groundwater annually; CGWB mandates <b>sluice valve caps</b> on all artesian heads.
        </div>
        """, unsafe_allow_html=True)
        
    elif exp_view == "⚙️ Aquifer Hydraulic Properties (Transmissivity & Storativity)":
        st.markdown("#### ⚙️ Aquifer Hydraulic Properties & Yield Potential Synthesis")
        st.markdown("Comprehensive transmissivity ($T$), storativity ($S$), and specific yield ($S_y$) derived from CGWB pumping tests:")
        
        st.dataframe(df_hyd, use_container_width=True, hide_index=True, height=220)
        
        # Transmissivity Comparison Bar Chart
        fig_hyd_bar = px.bar(
            df_hyd,
            x="Hydrogeological_Unit",
            y="Specific_Yield_pct",
            color="Development_Potential",
            title="<b>Aquifer Specific Yield (%) & Groundwater Development Potential</b>",
            color_discrete_map={
                "High (MVS / JJM Multi-village schemes)": "#10b981",
                "Moderate to High (Artesian in Mayurbhanj)": "#3b82f6",
                "Moderate (Bhubaneswar-Cuttack urban belt)": "#f59e0b",
                "Moderate (Fractured Borewells down to 120m)": "#8b5cf6",
                "Low (Dug-cum-Borewells / Check Dams required)": "#ef4444"
            }
        )
        fig_hyd_bar.update_layout(
            paper_bgcolor=theme_bg,
            plot_bgcolor=theme_bg,
            font=dict(family="DM Sans, sans-serif", color=theme_text),
            height=340,
            xaxis=dict(tickangle=-15)
        )
        st.plotly_chart(fig_hyd_bar, use_container_width=True, config={"displayModeBar": False})
        
    else: # Strategic Implications for JJM
        st.markdown("#### 🏛️ Strategic Implications for Jal Jeevan Mission & Groundwater Governance")
        
        imp_c1, imp_c2 = st.columns(2)
        with imp_c1:
            st.markdown("""
            <div style="border:1px solid var(--border); border-radius:8px; padding:14px; background:var(--card);">
                <div style="font-weight:700; color:var(--accent); font-size:1rem; margin-bottom:8px;">💧 1. Mega-Piped Water Schemes (MVS) Strategy</div>
                <div style="font-size:0.85rem; color:var(--text); line-height:1.5;">
                    • <b>Deep Alluvial Aquifer Tapping:</b> In coastal districts (Bhadrak, Kendrapara, Jagatsinghpur, Balasore), deep fresh aquifers (150-300m) yield <b>30 to 75 lps</b> of crystal-clear water, eliminating expensive river intake treatment plants.<br/>
                    • <b>Cement Sealing Protocol:</b> Tubewells drilled through upper saline layers must use <b>neat cement slurry seals</b> across the saline horizon (0-120m) to prevent down-hole saltwater leakage.<br/>
                    • <b>Well Spacing Norm:</b> Maintain minimum <b>500m spacing</b> between high-discharge (50 lps) production wells to prevent interference drawdown.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style="border:1px solid var(--border); border-radius:8px; padding:14px; background:var(--card);">
                <div style="font-weight:700; color:#10b981; font-size:1rem; margin-bottom:8px;">🏜️ 2. Drought-Prone Western Districts Water Security</div>
                <div style="font-size:0.85rem; color:var(--text); line-height:1.5;">
                    • <b>10 Drought-Prone Districts:</b> Nuapada, Kalahandi, Bolangir, Bargarh, Sambalpur, Jharsuguda, Deogarh, Sonepur, Boudh, and Kandhamal.<br/>
                    • <b>Deep Fracture Windows:</b> Exploratory drilling proved that <b>2 to 4 potential fracture zones occur between 60m and 150m depth</b>, yielding 3 to 10 lps even during peak summer drought.<br/>
                    • <b>Dug-cum-Borewell Model:</b> Convert dry shallow dug wells into dual-purpose structures with horizontal/vertical exploratory feeder bores.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with imp_c2:
            st.markdown("""
            <div style="border:1px solid var(--border); border-radius:8px; padding:14px; background:var(--card);">
                <div style="font-weight:700; color:#f59e0b; font-size:1rem; margin-bottom:8px;">🌊 3. Saline Water Skimming & Infiltration Galleries</div>
                <div style="font-size:0.85rem; color:var(--text); line-height:1.5;">
                    • <b>Puri-Brahmagiri Coastal Sector:</b> Where saline water occurs down to bedrock, deep borewells fail entirely.<br/>
                    • <b>Radial Skimming Wells:</b> Construct shallow horizontal infiltration galleries tapping the thin freshwater lens (0-15 mbgl) without puncturing the underlying saline interface.<br/>
                    • <b>Throttled Pumping:</b> Restrict daily pumping to <b>6-8 hours/day</b> at low discharge (<5 lps) to prevent saline upconing into the well screen.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style="border:1px solid var(--border); border-radius:8px; padding:14px; background:var(--card);">
                <div style="font-weight:700; color:#8b5cf6; font-size:1rem; margin-bottom:8px;">🏔️ 4. Managed Aquifer Recharge (MAR) Zonation</div>
                <div style="font-size:0.85rem; color:var(--text); line-height:1.5;">
                    • <b>Upstream Crystalline Recharge:</b> High recharge priority for Athgarh Sandstone and weathered granite pediplains using <b>percolation tanks and check dams</b>.<br/>
                    • <b>Subsurface Dykes:</b> Build underground clay/grout cutoff walls across riverbed alluvium to store post-monsoon baseflow for summer drinking supply.<br/>
                    • <b>Fluoride & Iron Dilution:</b> Monsoon artificial recharge accelerates flushing of weathered biotite granites, naturally diluting fluoride concentrations.
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
