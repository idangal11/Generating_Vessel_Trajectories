import os
import pandas as pd
from glob import glob

def vessel_df_to_gpt_format(vessel_df):
    """
    Converts vessel trajectory into GPT-style training format:
    Each line is: INPUT: LAT:... LON:... SPD:... BRG:... ΔT:... | OUTPUT: LAT:... LON:... |
    """
    formatted_segments = []
    prev_time = None

    for _, row in vessel_df.iterrows():
        try:
            # נקודת התחלה
            start_lat = f"{row['Start_Lat']:.4f}"
            start_lon = f"{row['Start_Lon']:.4f}"
            spd = f"{row['Speed_Knots']:.4f}"
            brg = f"{row['Bearing_Degrees']:.4f}"
            time = row['Segment_StartTime']

            # הפרש זמן
            if prev_time is not None:
                delta_t = int((time - prev_time).total_seconds())
            else:
                delta_t = 0
            prev_time = time

            # נקודת סיום
            end_lat = f"{row['End_Lat']:.4f}"
            end_lon = f"{row['End_Lon']:.4f}"

            line = f"INPUT: LAT:{start_lat} LON:{start_lon} SPD:{spd} BRG:{brg} ΔT:{delta_t} | OUTPUT: LAT:{end_lat} LON:{end_lon} |"
            formatted_segments.append(line)
        except Exception as e:
            continue  # skip bad rows

    return "\n".join(formatted_segments)


def convert_and_save_gpt_text(input_folder, output_folder, max_file_size_mb=100):
    all_files = sorted(glob(os.path.join(input_folder, "*.csv")))
    mmsi_groups = {}

    # Load and group by MMSI
    for file in all_files:
        try:
            df = pd.read_csv(file)
            # df['Segment_StartTime'] = pd.to_datetime(df['Segment_StartTime'])
            df['Segment_StartTime'] = pd.to_datetime(df['Segment_StartTime'], utc=True, errors='coerce')

            for mmsi, group in df.groupby('MMSI'):
                if mmsi not in mmsi_groups:
                    mmsi_groups[mmsi] = []
                mmsi_groups[mmsi].append(group)

        except Exception as e:
            print(f"[WARNING] Failed to read {file}: {e}")

    # Save grouped text
    os.makedirs(output_folder, exist_ok=True)
    current_file_index = 0
    current_lines = []
    current_size_bytes = 0
    max_size_bytes = max_file_size_mb * 1024 * 1024

    for mmsi, dfs in sorted(mmsi_groups.items()):
        vessel_df = pd.concat(dfs, ignore_index=True).sort_values(by='Segment_StartTime')
        vessel_text = vessel_df_to_gpt_format(vessel_df)
        vessel_bytes = len(vessel_text.encode("utf-8")) + 1  # +1 for newline

        if current_size_bytes + vessel_bytes > max_size_bytes:
            # Save current batch
            output_path = os.path.join(output_folder, f"vessel_gpt_{current_file_index}.txt")
            with open(output_path, "w") as f:
                f.write("\n".join(current_lines))
            print(f"[INFO] Saved {output_path} with {len(current_lines)} vessels.")
            current_file_index += 1
            current_lines = []
            current_size_bytes = 0

        if vessel_bytes <= max_size_bytes:
            current_lines.append(vessel_text)
            current_size_bytes += vessel_bytes
        else:
            print(f"[SKIP] Vessel {mmsi} too large for single file ({vessel_bytes / 1e6:.2f} MB). Skipped.")

    # Save remaining vessels
    if current_lines:
        output_path = os.path.join(output_folder, f"vessel_gpt_{current_file_index}.txt")
        with open(output_path, "w") as f:
            f.write("\n".join(current_lines))
        print(f"[INFO] Saved {output_path} with {len(current_lines)} vessels.")

# Example call
convert_and_save_gpt_text(
    input_folder="/mnt/new_home/idan7/data_mining/ais_tracks_export/vectors_for_GPT_updated/",
    output_folder="/mnt/new_home/idan7/data_mining/ais_tracks_export/text_for_GPT/",
    max_file_size_mb=200
)

