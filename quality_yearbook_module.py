import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io

PLOT_LAYOUT = dict(
    margin=dict(l=20, r=20, t=40, b=20),
    font=dict(family="DM Sans, sans-serif")
)

@st.cache_data
def load_quality_yearbook_data():
    dir_path = os.path.dirname(__file__)
    df_trends = pd.read_csv(os.path.join(dir_path, "cgwb_quality_temporal_trends.csv"))
    df_seasonal = pd.read_csv(os.path.join(dir_path, "cgwb_quality_seasonal_dynamics.csv"))
    df_metals = pd.read_csv(os.path.join(dir_path, "cgwb_quality_heavy_metals.csv"))
    
    annex_path = os.path.join(dir_path, "cgwb_quality_yearbook_annexures.csv")
    if os.path.exists(annex_path):
        df_annex = pd.read_csv(annex_path, low_memory=False)
    else:
        df_annex = pd.DataFrame()
        
    return df_trends, df_seasonal, df_metals, df_annex

def render_quality_yearbook_tab(is_dark=False):
    df_trends, df_seasonal, df_metals, df_annex = load_quality_yearbook_data()
    
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">🔬 CGWB Groundwater Quality Year Book (AAP 2024–2025 Synthesis)</div>
        <div class="chart-subtitle">Official State Water Quality Survey by Central Ground Water Board (Published July 2025) — Pre/Post-Monsoon Dilution Dynamics, 8-Year Temporal Contaminant Trends, Toxic Heavy Metals & Published Data Sheets</div>
    """, unsafe_allow_html=True)
    
    # Top Metrics Cards
    tot_mon = df_seasonal["PostM_Samples"].sum()
    tot_improved = df_seasonal["EC_Improved_Wells"].sum()
    tot_deteriorated = df_seasonal["EC_Deteriorated_Wells"].sum()
    pct_improved = (tot_improved / (tot_improved + tot_deteriorated)) * 100 if (tot_improved + tot_deteriorated) > 0 else 0
    
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Year Book Survey Network</div>
            <div class="metric-value">{tot_mon:,} Wells</div>
            <div class="metric-sub">618 Post-M & 459 Pre-M Stations (30 Districts)</div>
        </div>
        """, unsafe_allow_html=True)
    with q2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Monsoon EC Dilution Rate</div>
            <div class="metric-value">{pct_improved:.1f}%</div>
            <div class="metric-sub">{tot_improved} Wells Improved Post-Monsoon</div>
        </div>
        """, unsafe_allow_html=True)
    with q3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">8-Yr Peak Nitrate Exceedance</div>
            <div class="metric-value">16.2%</div>
            <div class="metric-sub">Persistent Agricultural Leaching Corridor</div>
        </div>
        """, unsafe_allow_html=True)
    with q4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Published Annexure Records</div>
            <div class="metric-value">{len(df_annex):,} Rows</div>
            <div class="metric-sub">14 Official Survey Data Sheets</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
    
    # Navigation Radio for Sub-topics
    q_subview = st.radio(
        "Select Quality Survey Dimension",
        [
            "🌦️ Pre-Monsoon vs Post-Monsoon Seasonal Dynamics (2024–25)",
            "📈 8-Year Temporal Contaminant Trends (2017–2024)",
            "☢️ Toxic Heavy Metals & Radionuclides Surveillance",
            "📋 Published Annexure Data Sheets Explorer (1,280 Records)"
        ],
        horizontal=True
    )
    
    if q_subview == "🌦️ Pre-Monsoon vs Post-Monsoon Seasonal Dynamics (2024–25)":
        st.markdown("#### 🌦️ Impact of Monsoon Recharge on Contaminant Dilution vs Geogenic Leaching")
        st.markdown("""
        Monsoon precipitation has a **two-fold hydrogeological impact** in Odisha:
        1. **Dilution of Soluble Ions (EC / Salinity)**: Fresh rainwater infiltration significantly diluted electrical conductivity across **Ganjam, Puri, and Boudh** (improved in >60% of stations).
        2. **Post-Recharge Geogenic Leaching (Fluoride)**: In crystalline granite terrains (Kalahandi, Sonepur, Sundargarh), monsoon recharge slightly raises alkaline groundwater pH, accelerating fluorite dissolution ($\text{CaF}_2$) and raising post-monsoon Fluoride exceedance from **1.74% to 2.91%**.
        """)
        
        # Dual Bar Chart of Seasonal Exceedances
        fig_season_f = px.bar(
            df_seasonal[df_seasonal["PostM_F_Exceed_Pct"] > 0].sort_values(by="PostM_F_Exceed_Pct", ascending=False),
            x="District",
            y=["PreM_F_Exceed_Pct", "PostM_F_Exceed_Pct"],
            title="<b>Fluoride Exceedance (>1.5 mg/L) %: Pre-Monsoon vs Post-Monsoon 2024</b>",
            labels={"value": "Exceedance Percentage (%)", "variable": "Sampling Season"},
            color_discrete_map={"PreM_F_Exceed_Pct": "#f59e0b", "PostM_F_Exceed_Pct": "#ef4444"},
            barmode="group"
        )
        fig_season_f.update_layout(
            paper_bgcolor=theme_bg,
            plot_bgcolor=theme_bg,
            font=dict(family="DM Sans, sans-serif", color=theme_text),
            height=320,
            xaxis=dict(gridcolor=grid_color),
            yaxis=dict(gridcolor=grid_color),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_season_f, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown("##### 📋 Complete District Seasonal Dynamics Data Sheet")
        st.dataframe(
            df_seasonal,
            use_container_width=True,
            hide_index=True,
            height=280
        )
        
    elif q_subview == "📈 8-Year Temporal Contaminant Trends (2017–2024)":
        st.markdown("#### 📈 Multi-Year Temporal Evolution of Major Contaminants (2017 to 2024)")
        st.markdown("Tracking long-term trends in the percentage of monitoring stations exceeding BIS drinking water permissible limits:")
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_trends["Year"], y=df_trends["Nitrate_Exceed_Pct"],
            mode="lines+markers", name="Nitrate (>45 mg/L)",
            line=dict(color="#f97316", width=3), marker=dict(size=8)
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_trends["Year"], y=df_trends["Fluoride_Exceed_Pct"],
            mode="lines+markers", name="Fluoride (>1.5 mg/L)",
            line=dict(color="#ef4444", width=3), marker=dict(size=8)
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_trends["Year"], y=df_trends["EC_Exceed_Pct"],
            mode="lines+markers", name="Salinity EC (>3000 µS/cm)",
            line=dict(color="#3b82f6", width=2, dash="dash"), marker=dict(size=7)
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_trends["Year"], y=df_trends["Uranium_Exceed_Pct"],
            mode="lines+markers", name="Uranium (>30 µg/L)",
            line=dict(color="#8b5cf6", width=2, dash="dot"), marker=dict(size=7)
        ))
        
        fig_trend.update_layout(
            paper_bgcolor=theme_bg,
            plot_bgcolor=theme_bg,
            font=dict(family="DM Sans, sans-serif", color=theme_text),
            height=360,
            title="<b>8-Year Contaminant Exceedance Rate (% of Wells Exceeding BIS Limits)</b>",
            xaxis=dict(title="Survey Year / Season", gridcolor=grid_color),
            yaxis=dict(title="Percentage of Locations Exceeding BIS Limit (%)", gridcolor=grid_color),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": True})
        
        st.dataframe(df_trends, use_container_width=True, hide_index=True)
        
    elif q_subview == "☢️ Toxic Heavy Metals & Radionuclides Surveillance":
        st.markdown("#### ☢️ Trace & Toxic Heavy Metals Surveillance (Table 20 & Annexures 5–11)")
        st.markdown("""
        In addition to general physicochemical parameters, CGWB carries out specialized **Inductively Coupled Plasma Mass Spectrometry (ICP-MS)** screening for trace toxic metals and radionuclides:
        """)
        
        st.dataframe(df_metals, use_container_width=True, hide_index=True, height=260)
        
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            st.markdown("""
            <div style="border:1px solid var(--border); border-radius:8px; padding:12px; background:var(--card);">
                <div style="font-weight:700; color:#8b5cf6; font-size:0.95rem; margin-bottom:6px;">☢️ 1. Uranium Radionuclide Screening (Annexure 05)</div>
                <div style="font-size:0.83rem; color:var(--text); line-height:1.4;">
                    • <b>Permissible Limit:</b> 30.0 µg/L (AERB & WHO guidelines).<br/>
                    • <b>Hotspot Identified:</b> Bargarh (Attabira & Bhedan blocks) where granite pegmatites and agricultural phosphate fertilizer application mobilize uranium.<br/>
                    • <b>Health Risk:</b> Primary concern is chemical nephrotoxicity (kidney tubule damage) rather than radiological radiation.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m_c2:
            st.markdown("""
            <div style="border:1px solid var(--border); border-radius:8px; padding:12px; background:var(--card);">
                <div style="font-weight:700; color:#ef4444; font-size:0.95rem; margin-bottom:6px;">⚠️ 2. Lead & Arsenic Surveillance (Annexures 06 & 07)</div>
                <div style="font-size:0.83rem; color:var(--text); line-height:1.4;">
                    • <b>Lead (Pb > 10 µg/L):</b> Isolated pockets in industrial mining corridors (Jharsuguda, Angul) requiring effluent discharge containment.<br/>
                    • <b>Arsenic (As > 10 µg/L):</b> Confined to deep reducing deltaic clay-sand transitions in localized coastal pockets.<br/>
                    • <b>Mitigation:</b> Deploy specialized granular ferric hydroxide (GFH) or activated alumina point-of-use filtration.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    else: # Published Annexures Data Sheets Explorer
        st.markdown("#### 📋 Published Quality Year Book Annexure Data Sheets Explorer")
        st.markdown("Explore and export the official published monitoring station data sheets directly from the CGWB report:")
        
        if not df_annex.empty:
            annex_sources = sorted([s for s in df_annex["Annexure_Source"].dropna().unique()])
            sel_annex = st.selectbox("Select Published Annexure Sheet", annex_sources, index=0)
            
            sub_annex = df_annex[df_annex["Annexure_Source"] == sel_annex]
            
            # Clean empty columns for display
            clean_sub = sub_annex.dropna(how="all", axis=1)
            
            st.dataframe(clean_sub, use_container_width=True, height=350)
            
            # CSV Download Button
            csv_data = io.StringIO()
            clean_sub.to_csv(csv_data, index=False)
            st.download_button(
                label=f"📥 Download {sel_annex} (CSV)",
                data=csv_data.getvalue(),
                file_name=f"CGWB_Yearbook_{sel_annex.replace(' ', '_')[:30]}.csv",
                mime="text/csv"
            )
        else:
            st.info("Annexure data sheet records loading...")

    st.markdown("</div>", unsafe_allow_html=True)
