import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# נתיב לקובץ
GPKG = r"/mnt/new_home/idan7/data_mining/ais_tracks_export/AISVesselTracks2024/AISVesselTracks2024.gpkg"
TABLE       = "AISVesselTracks2024"
COL_MMSI    = "MMSI"
COL_GROUP   = "VesselGroup"
COL_TSTART  = "TrackStartTime"
COL_DURMIN  = "DurationMinutes"

# שליפה מה-SQLite
SQL = f"""
SELECT
  "{COL_GROUP}" AS vesselgroup,
  strftime('%Y-%m', replace(substr("{COL_TSTART}",1,19),'T',' ')) AS ym,
  COUNT(DISTINCT "{COL_MMSI}") AS unique_mmsi,
  COALESCE(SUM("{COL_DURMIN}"),0) AS total_minutes
FROM "{TABLE}"
GROUP BY vesselgroup, ym
ORDER BY ym, vesselgroup;
"""

with sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True) as conn:
    df = pd.read_sql_query(SQL, conn)

# סינון קטגוריות לא רלוונטיות
df = df[~df["vesselgroup"].isin(["Other", "Not Available", None])]

# חישוב משך ממוצע בדקות לכל ספינה
df["avg_hours_per_vessel"] = (df["total_minutes"] / df["unique_mmsi"]) / 60

# Pivot לחודשים × קבוצות
pivot = df.pivot_table(index="ym", columns="vesselgroup", values="avg_hours_per_vessel", aggfunc="mean").fillna(0)
pivot = pivot.sort_index()

# ציור
plt.figure(figsize=(11,5))
colors = plt.cm.tab20(np.linspace(0, 1, pivot.shape[1]))
for (col, c) in zip(pivot.columns, colors):
    plt.plot(pivot.index, pivot[col].values, label=str(col), linewidth=2, marker='o', markersize=4, color=c)

plt.xticks(rotation=45, ha="right")
plt.xlabel("Month (YYYY-MM)")
plt.ylabel("Average sailing hours per vessel")
plt.title("Monthly average sailing time per vessel by vessel group")
plt.grid(True, alpha=0.25)
plt.legend(title="Vessel group", ncol=2, fontsize=9)
plt.tight_layout()
plt.show()
