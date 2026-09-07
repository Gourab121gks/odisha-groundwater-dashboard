import json
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

AQUIFER_GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "aquifers_principal.geojson")
BASIN_GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "odisha_basins.geojson")
RIVER_GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "odisha_rivers.geojson")
DISTRICT_GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "odisha_districts.geojson")

AQUIFER_COLORS = {
    "Alluvium": "#fef08a",                 # Pale Yellow
    "Laterite": "#fb923c",                 # Rust Orange
    "Basement Gneissic Complex": "#c084fc",# Light Purple
    "Khondalites": "#b45309",              # Brown / Bronze
    "Charnockite": "#84cc16",              # Olive Green
    "Sandstone": "#f59e0b",                # Golden Amber
    "Granite": "#f87171",                  # Salmon Red
    "Schist": "#06b6d4",                   # Cyan / Teal
    "Quartzite": "#818cf8",                # Indigo / Slate Blue
    "Shale": "#64748b",                    # Muted Slate
    "Gneiss": "#e879f9",                   # Lilac
    "Intrusive": "#a855f7"                 # Dark Violet
}

BASIN_COLORS = {
    "Mahanadi": "#38bdf8",                  # Sky blue
    "Brahmani": "#34d399",                  # Emerald
    "Baitarani": "#a78bfa",                 # Purple
    "Rushikulya": "#fbbf24",                # Amber
    "Kolab": "#f472b6",                     # Pink
    "Indravati": "#f87171",                 # Light Red
    "Vansadhara": "#fb923c",                # Orange
    "Budhabalanga": "#4ade80",              # Light Green
    "Subarnarekha": "#2dd4bf",              # Teal
    "Nagavali": "#818cf8",                  # Indigo
    "Bahuda": "#c084fc",                    # Violet
    "Direct Draining to Sea": "#94a3b8",    # Slate
    "Chilika": "#06b6d4",                   # Cyan
    "Jambhira": "#e879f9"                   # Lilac
}

@st.cache_data
def load_aquifer_geojson():
    if os.path.exists(AQUIFER_GEOJSON_PATH):
        with open(AQUIFER_GEOJSON_PATH, "r") as f:
            return json.load(f)
    return None

@st.cache_data
def load_basin_geojson():
    if os.path.exists(BASIN_GEOJSON_PATH):
        with open(BASIN_GEOJSON_PATH, "r") as f:
            return json.load(f)
    return None

@st.cache_data
def load_river_geojson():
    if os.path.exists(RIVER_GEOJSON_PATH):
        with open(RIVER_GEOJSON_PATH, "r") as f:
            return json.load(f)
    return None

@st.cache_data
def load_district_geojson():
    if os.path.exists(DISTRICT_GEOJSON_PATH):
        with open(DISTRICT_GEOJSON_PATH, "r") as f:
            return json.load(f)
    return None

def build_advanced_gis_map(
    df_wells,
    overlay_layer="Principal Aquifers",
    show_overlay=True,
    show_rivers=False,
    overlay_opacity=0.35,
    chosen_col="Status",
    color_metric="Quality Status",
    map_style="open-street-map",
    is_dark=False
):
    """
    Renders multi-layer interactive map with:
    1. Principal Aquifer / River Basin Vector Polygon Overlays
    2. River Network Streamlines
    3. Monitoring Station Points (color-coded by Status, Aquifer, Basin, or Contaminant)
    """
    fig = go.Figure()
    
    # 1. Geological Aquifers Layer
    if show_overlay and overlay_layer == "Principal Aquifers":
        aq_geojson = load_aquifer_geojson()
        if aq_geojson:
            df_aq = pd.DataFrame([feat["properties"] for feat in aq_geojson["features"]])
            for aq_name, group in df_aq.groupby("AQUIFER"):
                aq_indices = group.index.tolist()
                sub_geojson = {
                    "type": "FeatureCollection",
                    "features": [aq_geojson["features"][i] for i in aq_indices]
                }
                for feat in sub_geojson["features"]:
                    feat["id"] = feat["properties"]["OBJECTID"]
                    
                fill_color = AQUIFER_COLORS.get(aq_name, "#94a3b8")
                
                fig.add_trace(go.Choroplethmap(
                    geojson=sub_geojson,
                    locations=[feat["properties"]["OBJECTID"] for feat in sub_geojson["features"]],
                    z=[1] * len(sub_geojson["features"]),
                    colorscale=[[0, fill_color], [1, fill_color]],
                    showscale=False,
                    marker_opacity=overlay_opacity,
                    marker_line_width=1.2,
                    marker_line_color="#334155" if not is_dark else "#94a3b8",
                    hovertemplate=(
                        f"<b>Aquifer Formation:</b> {aq_name}<br>"
                        f"<b>Total Outcrop Area:</b> %{{customdata[0]:,.0f}} km²<br>"
                        f"<b>Specific Yield:</b> %{{customdata[1]}}%<extra></extra>"
                    ),
                    customdata=group[["Area", "Sp_Yield"]].values,
                    name=f"Aquifer: {aq_name}",
                    legendgroup="Aquifers"
                ))

    # 2. River Basins Layer
    elif show_overlay and overlay_layer == "River Basins (11 Catchments)":
        basin_geojson = load_basin_geojson()
        if basin_geojson:
            df_basins = pd.DataFrame([feat["properties"] for feat in basin_geojson["features"]])
            for b_name, grp in df_basins.groupby("BASIN_NAME"):
                b_indices = grp.index.tolist()
                sub_geojson = {
                    "type": "FeatureCollection",
                    "features": [basin_geojson["features"][i] for i in b_indices]
                }
                for feat in sub_geojson["features"]:
                    feat["id"] = feat["properties"]["OBJECTID"]
                    
                b_color = BASIN_COLORS.get(b_name, "#94a3b8")
                fig.add_trace(go.Choroplethmap(
                    geojson=sub_geojson,
                    locations=[feat["properties"]["OBJECTID"] for feat in sub_geojson["features"]],
                    z=[1] * len(sub_geojson["features"]),
                    colorscale=[[0, b_color], [1, b_color]],
                    showscale=False,
                    marker_opacity=overlay_opacity,
                    marker_line_width=1.5,
                    marker_line_color="#0f172a" if not is_dark else "#e2e8f0",
                    hovertemplate=f"<b>River Basin:</b> {b_name}<br><b>Catchment Area:</b> %{{customdata[0]:,.0f}} km²<extra></extra>",
                    customdata=grp[["AREA"]].values,
                    name=f"Basin: {b_name}",
                    legendgroup="Basins"
                ))

    # 3. River Streamlines Network (Optional)
    if show_rivers:
        river_geojson = load_river_geojson()
        if river_geojson:
            # Extract line coordinates to plot as continuous line trace
            lats, lons = [], []
            for feat in river_geojson["features"]:
                geom = feat.get("geometry", {})
                gtype = geom.get("type", "")
                coords = geom.get("coordinates", [])
                
                if gtype == "LineString":
                    for pt in coords:
                        lons.append(pt[0])
                        lats.append(pt[1])
                    lons.append(None)
                    lats.append(None)
                elif gtype == "MultiLineString":
                    for line in coords:
                        for pt in line:
                            lons.append(pt[0])
                            lats.append(pt[1])
                        lons.append(None)
                        lats.append(None)
                        
            fig.add_trace(go.Scattermap(
                lat=lats,
                lon=lons,
                mode="lines",
                line=dict(width=1.6, color="#0284c7" if not is_dark else "#38bdf8"),
                name="River Network",
                hoverinfo="skip",
                legendgroup="Rivers"
            ))

    # 4. Monitoring Well Points
    valid_wells = df_wells.dropna(subset=["Latitude", "Longitude"]).copy()
    
    if not valid_wells.empty:
        is_continuous = (chosen_col not in ["Status", "Aquifer_System", "River_Basin"] and chosen_col in valid_wells.columns and pd.api.types.is_numeric_dtype(valid_wells[chosen_col]))
        
        if is_continuous:
            valid_wells["Clean_Val"] = pd.to_numeric(valid_wells[chosen_col], errors="coerce").fillna(0)
            fig.add_trace(go.Scattermap(
                lat=valid_wells["Latitude"],
                lon=valid_wells["Longitude"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=valid_wells["Clean_Val"],
                    colorscale="Reds" if chosen_col in ["Fe", "NO3", "F", "Mn", "U"] else "Viridis",
                    colorbar=dict(title=color_metric, thickness=12, len=0.6, y=0.5),
                    opacity=0.92
                ),
                hovertemplate=(
                    "<b>Station: %{customdata[0]}</b><br>"
                    "Location: %{customdata[1]}, %{customdata[2]}<br>"
                    "Basin: <b>%{customdata[3]}</b><br>"
                    "Aquifer: <b>%{customdata[4]}</b><br>"
                    "Status: %{customdata[5]}<br>"
                    f"{chosen_col}: <b>%{{customdata[6]}}</b><extra></extra>"
                ),
                customdata=valid_wells[["Station_No", "Block", "District", "River_Basin", "Aquifer_System", "Status", chosen_col]].fillna("N/A").values,
                name="Monitoring Wells",
                legendgroup="Wells"
            ))
        elif chosen_col == "Aquifer_System":
            for aq_type, grp in valid_wells.groupby("Aquifer_System"):
                pt_color = AQUIFER_COLORS.get(aq_type, "#3b82f6")
                fig.add_trace(go.Scattermap(
                    lat=grp["Latitude"],
                    lon=grp["Longitude"],
                    mode="markers",
                    marker=dict(size=8, color=pt_color, opacity=0.9),
                    name=f"Well: {aq_type}",
                    legendgroup="Wells",
                    hovertemplate=(
                        "<b>Station: %{customdata[0]}</b><br>"
                        "Location: %{customdata[1]}, %{customdata[2]}<br>"
                        "Basin: <b>%{customdata[3]}</b><br>"
                        "Aquifer: <b>%{customdata[4]}</b><br>"
                        "Status: %{customdata[5]}<br>"
                        "Fe: %{customdata[6]} mg/L | NO3: %{customdata[7]} mg/L | F: %{customdata[8]} mg/L<extra></extra>"
                    ),
                    customdata=grp[["Station_No", "Block", "District", "River_Basin", "Aquifer_System", "Status", "Fe", "NO3", "F"]].fillna("N/A").values
                ))
        elif chosen_col == "River_Basin":
            for b_name, grp in valid_wells.groupby("River_Basin"):
                pt_color = BASIN_COLORS.get(b_name, "#3b82f6")
                fig.add_trace(go.Scattermap(
                    lat=grp["Latitude"],
                    lon=grp["Longitude"],
                    mode="markers",
                    marker=dict(size=8, color=pt_color, opacity=0.9),
                    name=f"Well: {b_name}",
                    legendgroup="Wells",
                    hovertemplate=(
                        "<b>Station: %{customdata[0]}</b><br>"
                        "Location: %{customdata[1]}, %{customdata[2]}<br>"
                        "Basin: <b>%{customdata[3]}</b><br>"
                        "Aquifer: <b>%{customdata[4]}</b><br>"
                        "Status: %{customdata[5]}<br>"
                        "Fe: %{customdata[6]} mg/L | NO3: %{customdata[7]} mg/L | F: %{customdata[8]} mg/L<extra></extra>"
                    ),
                    customdata=grp[["Station_No", "Block", "District", "River_Basin", "Aquifer_System", "Status", "Fe", "NO3", "F"]].fillna("N/A").values
                ))
        else: # By Status (Danger / Warning / Safe)
            status_colors = {"Danger": "#ef4444", "Warning": "#f59e0b", "Safe": "#22c55e"}
            for status in ["Danger", "Warning", "Safe"]:
                grp = valid_wells[valid_wells["Status"] == status]
                if not grp.empty:
                    fig.add_trace(go.Scattermap(
                        lat=grp["Latitude"],
                        lon=grp["Longitude"],
                        mode="markers",
                        marker=dict(size=8, color=status_colors.get(status, "#3b82f6"), opacity=0.9),
                        name=f"Well: {status}",
                        legendgroup="Wells",
                        hovertemplate=(
                            "<b>Station: %{customdata[0]}</b><br>"
                            "Location: %{customdata[1]}, %{customdata[2]}<br>"
                            "Basin: <b>%{customdata[3]}</b><br>"
                            "Aquifer: <b>%{customdata[4]}</b><br>"
                            "Status: %{customdata[5]}<br>"
                            "Fe: %{customdata[6]} mg/L | NO3: %{customdata[7]} mg/L | F: %{customdata[8]} mg/L<extra></extra>"
                        ),
                        customdata=grp[["Station_No", "Block", "District", "River_Basin", "Aquifer_System", "Status", "Fe", "NO3", "F"]].fillna("N/A").values
                    ))
                    
    # Map Layout Settings
    fig.update_layout(
        map=dict(
            style=map_style,
            center=dict(lat=20.45, lon=84.5),
            zoom=6.3
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=580,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            font=dict(size=10)
        )
    )
    return fig
