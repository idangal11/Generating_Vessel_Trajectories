import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

CSV = '/mnt/new_home/idan7/data_mining/ais_tracks_export/QGIS/unique_mmsi_per_vesselgroup.csv'

# קריאת הנתונים
df = pd.read_csv(CSV, encoding="utf-8")

# איתור ומחיקת שורות עם vesselgroup לא רצוי
idx_to_drop = df[df['vesselgroup'].isin(['Other', 'Not Available'])].index
df.drop(index=idx_to_drop, inplace=True)

# מיון מהגדול לקטן
df.sort_values(by="unique_mmsi", ascending=False, inplace=True)

# יצירת צבעים ייחודיים לכל קטגוריה
colors = plt.cm.tab20(np.linspace(0, 1, len(df)))

# ציור ההיסטוגרמה
plt.figure(figsize=(10, 5))
bars = plt.bar(df["vesselgroup"].astype(str), df["unique_mmsi"].astype(int), color=colors)

# הוספת ערכי מספר מעל כל עמודה
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 1, str(height),
             ha='center', va='bottom', fontsize=9)

plt.xticks(rotation=45, ha="right")
plt.xlabel("Vessel group")
plt.ylabel("Unique MMSI (number of vessels)")
plt.title("Unique vessels per vessel group")
plt.tight_layout()
plt.show()

