import geopandas as gpd
import shapely.wkt
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from geopy.distance import geodesic

# ==== שלב 1: טעינת הנתונים ====
GPKG = "/mnt/new_home/idan7/data_mining/ais_tracks_export/AISVesselTracks2024/AISVesselTracks2024.gpkg"
gdf = gpd.read_file(GPKG, layer="AISVesselTracks2024")
gdf["geometry_wkt"] = gdf.geometry.apply(lambda geom: geom.wkt)

# ==== שלב 2: חילוץ start / end לכל מקטע ====
routes = []
for _, row in gdf.iterrows():
    geom = shapely.wkt.loads(row["geometry_wkt"])
    if geom.geom_type == "MultiLineString":
        for line in geom.geoms:
            if len(line.coords) >= 2:
                start = line.coords[0]
                end = line.coords[-1]
                routes.append((start, end))
    elif geom.geom_type == "LineString":
        if len(geom.coords) >= 2:
            start = geom.coords[0]
            end = geom.coords[-1]
            routes.append((start, end))

routes_df = pd.DataFrame(routes, columns=["start", "end"])

# ==== שלב 3: פונקציית clustering לנקודות קרובות ====
def cluster_points(points, threshold_km=2):
    clusters = []
    labels = {}
    for p in points:
        found = False
        for i, center in enumerate(clusters):
            if geodesic((p[1], p[0]), (center[1], center[0])).km <= threshold_km:
                labels[p] = i
                found = True
                break
        if not found:
            clusters.append(p)
            labels[p] = len(clusters) - 1
    return labels, clusters

# כל הנקודות שיכולות להיות צמתים
all_points = set(routes_df["start"]) | set(routes_df["end"])
labels, cluster_centers = cluster_points(list(all_points), threshold_km=2)

# ==== שלב 4: מיפוי start/end ל-cluster ====
routes_df["start_cluster"] = routes_df["start"].apply(lambda p: labels[p])
routes_df["end_cluster"] = routes_df["end"].apply(lambda p: labels[p])

# ==== שלב 5: ספירת edges בין clusters ====
edges_df = routes_df.groupby(["start_cluster", "end_cluster"]).size().reset_index(name="count")

# ==== שלב 6: בניית הגרף ====
G = nx.DiGraph()
for _, row in edges_df.iterrows():
    start_center = cluster_centers[row["start_cluster"]]
    end_center = cluster_centers[row["end_cluster"]]
    G.add_node(row["start_cluster"], pos=start_center)
    G.add_node(row["end_cluster"], pos=end_center)
    G.add_edge(row["start_cluster"], row["end_cluster"], weight=row["count"])

# ==== שלב 7: ציור הגרף ====
pos = nx.get_node_attributes(G, "pos")
plt.figure(figsize=(12, 10))
nx.draw(
    G, pos,
    with_labels=False,
    node_size=50,
    node_color="red",
    edge_color="gray",
    width=[G[u][v]['weight'] / 10 for u, v in G.edges()]
)
plt.title("Vessel Route Network Graph (clustered by 2 km)")
plt.show()
