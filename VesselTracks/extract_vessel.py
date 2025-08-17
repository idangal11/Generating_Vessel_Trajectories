import pandas as pd
from pathlib import Path

# --- config ---
CHUNKS_DIR = Path("/mnt/new_home/idan7/data_mining/ais_tracks_export/chunks")
TARGET_MMSI = "367635620"  # keep as string
OUT_CSV = Path("/mnt/new_home/idan7/data_mining/ais_tracks_export/mmsi_367635620_tracks_sorted.csv")

# --- collect rows from all CSVs ---
frames = []
for csv_path in sorted(CHUNKS_DIR.glob("*.csv")):
    df = pd.read_csv(csv_path, dtype={"MMSI": str}, low_memory=False)
    sub = df[df["MMSI"] == TARGET_MMSI].copy()
    if not sub.empty:
        sub["source_file"] = csv_path.name
        frames.append(sub)

if not frames:
    raise SystemExit(f"No rows found for MMSI {TARGET_MMSI} in {CHUNKS_DIR}")

df = pd.concat(frames, ignore_index=True)

# --- parse time + sort by time ---
df["TrackStartTime"] = pd.to_datetime(df["TrackStartTime"], errors="coerce", utc=True)
df["TrackEndTime"]   = pd.to_datetime(df["TrackEndTime"], errors="coerce", utc=True)
df = df.dropna(subset=["TrackStartTime"]).sort_values(["TrackStartTime", "TrackEndTime"]).reset_index(drop=True)

# --- exact column order (only those that exist) ---
cols = [
    "MMSI", "TrackStartTime", "TrackEndTime",
    "VesselType", "Length", "Width", "Draft",
    "DurationMinutes", "VesselGroup", "geometry", "source_file"
]
df = df[[c for c in cols if c in df.columns]]

# --- save ---
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_CSV, index=False)

print(f"Rows: {len(df)}")
print(f"Saved to: {OUT_CSV}")
print(df.head(10))
