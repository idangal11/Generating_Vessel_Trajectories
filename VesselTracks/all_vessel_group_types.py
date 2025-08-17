import pandas as pd
import os

# נתיב התיקייה שמכילה את קובצי הצ'אנקים
input_folder = "/mnt/new_home/idan7/data_mining/ais_tracks_export/chunks/"  # שנה בהתאם

# רשימה לאגירת הערכים של VesselGroup
vessel_groups = set()

# מעבר על כל הקבצים
for file in os.listdir(input_folder):
    if file.endswith(".csv") and file.startswith("ais_chunk_"):
        full_path = os.path.join(input_folder, file)
        try:
            df = pd.read_csv(full_path, usecols=["VesselGroup"])  # טען רק את העמודה הרלוונטית
            unique_values = df["VesselGroup"].dropna().unique()
            vessel_groups.update(unique_values)
        except Exception as e:
            print(f"שגיאה בקובץ {file}: {e}")

# הדפסת כל סוגי VesselGroup שנמצאו
print("סוגי VesselGroup שנמצאו:")
for group in sorted(vessel_groups):
    print(group)
