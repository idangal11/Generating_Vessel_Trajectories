# -*- coding: utf-8 -*-
"""
Count unique MMSI per vessel group from a large .gpkg and plot a histogram.

- Works directly via sqlite3 on the GeoPackage (no heavy GeoPandas load).
- Auto-detects the layer (table) and the MMSI / vessel group column names (case-insensitive).
- Saves a CSV with counts and shows a bar chart.
"""

import os, sqlite3, sys
import pandas as pd
import matplotlib.pyplot as plt

GPKG_PATH = r"/mnt/new_home/idan7/data_mining/ais_tracks_export/AISVesselTracks2024/AISVesselTracks2024.gpkg"   # ← עדכן נתיב
CSV_OUT   = "/mnt/new_home/idan7/data_mining/ais_tracks_export/QGIS/unique_mmsi_per_vesselgroup.csv"

# ---- helpers ----
def list_feature_tables(conn):
    # GeoPackage lists feature tables in gpkg_contents
    q = "SELECT table_name FROM gpkg_contents WHERE data_type='features';"
    return [r[0] for r in conn.execute(q).fetchall()]

def columns_of(conn, table):
    q = f'PRAGMA table_info("{table}");'
    return {row[1]: row for row in conn.execute(q).fetchall()}  # name -> pragma row

def pick_column(cols, candidates):
    # return first existing column name that matches candidates case-insensitively
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def ensure_index(conn, table, col):
    # create an index if not exists (speeds up COUNT DISTINCT on big files)
    idx = f'idx_{table}_{col}'
    conn.execute(f'CREATE INDEX IF NOT EXISTS "{idx}" ON "{table}"("{col}");')

# ---- main ----
if not os.path.isfile(GPKG_PATH):
    sys.exit(f"File not found: {GPKG_PATH}")

with sqlite3.connect(f"file:{GPKG_PATH}?mode=ro", uri=True) as conn:
    tables = list_feature_tables(conn)
    if not tables:
        sys.exit("No feature tables found in gpkg_contents.")

    chosen = None
    mmsi_col = None
    group_col = None

    # Try to auto-detect the right table & column names
    MMSI_CANDS   = ["MMSI", "mmsi"]
    GROUP_CANDS  = ["vesselgroup", "VesselGroup", "vessel_group", "VESSELGROUP", "ship_group", "VesselType", "vesseltype"]

    for t in tables:
        cols = columns_of(conn, t)
        mc = pick_column(cols, MMSI_CANDS)
        gc = pick_column(cols, GROUP_CANDS)
        if mc and gc:
            chosen = t
            mmsi_col = mc
            group_col = gc
            break

    if not chosen:
        # If nothing matched, print columns to help debug
        dbg = {t: list(columns_of(conn, t).keys()) for t in tables}
        sys.exit(f"Could not auto-detect MMSI / vessel group columns.\nTables & columns:\n{dbg}")

    print(f"[info] Using table: {chosen} | MMSI: {mmsi_col} | group: {group_col}")

    # Optional: build indexes to speed up big aggregations (comment out if file is read-only on FS)
    try:
        conn2 = sqlite3.connect(GPKG_PATH)  # open writeable (if allowed) just to create indexes
        ensure_index(conn2, chosen, mmsi_col)
        ensure_index(conn2, chosen, group_col)
        conn2.commit()
        conn2.close()
    except Exception as e:
        print(f"[warn] Could not create indexes (continuing without): {e}")

    # Run aggregation (read-only connection again)
    sql = f'''
        SELECT "{group_col}" AS vesselgroup,
               COUNT(DISTINCT "{mmsi_col}") AS unique_mmsi
        FROM "{chosen}"
        GROUP BY "{group_col}"
        ORDER BY unique_mmsi DESC;
    '''
    df = pd.read_sql_query(sql, conn)

# Save results
df.to_csv(CSV_OUT, index=False, encoding="utf-8")
print(f"[done] Saved counts → {CSV_OUT}")
print(df)

# ---- plot histogram (bar chart) ----
plt.figure(figsize=(10, 5))
plt.bar(df["vesselgroup"].astype(str), df["unique_mmsi"].astype(int))
plt.xticks(rotation=45, ha="right")
plt.xlabel("Vessel group")
plt.ylabel("Unique MMSI (number of vessels)")
plt.title("Unique vessels per vessel group")
plt.tight_layout()
plt.show()
