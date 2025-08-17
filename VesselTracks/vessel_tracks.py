# import geopandas as gpd
#
# # קריאה מהשרת המרוחק - 10 שורות בלבד
# gdf = gpd.read_file(
#     "/mnt/new_home/idan7/data_mining/ais_tracks_export/AISVesselTracks2024/AISVesselTracks2024.gpkg",
#     engine="pyogrio",
#     skip_features=0,
#     max_features=10
# )
#
# print(gdf.head())


import geopandas as gpd

# מסלול לקובץ
file_path = "/mnt/new_home/idan7/data_mining/ais_tracks_export/AISVesselTracks2024/AISVesselTracks2024.gpkg"

# קביעת גודל צ’אנק
chunk_size = 10000  # שורות לכל קובץ
offset = 0
chunk_id = 1

while True:
    print(f"Reading chunk {chunk_id}...")
    gdf = gpd.read_file(
        file_path,
        engine="pyogrio",
        skip_features=offset,
        max_features=chunk_size
    )
    if gdf.empty:
        break

    output_path = f"/mnt/new_home/idan7/data_mining/ais_tracks_export/chunks/ais_chunk_{chunk_id}.csv"
    gdf.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

    offset += chunk_size
    chunk_id += 1

print("All chunks exported successfully.")
