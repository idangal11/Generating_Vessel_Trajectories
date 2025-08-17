import pandas as pd
import os

def compute_vesseltype_stats_from_folder(input_dir, output_txt):
    all_chunks = []

    # Collect all CSV files from directory
    for file in os.listdir(input_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(input_dir, file)
            try:
                df = pd.read_csv(file_path, usecols=['VesselType', 'Length', 'Width', 'Draft'])
                df = df.dropna()
                all_chunks.append(df)
                print(f"[INFO] Loaded: {file}")
            except Exception as e:
                print(f"[WARNING] Skipping file {file}: {e}")

    # Concatenate all loaded chunks
    full_df = pd.concat(all_chunks, ignore_index=True)
    print(f"[INFO] Total records: {len(full_df)}")

    # Group by VesselType and compute means
    grouped = full_df.groupby('VesselType').agg({
        'Length': 'mean',
        'Width': 'mean',
        'Draft': 'mean'
    }).round(3)

    # Convert to dictionary
    vessel_stats = grouped.to_dict(orient='index')

    # Write to .txt in Python dict format
    with open(output_txt, 'w') as f:
        for vessel_type, stats in vessel_stats.items():
            f.write(f"{int(vessel_type)}: {{'Length': {stats['Length']}, 'Width': {stats['Width']}, 'Draft': {stats['Draft']}}},\n")

    print(f"[INFO] Saved stats for {len(vessel_stats)} VesselTypes to: {output_txt}")

# Example usage:
input_folder = '/mnt/new_home/idan7/data_mining/ais_tracks_export/chunks/'
output_file = '/mnt/new_home/idan7/data_mining/vesseltype_stats.txt'
compute_vesseltype_stats_from_folder(input_folder, output_file)
