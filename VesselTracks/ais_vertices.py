import pandas as pd, geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, LineString, MultiLineString

CSV_PATH = "/mnt/new_home/idan7/data_mining/ais_tracks_export/AISVesselTracks2024/AISVesselTracks2024_head_0p5GB_Passenger.csv"
OUT_GPKG = "/mnt/new_home/idan7/data_mining/ais_tracks_export/QGIS/ais_vertices_passenger.gpkg"
OUT_LAYER = "ais_vertices"
KEEP_COLS = ["MMSI","VesselGroup","TrackStartTime"]

def explode_row(row):
    geom = wkt.loads(row["geometry_wkt"])
    attrs = {c: row.get(c) for c in KEEP_COLS if c in row}
    parts = [geom] if isinstance(geom, LineString) else list(geom.geoms) if isinstance(geom, MultiLineString) else []
    for p_i, line in enumerate(parts):
        for v_i, (x,y) in enumerate(line.coords):
            yield {**attrs, "part_index":p_i, "vertex_index":v_i, "lon":x, "lat":y}

first = True
for chunk in pd.read_csv(CSV_PATH, dtype={"MMSI":"string"}, chunksize=10_000):
    rows = [r for _, row in chunk.iterrows() for r in explode_row(row)]
    if not rows:
        continue
    tmp = pd.DataFrame(rows)
    gdf = gpd.GeoDataFrame(tmp, geometry=gpd.points_from_xy(tmp["lon"], tmp["lat"]), crs="EPSG:4326")
    gdf.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG", mode="w" if first else "a")
    first = False
print("done.")
