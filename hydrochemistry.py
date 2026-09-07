import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Standard BIS IS 10500:2012 Drinking Water Permissible Limits
BIS_LIMITS = {
    "pH": 8.5,
    "TDS (mg/L)": 500.0,
    "TH": 300.0,
    "Ca": 75.0,
    "Mg": 30.0,
    "Cl": 250.0,
    "SO4": 200.0,
    "NO3": 45.0,
    "F": 1.0,
    "Fe": 1.0
}

# Unit Weights for WQI (Weighted Arithmetic Method)
inv_sum = sum([1.0 / s for s in BIS_LIMITS.values()])
k_val = 1.0 / inv_sum
WQI_WEIGHTS = {param: k_val / std for param, std in BIS_LIMITS.items()}

def calculate_wqi_single_row(row):
    wi_qi_sum = 0.0
    wi_sum = 0.0
    
    for param, std in BIS_LIMITS.items():
        val = row.get(param)
        if pd.isna(val) and param == "TDS (mg/L)":
            val = row.get("EC", np.nan) * 0.65 if pd.notna(row.get("EC")) else np.nan
            
        if pd.notna(val) and val is not None:
            try:
                num_val = float(val)
                if param == "pH":
                    qi = ((num_val - 7.0) / (8.5 - 7.0)) * 100.0 if num_val >= 7.0 else ((7.0 - num_val) / (7.0 - 6.5)) * 100.0
                else:
                    qi = (num_val / std) * 100.0
                wi = WQI_WEIGHTS[param]
                wi_qi_sum += wi * qi
                wi_sum += wi
            except:
                pass
    if wi_sum > 0:
        return wi_qi_sum / wi_sum
    return np.nan

def classify_wqi(wqi):
    if pd.isna(wqi): return "Indeterminate"
    if wqi < 50: return "Excellent (<50)"
    elif wqi < 100: return "Good (50-100)"
    elif wqi < 200: return "Poor (100-200)"
    elif wqi < 300: return "Very Poor (200-300)"
    else: return "Unsuitable (>300)"

def calculate_corrosivity_single_row(row):
    ph = row.get("pH")
    ec = row.get("EC")
    ca = row.get("Ca")
    hco3 = row.get("HCO3", 0)
    co3 = row.get("CO3", 0)
    
    if pd.isna(ph) or pd.isna(ec) or pd.isna(ca):
        return np.nan, np.nan, "Indeterminate"
    
    try:
        ph = float(ph)
        tds = float(ec) * 0.65
        alk = (float(hco3) * 0.82) + (float(co3) * 1.67)
        ca_hard = float(ca) * 2.497
        
        if alk <= 0: alk = 10.0
        if ca_hard <= 0: ca_hard = 10.0
        if tds <= 0: tds = 50.0
        
        A_f = (np.log10(tds) - 1.0) / 10.0
        B_f = 2.0  # constant at 25 deg C
        C_f = np.log10(ca_hard) - 0.4
        D_f = np.log10(alk)
        
        phs = (9.3 + A_f + B_f) - (C_f + D_f)
        lsi = ph - phs
        rsi = 2.0 * phs - ph
        
        if lsi < -0.5 or rsi > 8.5:
            cat = "Corrosive / Aggressive"
        elif lsi > 0.5 or rsi < 6.5:
            cat = "Scale Forming (Encrusting)"
        else:
            cat = "Balanced / Non-Aggressive"
            
        return round(lsi, 2), round(rsi, 2), cat
    except:
        return np.nan, np.nan, "Indeterminate"


def calculate_hydrochemistry(df):
    """
    Computes meq/L for major cations and anions, ternary percentages,
    SAR, %Na, USSL classification, Wilcox classification, Gibbs ratios,
    WQI (Water Quality Index), and LSI/RSI pipe corrosivity indices.
    """
    df_calc = df.copy()
    
    eq_weights = {
        "Ca": 20.04,
        "Mg": 12.15,
        "Na": 22.99,
        "K": 39.10,
        "Cl": 35.45,
        "SO4": 48.03,
        "HCO3": 61.02,
        "CO3": 30.00
    }
    
    for ion, eq in eq_weights.items():
        if ion in df_calc.columns:
            df_calc[f"{ion}_meq"] = pd.to_numeric(df_calc[ion], errors="coerce").fillna(0) / eq
        else:
            df_calc[f"{ion}_meq"] = 0.0
            
    # Cation & Anion Totals
    df_calc["Total_Cations"] = df_calc["Ca_meq"] + df_calc["Mg_meq"] + df_calc["Na_meq"] + df_calc["K_meq"]
    df_calc["Total_Anions"] = df_calc["Cl_meq"] + df_calc["SO4_meq"] + df_calc["HCO3_meq"] + df_calc["CO3_meq"]
    
    # Ternary percentages (0 - 100%)
    has_cations = df_calc["Total_Cations"] > 0
    has_anions = df_calc["Total_Anions"] > 0
    
    df_calc["Ca_pct"] = np.where(has_cations, (df_calc["Ca_meq"] / df_calc["Total_Cations"]) * 100.0, np.nan)
    df_calc["Mg_pct"] = np.where(has_cations, (df_calc["Mg_meq"] / df_calc["Total_Cations"]) * 100.0, np.nan)
    df_calc["Na_K_pct"] = np.where(has_cations, ((df_calc["Na_meq"] + df_calc["K_meq"]) / df_calc["Total_Cations"]) * 100.0, np.nan)
    
    df_calc["Cl_pct"] = np.where(has_anions, (df_calc["Cl_meq"] / df_calc["Total_Anions"]) * 100.0, np.nan)
    df_calc["SO4_pct"] = np.where(has_anions, (df_calc["SO4_meq"] / df_calc["Total_Anions"]) * 100.0, np.nan)
    df_calc["HCO3_CO3_pct"] = np.where(has_anions, ((df_calc["HCO3_meq"] + df_calc["CO3_meq"]) / df_calc["Total_Anions"]) * 100.0, np.nan)
    
    # Diamond 2D Transformation (Piper Diamond Projection)
    df_calc["Diam_X"] = np.where(
        has_cations & has_anions, 
        0.5 * ( (df_calc["Cl_pct"] + df_calc["SO4_pct"]) - (df_calc["Ca_pct"] + df_calc["Mg_pct"]) + 100.0 ), 
        np.nan
    ).round(2)
    
    df_calc["Diam_Y"] = np.where(
        has_cations & has_anions, 
        (df_calc["Na_K_pct"] + df_calc["SO4_pct"] + df_calc["Cl_pct"]) / 2.0, 
        np.nan
    ).round(2)
    
    # Hydrochemical Facies Classification
    def classify_facies(row):
        ca = row.get("Ca_pct", 0)
        mg = row.get("Mg_pct", 0)
        na_k = row.get("Na_K_pct", 0)
        hco3 = row.get("HCO3_CO3_pct", 0)
        cl = row.get("Cl_pct", 0)
        so4 = row.get("SO4_pct", 0)
        if pd.isna(ca) or pd.isna(hco3) or (ca == 0 and hco3 == 0): return "Indeterminate"
        
        alkaline_earths = ca + mg
        alkalies = na_k
        weak_acids = hco3
        strong_acids = cl + so4
        
        if alkaline_earths > alkalies and weak_acids > strong_acids:
            return "Ca²⁺ - Mg²⁺ - HCO₃⁻ (Fresh Recharge)"
        elif alkalies > alkaline_earths and strong_acids > weak_acids:
            return "Na⁺ - K⁺ - Cl⁻ - SO₄²⁻ (Saline / Marine)"
        elif alkaline_earths > alkalies and strong_acids > weak_acids:
            return "Ca²⁺ - Mg²⁺ - Cl⁻ - SO₄²⁻ (Mixed / Mine Water)"
        elif alkalies > alkaline_earths and weak_acids > strong_acids:
            return "Na⁺ - K⁺ - HCO₃⁻ (Ion-Exchange Water)"
        else:
            return "Mixed Facies"
        
    df_calc["Water_Type"] = df_calc.apply(classify_facies, axis=1)
    
    # SAR (Sodium Adsorption Ratio)
    sar_denom = np.sqrt((df_calc["Ca_meq"] + df_calc["Mg_meq"]) / 2.0)
    df_calc["SAR"] = np.where(sar_denom > 0, df_calc["Na_meq"] / sar_denom, 0.0).round(2)
    
    # %Na
    df_calc["Pct_Na"] = np.where(has_cations, ((df_calc["Na_meq"] + df_calc["K_meq"]) / df_calc["Total_Cations"]) * 100.0, 0.0).round(1)
    
    # USSL Class
    def calc_ussl(row):
        ec = row.get("EC", 0)
        sar = row.get("SAR", 0)
        if pd.isna(ec) or pd.isna(sar) or ec == 0: return "Unknown"
        c = "C1" if ec < 250 else ("C2" if ec < 750 else ("C3" if ec < 2250 else "C4"))
        s = "S1" if sar < 10 else ("S2" if sar < 18 else ("S3" if sar < 26 else "S4"))
        return f"{c}-{s}"
    df_calc["USSL_Class"] = df_calc.apply(calc_ussl, axis=1)
    
    # Wilcox Class
    def calc_wilcox(row):
        p = row.get("Pct_Na", 0)
        ec = row.get("EC", 0)
        if pd.isna(p) or pd.isna(ec) or ec == 0: return "Unknown"
        if p < 20 and ec < 250: return "Excellent"
        elif p < 40 and ec < 750: return "Good"
        elif p < 60 and ec < 2000: return "Permissible"
        elif p < 80 and ec < 3000: return "Doubtful"
        else: return "Unsuitable"
    df_calc["Wilcox_Class"] = df_calc.apply(calc_wilcox, axis=1)
    
    # Gibbs Ratios
    cl_v = df_calc["Cl"].fillna(0)
    hco3_v = df_calc["HCO3"].fillna(0)
    na_v = df_calc["Na"].fillna(0)
    k_v = df_calc["K"].fillna(0)
    ca_v = df_calc["Ca"].fillna(0)
    
    df_calc["Gibbs_Anion"] = np.where((cl_v + hco3_v) > 0, cl_v / (cl_v + hco3_v), np.nan).round(3)
    df_calc["Gibbs_Cation"] = np.where((na_v + k_v + ca_v) > 0, (na_v + k_v) / (na_v + k_v + ca_v), np.nan).round(3)
    
    if "TDS (mg/L)" not in df_calc.columns:
        df_calc["TDS (mg/L)"] = (df_calc["EC"].fillna(0) * 0.64).round(1)
        
    # --- WQI Calculation ---
    df_calc["WQI"] = df_calc.apply(calculate_wqi_single_row, axis=1).round(1)
    df_calc["WQI_Class"] = df_calc["WQI"].apply(classify_wqi)
    
    # --- Corrosivity Calculation ---
    corr_res = df_calc.apply(calculate_corrosivity_single_row, axis=1)
    df_calc["LSI"] = [r[0] for r in corr_res]
    df_calc["RSI"] = [r[1] for r in corr_res]
    df_calc["Corrosivity_Class"] = [r[2] for r in corr_res]
    
    return df_calc


def create_piper_diagram(df_calc, is_dark=False):
    """
    Constructs a complete Piper Trilinear Diagram (Cation Ternary, Anion Ternary, Diamond Facies).
    """
    valid = df_calc[df_calc["Ca_pct"].notna() & df_calc["Cl_pct"].notna()].copy()
    if valid.empty:
        return go.Figure().update_layout(title="Insufficient Cation/Anion Data for Piper Diagram")
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "ternary"}, {"type": "ternary"}]],
        subplot_titles=("⚡ Cation Ternary (Ca²⁺ - Mg²⁺ - Na⁺+K⁺)", "🧪 Anion Ternary (HCO₃⁻+CO₃²⁻ - SO₄²⁻ - Cl⁻)")
    )
    
    # Cation Ternary
    fig.add_trace(go.Scatterternary(
        a=valid["Mg_pct"],
        b=valid["Ca_pct"],
        c=valid["Na_K_pct"],
        mode="markers",
        marker=dict(
            size=7,
            color=valid["EC"].fillna(500),
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="EC (µS/cm)", x=1.05, len=0.8)
        ),
        text=valid["Location"],
        customdata=valid[["District", "Water_Type"]],
        hovertemplate="<b>%{text}</b><br>District: %{customdata[0]}<br>Facies: %{customdata[1]}<br>Mg: %{a:.1f}%<br>Ca: %{b:.1f}%<br>Na+K: %{c:.1f}%<extra></extra>",
        name="Cations"
    ), row=1, col=1)
    
    # Anion Ternary
    fig.add_trace(go.Scatterternary(
        a=valid["SO4_pct"],
        b=valid["HCO3_CO3_pct"],
        c=valid["Cl_pct"],
        mode="markers",
        marker=dict(
            size=7,
            color=valid["EC"].fillna(500),
            colorscale="Viridis",
            showscale=False
        ),
        text=valid["Location"],
        customdata=valid[["District", "Water_Type"]],
        hovertemplate="<b>%{text}</b><br>District: %{customdata[0]}<br>Facies: %{customdata[1]}<br>SO4: %{a:.1f}%<br>HCO3: %{b:.1f}%<br>Cl: %{c:.1f}%<extra></extra>",
        name="Anions"
    ), row=1, col=2)
    
    fig.update_layout(
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        ternary=dict(
            sum=100,
            aaxis=dict(title="Mg²⁺ %", min=0.01),
            baxis=dict(title="Ca²⁺ %", min=0.01),
            caxis=dict(title="Na⁺+K⁺ %", min=0.01),
            bgcolor=theme_bg
        ),
        ternary2=dict(
            sum=100,
            aaxis=dict(title="SO₄²⁻ %", min=0.01),
            baxis=dict(title="HCO₃⁻+CO₃²⁻ %", min=0.01),
            caxis=dict(title="Cl⁻ %", min=0.01),
            bgcolor=theme_bg
        ),
        margin=dict(l=20, r=40, t=50, b=20),
        height=480,
        showlegend=False
    )
    return fig


