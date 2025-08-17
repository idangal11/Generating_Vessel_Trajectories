import pandas as pd
import numpy as np
from shapely import wkt
from geopy.distance import geodesic
import os
import math
import time
from concurrent.futures import ProcessPoolExecutor

# Vessel stats dictionary (not included here for brevity)
# You can inject VESSEL_STATS_BY_TYPE externally if needed

def calculate_bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (
        math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    )

    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def process_single_file(file_tuple):
    input_csv_path, output_csv_path, vessel_stats = file_tuple

    if os.path.exists(output_csv_path):
        return f"[SKIP] {os.path.basename(output_csv_path)} already exists."

    try:
        df = pd.read_csv(input_csv_path)
        df = df.sort_values(by=['MMSI', 'TrackStartTime']).reset_index(drop=True)
        vector_data = []

        for idx, row in df.iterrows():
            try:
                vt = int(row['VesselType'])
                if vt not in vessel_stats:
                    continue

                multiline = wkt.loads(row['geometry'])
                all_points = [pt for line in multiline.geoms for pt in line.coords]
                if len(all_points) < 2:
                    continue

                total_duration_min = row['DurationMinutes']
                if total_duration_min == 0:
                    continue

                duration_per_segment_min = total_duration_min / (len(all_points) - 1)
                time_diff_sec = duration_per_segment_min * 60.0
                stats = vessel_stats[vt]

                for i in range(1, len(all_points)):
                    lon1, lat1 = all_points[i - 1]
                    lon2, lat2 = all_points[i]

                    distance = geodesic((lat1, lon1), (lat2, lon2)).meters
                    angle = calculate_bearing(lat1, lon1, lat2, lon2)
                    speed_knots = (distance * 1.94384) / time_diff_sec

                    segment_start = pd.to_datetime(row['TrackStartTime']) + pd.to_timedelta((i - 1) * duration_per_segment_min, unit='m')
                    segment_end = pd.to_datetime(row['TrackStartTime']) + pd.to_timedelta(i * duration_per_segment_min, unit='m')

                    vector_data.append({
                        'MMSI': row['MMSI'],
                        'TrackStartTime': row['TrackStartTime'],
                        'TrackEndTime': row['TrackEndTime'],
                        'Segment_StartTime': segment_start,
                        'Segment_EndTime': segment_end,
                        'VesselType': vt,
                        'Global_Length': stats['Length'],
                        'Global_Width': stats['Width'],
                        'Global_Draft': stats['Draft'],
                        'Distance_Meters': distance,
                        'Speed_Knots': speed_knots,
                        'Bearing_Degrees': angle,
                        'Start_Lat': lat1,
                        'Start_Lon': lon1,
                        'End_Lat': lat2,
                        'End_Lon': lon2
                    })

            except Exception:
                continue

        if vector_data:
            output_df = pd.DataFrame(vector_data)
            output_df.to_csv(output_csv_path, index=False)
            return f"[INFO] Processed and saved {len(vector_data)} vectors to: {os.path.basename(output_csv_path)}"
        else:
            return f"[WARNING] No valid vectors in file: {os.path.basename(input_csv_path)}"
    except Exception as e:
        return f"[ERROR] Failed to process {os.path.basename(input_csv_path)}: {e}"

def process_all_batches_parallel(input_dir, output_dir, vessel_stats, max_workers=4):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_tasks = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f'vectors_{filename}')
            file_tasks.append((input_path, output_path, vessel_stats))

    start_time = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(process_single_file, file_tasks)
        for result in results:
            print(result)

    elapsed = time.time() - start_time
    print(f"[DONE] Processed {len(file_tasks)} files in {elapsed:.2f} seconds.")

# This function can now be used by providing vessel stats and the appropriate folder paths.
