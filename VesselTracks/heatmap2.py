#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIS Heatmap (fixed orientation) → density.tif + rgba.tif
- Reads points from GPKG (EPSG:4326 or known CRS)
- Reprojects to EPSG:3857
- Bins points to raster grid, applies Gaussian-like blur (NumPy only)
- Correctly orients raster: rows from north to south (np.flipud(H.T))
- Writes:
    1) float32 density GeoTIFF (for analysis / QGIS styling)
    2) RGBA overlay with alpha+mask (ready to place above OSM)
"""

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS

# ====== PATHS (עדכן אם צריך) ======
IN_GPKG = "/mnt/new_home/idan7/data_mining/ais_tracks_export/QGIS/ais_vertices_passenger.gpkg"
IN_LAYER = "ais_vertices"
OUT_DENS = "/mnt/new_home/idan7/data_mining/ais_tracks_export/QGIS/ais_heatmap_density_pass_1.tif"
OUT_RGBA = "/mnt/new_home/idan7/data_mining/ais_tracks_export/QGIS/ais_heatmap_rgba_pass_1.tif"

# ====== PARAMS ======
PIXEL_SIZE_M   = 500      # גודל פיקסל במטרים (קטן=חד יותר)
BANDWIDTH_M    = 4000     # החלקה (בקירוב σ) במטרים (גדול=חלק יותר)
PADDING_FACTOR = 1.0      # ריפוד גבולות ביחס ל-BANDWIDTH
CLIP_LOW_PCT   = 2.0      # חיתוך נמוכים (כמו cumulative count cut)
CLIP_HIGH_PCT  = 98.0     # חיתוך גבוהים
ALPHA_CUTOFF   = 0.10     # מתחת ל-10% → שקוף
ALPHA_GAMMA    = 0.8      # עקומה רכה לאלפא
ALPHA_MAX      = 230      # 0..255
MAX_PIXELS     = 25_000_000

# ====== HELPERS ======
def gaussian_blur_numpy(img: np.ndarray, sigma_px: float) -> np.ndarray:
    """Separable 1D Gaussian blur (NumPy only)."""
    if sigma_px <= 0:
        return img.astype("float32")
    r = int(max(1, round(3 * sigma_px)))
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-0.5 * (x / sigma_px) ** 2).astype(np.float32)
    k /= k.sum()
    # rows
    a = np.pad(img.astype("float32"), ((0, 0), (r, r)), mode="reflect")
    rows = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 1, a)
    # cols
    b = np.pad(rows, ((r, r), (0, 0)), mode="reflect")
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 0, b)
    return out.astype("float32")

def get_colormap():
    """Return f(t∈[0,1]) -> uint8 RGB(…,3). Prefer matplotlib 'inferno' if available."""
    try:
        from matplotlib import cm
        cmap = cm.get_cmap("inferno")
        def f(t):
            t = np.clip(t, 0, 1)
            return (cmap(t)[..., :3] * 255.0).astype(np.uint8)
        return f
    except Exception:
        # fallback ramp: black→red→yellow→white
        def f(t):
            t = np.clip(t, 0, 1).astype(np.float32)
            r = np.clip(4*t,     0, 1)
            g = np.clip(4*t-1.5, 0, 1)
            b = np.clip(4*t-3.0, 0, 1)
            return (np.stack([r, g, b], -1) * 255.0).astype(np.uint8)
        return f

# ====== MAIN ======
def main():
    # 1) read points, project to EPSG:3857
    gdf = gpd.read_file(IN_GPKG, layer=IN_LAYER)
    if gdf.empty:
        raise RuntimeError("Input layer is empty.")
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)  # נקודות נוצרו קודם ב-WGS84
    gdf = gdf.to_crs(3857)
    gdf = gdf.loc[gdf.geometry.notna() & ~gdf.geometry.is_empty, ["geometry"]]

    x = gdf.geometry.x.to_numpy(np.float64)
    y = gdf.geometry.y.to_numpy(np.float64)

    # 2) bounds + padding
    x_min, y_min, x_max, y_max = gdf.total_bounds
    pad = PADDING_FACTOR * BANDWIDTH_M
    x_min -= pad; x_max += pad
    y_min -= pad; y_max += pad

    # 3) grid size (cap total pixels)
    width  = int(np.ceil((x_max - x_min) / PIXEL_SIZE_M))
    height = int(np.ceil((y_max - y_min) / PIXEL_SIZE_M))
    pixel_size = float(PIXEL_SIZE_M)
    if width * height > MAX_PIXELS:
        scale = np.sqrt((width * height) / MAX_PIXELS)
        pixel_size *= scale
        width  = int(np.ceil((x_max - x_min) / pixel_size))
        height = int(np.ceil((y_max - y_min) / pixel_size))
        print(f"[warn] raster too big; increased pixel size to ~{int(pixel_size)} m")

    # 4) histogram with correct orientation for rasters
    #    H shape: (width, height) in x→y; then transpose and flipud
    H, x_edges, y_edges = np.histogram2d(
        x, y,
        bins=[width, height],
        range=[[x_min, x_max], [y_min, y_max]]
    )
    counts = np.flipud(H.T).astype("float32")  # rows = north→south

    # 5) smoothing
    sigma_px = BANDWIDTH_M / pixel_size
    heat = gaussian_blur_numpy(counts, sigma_px)

    # 6) normalize + clip
    low  = float(np.percentile(heat, CLIP_LOW_PCT))
    high = float(np.percentile(heat, CLIP_HIGH_PCT))
    if high <= low:
        low, high = float(heat.min()), float(max(heat.max(), 1.0))
    t = np.clip((heat - low) / (high - low), 0, 1)

    # 7) write density (float32, EPSG:3857)
    transform = from_origin(x_min, y_max, pixel_size, pixel_size)
    with rasterio.open(
        OUT_DENS, "w", driver="GTiff",
        height=heat.shape[0], width=heat.shape[1], count=1, dtype="float32",
        crs=CRS.from_epsg(3857), transform=transform,
        compress="LZW", BIGTIFF="IF_SAFER", tiled=True
    ) as dst:
        dst.write(heat, 1)
    print(f"[done] density → {OUT_DENS}")

    # 8) build RGBA overlay (color + alpha + mask)
    cmap = get_colormap()
    rgb = cmap(t)  # (H,W,3) uint8
    a_norm = np.clip((t - ALPHA_CUTOFF) / max(1e-6, 1 - ALPHA_CUTOFF), 0, 1)
    a_norm = np.power(a_norm, ALPHA_GAMMA)
    alpha = (a_norm * ALPHA_MAX).astype(np.uint8)
    rgba = np.dstack([rgb, alpha])
    mask = (alpha > 0).astype(np.uint8) * 255

    with rasterio.open(
        OUT_RGBA, "w", driver="GTiff",
        height=rgba.shape[0], width=rgba.shape[1], count=4, dtype="uint8",
        crs=CRS.from_epsg(3857), transform=transform,
        photometric="RGB", compress="DEFLATE", BIGTIFF="IF_SAFER", tiled=True
    ) as dst:
        for b in range(4):
            dst.write(rgba[..., b], b + 1)
        dst.write_mask(mask)
    print(f"[done] rgba   → {OUT_RGBA}")
    print(f"      size: {rgba.shape[1]}×{rgba.shape[0]} px | pixel≈{int(pixel_size)} m | σ(px)={sigma_px:.2f}")

if __name__ == "__main__":
    main()
