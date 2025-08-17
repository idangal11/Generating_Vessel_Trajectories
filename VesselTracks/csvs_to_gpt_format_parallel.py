import os
import pandas as pd
from glob import glob
from datetime import datetime

INPUT_FOLDER = "/mnt/new_home/idan7/data_mining/ais_tracks_export/vectors_for_GPT_updated/"
OUTPUT_FOLDER = "/mnt/new_home/idan7/data_mining/ais_tracks_export/text_for_GPT_extended/"
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_ROWS_PER_VESSEL = 100  # אפשר לבטל אם לא רלוונטי

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def vessel_df_to_gpt_format_pandas(df: pd.DataFrame) -> str:
    formatted_segments = []
    prev_time = None

    for _, row in df.iterrows():
        try:
            time = row['Segment_StartTime']
            if pd.isnull(time):
                print('Exception1:', e)
                continue
            if not isinstance(time, (pd.Timestamp, datetime)):
                try:
                    time = pd.to_datetime(time)
                except Exception:
                    print('Exception2:', e)
                    continue

            delta_t = int((time - prev_time).total_seconds()) if prev_time else 0
            prev_time = time

            line = (
                f"MMSI:{int(row['MMSI'])} | "
                f"INPUT: LAT:{row['Start_Lat']:.4f} LON:{row['Start_Lon']:.4f} "
                f"SPD:{row['Speed_Knots']:.4f} BRG:{row['Bearing_Degrees']:.4f} ΔT:{delta_t} | "
                f"OUTPUT: LAT:{row['End_Lat']:.4f} LON:{row['End_Lon']:.4f} |"
            )

            formatted_segments.append(line)
        except Exception as e:
            print('Exception3:', e)
            continue

    return "\n".join(formatted_segments)




def convert_all_csvs_to_gpt_format_pandas(input_folder, output_folder):
    all_files = sorted(glob(os.path.join(input_folder, "*.csv")))

    current_file_index = 0
    current_lines = []
    current_size_bytes = 0

    for file in all_files:
        print(f"[INFO] Processing {file}")
        try:
            df = pd.read_csv(file)
            # df["Segment_StartTime"] = pd.to_datetime(df["Segment_StartTime"], errors="coerce")

            dropped = df[df["Segment_StartTime"].isna() | df["MMSI"].isna()]
            print("[INFO] Dropping rows:\n", dropped.head())

            df = df.dropna(subset=["Segment_StartTime", "MMSI"])  # מסננים שורות בעייתיות

            df["MMSI"] = df["MMSI"].astype(int)
            df = df.sort_values(by=["MMSI", "Segment_StartTime"])

            for mmsi, vessel_df in df.groupby("MMSI"):
                vessel_df = vessel_df.dropna()
                # vessel_df = vessel_df.head(MAX_ROWS_PER_VESSEL)  # בטל אם לא רלוונטי

                gpt_text = vessel_df_to_gpt_format_pandas(vessel_df)
                vessel_bytes = len(gpt_text.encode("utf-8")) + 1

                if current_size_bytes + vessel_bytes > MAX_FILE_SIZE_BYTES:
                    output_path = os.path.join(output_folder, f"vessel_gpt_{current_file_index}.txt")
                    with open(output_path, "w") as f:
                        f.write("\n".join(current_lines))
                    print(f"[SAVED] {output_path} with {len(current_lines)} vessels")
                    current_file_index += 1
                    current_lines = []
                    current_size_bytes = 0

                if vessel_bytes <= MAX_FILE_SIZE_BYTES:
                    current_lines.append(gpt_text)
                    current_size_bytes += vessel_bytes
                else:
                    print(f"[SKIPPED] Vessel {mmsi} too large ({vessel_bytes / 1e6:.2f} MB)")

        except Exception as e:
            print(f"[ERROR] Failed to process {file}: {e}")

    if current_lines:
        output_path = os.path.join(output_folder, f"vessel_gpt_{current_file_index}.txt")
        with open(output_path, "w") as f:
            f.write("\n".join(current_lines))
        print(f"[FINAL SAVE] {output_path} with {len(current_lines)} vessels")


if __name__ == "__main__":
    print("[START] GPT format conversion using pandas only")
    convert_all_csvs_to_gpt_format_pandas(INPUT_FOLDER, OUTPUT_FOLDER)
    print("[DONE]")
