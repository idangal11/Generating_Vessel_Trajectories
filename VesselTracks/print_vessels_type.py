import pandas as pd
import os

# הגדרת הפרמטרים
input_folder = r"/mnt/new_home/idan7/data_mining/ais_tracks_export/chunks/"
output_file = "/mnt/new_home/idan7/data_mining/filtered_mmsi_357455000.csv"
target_mmsi = 357455000

# מציאת כל קובצי CSV בתיקייה
csv_files = [file for file in os.listdir(input_folder) if file.endswith(".csv")]
print(csv_files)
# רשימה לאגירת התוצאות
filtered_rows = []

# מעבר על כל הקבצים
for file in csv_files:
    file_path = os.path.join(input_folder, file)
    try:
        df = pd.read_csv(file_path)
        if "MMSI" in df.columns:
            filtered = df[df["MMSI"] == target_mmsi]
            if not filtered.empty:
                print()
                print(f'נמצאו רשומות בקובץ: {file}')
                filtered_rows.append(filtered)
    except Exception as e:
        print(f"שגיאה בקריאת {file}: {e}")

# איחוד ושמירה
if filtered_rows:
    result_df = pd.concat(filtered_rows)
    result_df.to_csv(output_file, index=False)
    print(f"נשמרו {len(result_df)} רשומות ל־{output_file}")
else:
    print("לא נמצאו רשומות מתאימות.")