def create_piper_diamond(df_calc, is_dark=False):
    """
    Constructs the central Piper diamond projection.
    """
    valid = df_calc[df_calc["Diam_X"].notna() & df_calc["Diam_Y"].notna()].copy()
    if valid.empty:
        return go.Figure().update_layout(title="No Diamond projection data")
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    fig = px.scatter(
        valid,
        x="Diam_X",
        y="Diam_Y",
        color="Water_Type",
        hover_name="Location",
        hover_data=["District", "EC", "pH"],
        color_discrete_map={
            "Ca²⁺ - Mg²⁺ - HCO₃⁻ (Fresh Recharge)": "#22c55e",
            "Na⁺ - K⁺ - Cl⁻ - SO₄²⁻ (Saline / Marine)": "#ef4444",
            "Ca²⁺ - Mg²⁺ - Cl⁻ - SO₄²⁻ (Mixed / Mine Water)": "#f59e0b",
            "Na⁺ - K⁺ - HCO₃⁻ (Ion-Exchange Water)": "#3b82f6",
            "Mixed Facies": "#a855f7"
        },
        opacity=0.85
    )
    
    # Diamond boundaries
    fig.add_shape(type="line", x0=50, y0=0, x1=100, y1=50, line=dict(color=grid_color, width=1.5))
    fig.add_shape(type="line", x0=100, y0=50, x1=50, y1=100, line=dict(color=grid_color, width=1.5))
    fig.add_shape(type="line", x0=50, y0=100, x1=0, y1=50, line=dict(color=grid_color, width=1.5))
    fig.add_shape(type="line", x0=0, y0=50, x1=50, y1=0, line=dict(color=grid_color, width=1.5))
    
    fig.update_layout(
        title="💎 Piper Diamond Facies Field (Central Projection)",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        xaxis=dict(title="(Cl⁻ + SO₄²⁻) - (Ca²⁺ + Mg²⁺) Component", range=[-5, 105], showgrid=False),
        yaxis=dict(title="(Na⁺ + K⁺ + SO₄²⁻ + Cl⁻) Component", range=[-5, 105], showgrid=False),
        margin=dict(l=40, r=20, t=50, b=40),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_wilcox_diagram(df_calc, is_dark=False):
    """
    Wilcox Diagram: %Na vs Electrical Conductivity (EC).
    """
    valid = df_calc[df_calc["Pct_Na"].notna() & df_calc["EC"].notna() & (df_calc["EC"] > 0)].copy()
    
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    
    fig = px.scatter(
        valid,
        x="EC",
        y="Pct_Na",
        color="Wilcox_Class",
        hover_name="Location",
        hover_data=["District", "SAR", "EC"],
        color_discrete_map={
            "Excellent": "#22c55e",
            "Good": "#3b82f6",
            "Permissible": "#f59e0b",
            "Doubtful": "#ea580c",
            "Unsuitable": "#ef4444"
        },
        opacity=0.85
    )
    
    fig.update_layout(
        title="🌾 Wilcox Diagram for Irrigation Water Quality",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        xaxis=dict(title="Electrical Conductivity EC (µS/cm)", type="log", range=[1.5, 4.2]),
        yaxis=dict(title="Sodium Percentage (%Na)", range=[0, 100]),
        margin=dict(l=40, r=20, t=50, b=40),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_ussl_diagram(df_calc, is_dark=False):
    """
    USSL (United States Salinity Laboratory) Diagram: SAR vs EC.
    """
    valid = df_calc[df_calc["SAR"].notna() & df_calc["EC"].notna() & (df_calc["EC"] > 0)].copy()
    
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    fig = px.scatter(
        valid,
        x="EC",
        y="SAR",
        color="USSL_Class",
        hover_name="Location",
        hover_data=["District", "EC", "SAR"],
        color_discrete_sequence=px.colors.qualitative.Bold,
        opacity=0.85
    )
    
    # Salinity thresholds
    for x_val in [250, 750, 2250]:
        fig.add_shape(type="line", x0=x_val, y0=0, x1=x_val, y1=30, line=dict(color=grid_color, dash="dash"))
    # Sodium thresholds
    for y_val in [10, 18, 26]:
        fig.add_shape(type="line", x0=100, y0=y_val, x1=5000, y1=y_val, line=dict(color=grid_color, dash="dash"))
        
    fig.update_layout(
        title="💧 USSL Salinity Hazard vs Sodium Hazard Classification",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        xaxis=dict(title="Electrical Conductivity EC (µS/cm) [Log Scale]", type="log", range=[2, 4]),
        yaxis=dict(title="Sodium Adsorption Ratio (SAR)", range=[0, 30]),
        margin=dict(l=40, r=20, t=50, b=40),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_gibbs_diagrams(df_calc, is_dark=False):
    """
    Gibbs Boomerang Diagrams:
    1. Gibbs Anion: Cl / (Cl + HCO3) vs TDS
    2. Gibbs Cation: (Na + K) / (Na + K + Ca) vs TDS
    """
    valid = df_calc[df_calc["TDS (mg/L)"].notna() & (df_calc["TDS (mg/L)"] > 0)].copy()
    
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("🌧️ Gibbs Ratio I (Anion Ratio)", "⛰️ Gibbs Ratio II (Cation Ratio)")
    )
    
    fig.add_trace(go.Scatter(
        x=valid["Gibbs_Anion"],
        y=valid["TDS (mg/L)"],
        mode="markers",
        marker=dict(size=7, color="#3b82f6", opacity=0.8),
        text=valid["Location"],
        customdata=valid[["District", "TDS (mg/L)", "Gibbs_Anion"]],
        hovertemplate="<b>%{text}</b><br>District: %{customdata[0]}<br>TDS: %{customdata[1]} mg/L<br>Anion Ratio: %{customdata[2]:.3f}<extra></extra>",
        name="Anion Ratio"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=valid["Gibbs_Cation"],
        y=valid["TDS (mg/L)"],
        mode="markers",
        marker=dict(size=7, color="#10b981", opacity=0.8),
        text=valid["Location"],
        customdata=valid[["District", "TDS (mg/L)", "Gibbs_Cation"]],
        hovertemplate="<b>%{text}</b><br>District: %{customdata[0]}<br>TDS: %{customdata[1]} mg/L<br>Cation Ratio: %{customdata[2]:.3f}<extra></extra>",
        name="Cation Ratio"
    ), row=1, col=2)
    
    for col_idx in [1, 2]:
        fig.add_annotation(x=0.5, y=2.5, text="<b>Rock-Water Interaction</b>", showarrow=False, font=dict(color="#10b981", size=10), row=1, col=col_idx)
        fig.add_annotation(x=0.85, y=3.4, text="<b>Evaporation</b>", showarrow=False, font=dict(color="#ef4444", size=10), row=1, col=col_idx)
        fig.add_annotation(x=0.15, y=1.5, text="<b>Precipitation</b>", showarrow=False, font=dict(color="#3b82f6", size=10), row=1, col=col_idx)
    
    fig.update_xaxes(title_text="Cl⁻ / (Cl⁻ + HCO₃⁻)", range=[0, 1], gridcolor=grid_color, row=1, col=1)
    fig.update_xaxes(title_text="(Na⁺ + K⁺) / (Na⁺ + K⁺ + Ca²⁺)", range=[0, 1], gridcolor=grid_color, row=1, col=2)
    fig.update_yaxes(title_text="TDS (mg/L) [Log Scale]", type="log", range=[1, 4], gridcolor=grid_color, row=1, col=1)
    fig.update_yaxes(title_text="TDS (mg/L) [Log Scale]", type="log", range=[1, 4], gridcolor=grid_color, row=1, col=2)
    
    fig.update_layout(
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        margin=dict(l=40, r=20, t=50, b=40),
        height=480,
        showlegend=False
    )
    return fig


def create_bivariate_scatter(df_calc, x_param, y_param, color_param=None, is_dark=False):
    """
    Constructs an interactive hydrogeochemical bivariate scatter diagram with 1:1 equiline and OLS regression.
    """
    valid = df_calc[[x_param, y_param] + ([color_param] if color_param else []) + ["Location", "District"]].dropna()
    if valid.empty:
        return go.Figure().update_layout(title="No data available for selected pair")
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    fig = px.scatter(
        valid,
        x=x_param,
        y=y_param,
        color=color_param if color_param else None,
        hover_name="Location",
        hover_data=["District"],
        trendline="ols",
        trendline_color_override="#ef4444" if not color_param else None,
        color_discrete_sequence=px.colors.qualitative.Safe,
        opacity=0.85
    )
    
    max_val = max(valid[x_param].max(), valid[y_param].max())
    min_val = min(valid[x_param].min(), valid[y_param].min())
    if min_val >= 0 and max_val > 0:
        fig.add_shape(
            type="line",
            x0=0, y0=0, x1=max_val, y1=max_val,
            line=dict(color=grid_color, dash="dot", width=1.5)
        )
        fig.add_annotation(
            x=max_val * 0.8, y=max_val * 0.8,
            text="1:1 Equiline",
            showarrow=False,
            font=dict(color=grid_color, size=10)
        )
    
    fig.update_layout(
        title=f"📊 Hydrochemical Bivariate Scatter: {y_param} vs {x_param}",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        xaxis=dict(gridcolor=grid_color),
        yaxis=dict(gridcolor=grid_color),
        margin=dict(l=40, r=20, t=50, b=40),
        height=500
    )
    return fig


def create_wqi_summary_chart(df_calc, is_dark=False):
    """
    Renders WQI classification donut chart & score distribution.
    """
    valid = df_calc[df_calc["WQI_Class"] != "Indeterminate"].copy()
    if valid.empty:
        return go.Figure().update_layout(title="Insufficient Data for WQI Distribution")
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    
    counts = valid["WQI_Class"].value_counts().reset_index()
    counts.columns = ["WQI Class", "Count"]
    
    wqi_colors = {
        "Excellent (<50)": "#22c55e",
        "Good (50-100)": "#3b82f6",
        "Poor (100-200)": "#f59e0b",
        "Very Poor (200-300)": "#ea580c",
        "Unsuitable (>300)": "#ef4444"
    }
    
    fig = px.pie(
        counts,
        names="WQI Class",
        values="Count",
        hole=0.45,
        color="WQI Class",
        color_discrete_map=wqi_colors,
        title="<b>Water Quality Index (WA-WQI) Potability Distribution</b>"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig


def create_corrosivity_diagram(df_calc, is_dark=False):
    """
    Renders Langelier Saturation Index (LSI) vs Ryznar Stability Index (RSI) pipe scaling/corrosion quadrant.
    """
    valid = df_calc[df_calc["LSI"].notna() & df_calc["RSI"].notna()].copy()
    if valid.empty:
        return go.Figure().update_layout(title="Insufficient data for Corrosivity (LSI/RSI) analysis")
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    corr_colors = {
        "Corrosive / Aggressive": "#ef4444",
        "Balanced / Non-Aggressive": "#22c55e",
        "Scale Forming (Encrusting)": "#3b82f6"
    }
    
    fig = px.scatter(
        valid,
        x="LSI",
        y="RSI",
        color="Corrosivity_Class",
        hover_name="Location",
        hover_data=["District", "pH", "Ca", "EC"],
        color_discrete_map=corr_colors,
        opacity=0.85
    )
    
    # Add engineering classification reference thresholds
    fig.add_shape(type="line", x0=-0.5, y0=4, x1=-0.5, y1=12, line=dict(color=grid_color, dash="dash"))
    fig.add_shape(type="line", x0=0.5, y0=4, x1=0.5, y1=12, line=dict(color=grid_color, dash="dash"))
    fig.add_shape(type="line", x0=-3, y0=6.5, x1=3, y1=6.5, line=dict(color=grid_color, dash="dash"))
    fig.add_shape(type="line", x0=-3, y0=8.5, x1=3, y1=8.5, line=dict(color=grid_color, dash="dash"))
    
    # Annotate Engineering Zones
    fig.add_annotation(x=1.5, y=5.5, text="<b>Heavy Scaling Zone</b><br>(Pipe Clogging)", showarrow=False, font=dict(color="#3b82f6", size=10))
    fig.add_annotation(x=0.0, y=7.5, text="<b>Balanced Zone</b><br>(Protective Film)", showarrow=False, font=dict(color="#22c55e", size=10))
    fig.add_annotation(x=-1.5, y=10.0, text="<b>Corrosive Zone</b><br>(Metal Leaching)", showarrow=False, font=dict(color="#ef4444", size=10))
    
    fig.update_layout(
        title="<b>🛠️ Langelier (LSI) vs Ryznar (RSI) Pipe Corrosivity & Scaling Matrix</b>",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        xaxis=dict(title="Langelier Saturation Index (LSI)", range=[-3, 3], gridcolor=grid_color),
        yaxis=dict(title="Ryznar Stability Index (RSI)", range=[4, 12], gridcolor=grid_color),
        margin=dict(l=40, r=20, t=50, b=40),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_schoeller_diagram(df_calc, group_by="Aquifer_System", is_dark=False):
    """
    Renders Schoeller Semi-Logarithmic Diagram across 6 major ionic species.
    """
    ions = ["Ca_meq", "Mg_meq", "Na_meq", "Cl_meq", "SO4_meq", "HCO3_meq"]
    ion_labels = ["Ca²⁺", "Mg²⁺", "Na⁺+K⁺", "Cl⁻", "SO₄²⁻", "HCO₃⁻"]
    
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    fig = go.Figure()
    
    if group_by in df_calc.columns:
        for grp_name, grp in df_calc.groupby(group_by):
            if len(grp) < 2: continue
            means = [grp[col].dropna().mean() for col in ions]
            means_log = [m if m > 0.01 else 0.01 for m in means]
            
            fig.add_trace(go.Scatter(
                x=ion_labels,
                y=means_log,
                mode="lines+markers",
                name=f"{grp_name} (n={len(grp)})",
                line=dict(width=2.2),
                marker=dict(size=7),
                hovertemplate=f"<b>Group: {grp_name}</b><br>Ion: %{{x}}<br>Mean Conc: %{{y:.2f}} meq/L<extra></extra>"
            ))
            
    fig.update_layout(
        title=f"<b>📈 Schoeller Semi-Logarithmic Diagram (Averaged by {group_by.replace('_', ' ')})</b>",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        yaxis=dict(type="log", title="Ionic Concentration (meq/L) [Log Scale]", gridcolor=grid_color),
        xaxis=dict(title="Major Hydrochemical Ions", gridcolor=grid_color),
        height=480,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    return fig


def create_durov_diagram(df_calc, is_dark=False):
    """
    Renders Extended Durov Diagram combining Facies + pH + TDS subplots.
    """
    valid = df_calc[df_calc["Total_Cations"] > 0 & (df_calc["Total_Anions"] > 0)].copy()
    if valid.empty:
        return go.Figure().update_layout(title="Insufficient data for Durov Diagram")
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"
    
    valid["Durov_X"] = (100.0 - valid["HCO3_CO3_pct"]).clip(0, 100)
    valid["Durov_Y"] = valid["Na_K_pct"].clip(0, 100)
    
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.65, 0.35],
        row_heights=[0.35, 0.65],
        specs=[[{"type": "scatter"}, None],
               [{"type": "scatter"}, {"type": "scatter"}]],
        horizontal_spacing=0.08,
        vertical_spacing=0.08
    )
    
    # 1. Main Facies Matrix (Row 2, Col 1)
    fig.add_trace(go.Scatter(
        x=valid["Durov_X"],
        y=valid["Durov_Y"],
        mode="markers",
        marker=dict(size=6, color="#3b82f6", opacity=0.8),
        text=valid["Location"],
        customdata=valid[["District", "Aquifer_System", "pH", "TDS (mg/L)"]].fillna("N/A").values,
        hovertemplate="<b>%{text}</b><br>Dist: %{customdata[0]}<br>Aquifer: %{customdata[1]}<br>pH: %{customdata[2]}<br>TDS: %{customdata[3]} mg/L<extra></extra>",
        name="Hydrochemical Facies"
    ), row=2, col=1)
    
    for x_line in [33.3, 66.6]:
        fig.add_shape(type="line", x0=x_line, y0=0, x1=x_line, y1=100, line=dict(color=grid_color, dash="dash"), row=2, col=1)
    for y_line in [33.3, 66.6]:
        fig.add_shape(type="line", x0=0, y0=y_line, x1=100, y1=y_line, line=dict(color=grid_color, dash="dash"), row=2, col=1)
        
    # 2. Top Subplot: pH (Row 1, Col 1)
    fig.add_trace(go.Scatter(
        x=valid["Durov_X"],
        y=valid["pH"],
        mode="markers",
        marker=dict(size=5, color="#10b981", opacity=0.7),
        name="pH Projection",
        hoverinfo="skip"
    ), row=1, col=1)
    
    # 3. Right Subplot: TDS (Row 2, Col 2)
    fig.add_trace(go.Scatter(
        x=valid["TDS (mg/L)"],
        y=valid["Durov_Y"],
        mode="markers",
        marker=dict(size=5, color="#f59e0b", opacity=0.7),
        name="TDS Projection",
        hoverinfo="skip"
    ), row=2, col=2)
    
    fig.update_xaxes(title_text="(Cl⁻ + SO₄²⁻) %", range=[0, 100], gridcolor=grid_color, row=2, col=1)
    fig.update_yaxes(title_text="(Na⁺ + K⁺) %", range=[0, 100], gridcolor=grid_color, row=2, col=1)
    
    fig.update_xaxes(showticklabels=False, range=[0, 100], gridcolor=grid_color, row=1, col=1)
    fig.update_yaxes(title_text="pH", range=[5, 9.5], gridcolor=grid_color, row=1, col=1)
    
    fig.update_xaxes(title_text="TDS (mg/L)", type="log", gridcolor=grid_color, row=2, col=2)
    fig.update_yaxes(showticklabels=False, range=[0, 100], gridcolor=grid_color, row=2, col=2)
    
    fig.update_layout(
        title="<b>📐 Extended Durov Diagram (Facies + pH + TDS Integration)</b>",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        height=580,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False
    )
    return fig
