import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.spatial import cKDTree

def calculate_idw_grid(df, param="Fe", grid_res=90, power=2.0):
    """
    Computes 2D Inverse Distance Weighting (IDW) surface for continuous plume mapping.
    """
    valid = df.dropna(subset=["Latitude", "Longitude", param]).copy()
    if len(valid) < 5:
        return None, None, None
        
    lats = valid["Latitude"].values
    lons = valid["Longitude"].values
    vals = pd.to_numeric(valid[param], errors="coerce").fillna(0).values
    
    # Odisha Geographic Bounding Box
    lon_min, lon_max = 81.35, 87.50
    lat_min, lat_max = 17.80, 22.60
    
    grid_lon = np.linspace(lon_min, lon_max, grid_res)
    grid_lat = np.linspace(lat_min, lat_max, grid_res)
    grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)
    
    # Nearest-neighbor IDW using cKDTree
    points = np.column_stack((lons, lats))
    tree = cKDTree(points)
    
    grid_points = np.column_stack((grid_x.ravel(), grid_y.ravel()))
    
    # Query 12 nearest stations
    k_neighbors = min(12, len(valid))
    distances, indices = tree.query(grid_points, k=k_neighbors)
    
    # Small epsilon to avoid division by zero
    distances = np.maximum(distances, 1e-5)
    weights = 1.0 / (distances ** power)
    weights /= weights.sum(axis=1, keepdims=True)
    
    interpolated_vals = np.sum(weights * vals[indices], axis=1)
    grid_z = interpolated_vals.reshape(grid_res, grid_res)
    
    return grid_lon, grid_lat, grid_z

def create_idw_plume_map(df, param="Fe", param_label="Iron (Fe mg/L)", map_style="open-street-map", is_dark=False):
    """
    Renders continuous spatial IDW contour overlay map with monitoring stations.
    """
    grid_lon, grid_lat, grid_z = calculate_idw_grid(df, param=param)
    
    if grid_z is None:
        fig = go.Figure()
        fig.update_layout(title="Insufficient spatial points for interpolation.")
        return fig
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    
    # Custom colorscale per parameter
    scale_name = "YlOrRd" if param in ["Fe", "NO3", "F", "WQI"] else "Viridis"
    
    fig = go.Figure()
    
    # IDW 2D Density / Contour surface
    fig.add_trace(go.Contour(
        x=grid_lon,
        y=grid_lat,
        z=grid_z,
        colorscale=scale_name,
        contours=dict(
            coloring="heatmap",
            showlabels=True,
            labelfont=dict(size=9, color="#ffffff")
        ),
        colorbar=dict(title=f"Predicted {param}", thickness=14, len=0.7),
        opacity=0.78,
        name="IDW Spatial Plume",
        hoverinfo="x+y+z"
    ))
    
    # Overlay actual station points
    valid_pts = df.dropna(subset=["Latitude", "Longitude", param]).copy()
    fig.add_trace(go.Scatter(
        x=valid_pts["Longitude"],
        y=valid_pts["Latitude"],
        mode="markers",
        marker=dict(
            size=6,
            color="#0f172a" if not is_dark else "#ffffff",
            line=dict(width=1, color="#ffffff" if not is_dark else "#000000")
        ),
        text=valid_pts["Location"] if "Location" in valid_pts.columns else valid_pts["Station_No"],
        customdata=valid_pts[["District", "Aquifer_System", "River_Basin", param]].fillna("N/A").values,
        hovertemplate="<b>%{text}</b><br>Dist: %{customdata[0]}<br>Aquifer: %{customdata[1]}<br>Basin: %{customdata[2]}<br>" + f"Observed {param}: " + "<b>%{customdata[3]}</b><extra></extra>",
        name="Monitoring Wells"
    ))
    
    fig.update_layout(
        title=f"<b>Continuous Spatial Plume Surface (IDW Interpolation): {param_label}</b>",
        paper_bgcolor=theme_bg,
        plot_bgcolor=theme_bg,
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        xaxis=dict(title="Longitude (°E)", range=[81.3, 87.6]),
        yaxis=dict(title="Latitude (°N)", range=[17.7, 22.7]),
        height=580,
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig


def create_3d_subsurface_profile(df, color_by="Status", max_depth=100, is_dark=False):
    """
    3D Subsurface Stratigraphy & Aquifer Depth Profiler (Longitude x Latitude x -Depth mbgl).
    """
    valid = df.dropna(subset=["Latitude", "Longitude", "Depth_mbgl"]).copy()
    valid["Depth_Num"] = pd.to_numeric(valid["Depth_mbgl"], errors="coerce")
    valid = valid[valid["Depth_Num"].notna() & (valid["Depth_Num"] <= max_depth) & (valid["Depth_Num"] >= 0)].copy()
    
    if valid.empty:
        fig = go.Figure()
        fig.update_layout(title="No depth records available for 3D subsurface profiling.")
        return fig
        
    theme_bg = "#18181b" if is_dark else "#ffffff"
    theme_text = "#fafafa" if is_dark else "#09090b"
    
    # Invert depth so subterranean depths go downward along Z-axis
    valid["Z_Subsurface"] = -valid["Depth_Num"]
    
    fig = go.Figure()
    
    if color_by == "Status":
        status_colors = {"Danger": "#ef4444", "Warning": "#f59e0b", "Safe": "#22c55e"}
        for st_name in ["Danger", "Warning", "Safe"]:
            grp = valid[valid["Status"] == st_name]
            if not grp.empty:
                fig.add_trace(go.Scatter3d(
                    x=grp["Longitude"],
                    y=grp["Latitude"],
                    z=grp["Z_Subsurface"],
                    mode="markers",
                    marker=dict(size=5, color=status_colors.get(st_name, "#3b82f6"), opacity=0.85),
                    name=f"Well: {st_name}",
                    text=grp["Location"] if "Location" in grp.columns else grp["Station_No"],
                    customdata=grp[["District", "Aquifer_System", "River_Basin", "Depth_Num", "Fe", "NO3", "F"]].fillna("N/A").values,
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "District: %{customdata[0]}<br>"
                        "Aquifer: %{customdata[1]}<br>"
                        "Basin: %{customdata[2]}<br>"
                        "Depth: <b>%{customdata[3]} mbgl</b><br>"
                        "Fe: %{customdata[4]} | NO3: %{customdata[5]} | F: %{customdata[6]}<extra></extra>"
                    )
                ))
    else: # Continuous parameter or WQI
        is_num = color_by in valid.columns and pd.api.types.is_numeric_dtype(valid[color_by])
        valid["Plot_Col"] = pd.to_numeric(valid[color_by], errors="coerce").fillna(0) if is_num else 0
        fig.add_trace(go.Scatter3d(
            x=valid["Longitude"],
            y=valid["Latitude"],
            z=valid["Z_Subsurface"],
            mode="markers",
            marker=dict(
                size=5,
                color=valid["Plot_Col"],
                colorscale="YlOrRd" if color_by in ["Fe", "NO3", "F", "WQI"] else "Viridis",
                colorbar=dict(title=color_by, thickness=12, len=0.6),
                opacity=0.88
            ),
            text=valid["Location"] if "Location" in valid.columns else valid["Station_No"],
            customdata=valid[["District", "Aquifer_System", "River_Basin", "Depth_Num", color_by]].fillna("N/A").values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "District: %{customdata[0]}<br>"
                "Aquifer: %{customdata[1]}<br>"
                "Basin: %{customdata[2]}<br>"
                "Depth: <b>%{customdata[3]} mbgl</b><br>"
                f"{color_by}: <b>%{{customdata[4]}}</b><extra></extra>"
            ),
            name="Subsurface Wells"
        ))
        
    fig.update_layout(
        title=f"<b>🧊 3D Subsurface Aquifer Stratigraphy & Depth Model (max {max_depth} mbgl)</b>",
        paper_bgcolor=theme_bg,
        scene=dict(
            xaxis=dict(title="Longitude (°E)", backgroundcolor=theme_bg, gridcolor="rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"),
            yaxis=dict(title="Latitude (°N)", backgroundcolor=theme_bg, gridcolor="rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"),
            zaxis=dict(title="Depth mbgl (-Z)", backgroundcolor=theme_bg, gridcolor="rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"),
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=0.8)
            )
        ),
        font=dict(family="DM Sans, sans-serif", color=theme_text),
        height=640,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig
