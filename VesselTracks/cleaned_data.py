import os
from collections import defaultdict

input_dir = "/mnt/new_home/idan7/data_mining/ais_tracks_export/text_for_GPT_extended/"
output_file = "/mnt/new_home/idan7/data_mining/ais_tracks_export/cleaned_data/vessel_tracks.txt"

# אוגר את כל השורות לפי MMSI
mmsi_to_lines = defaultdict(list)

for fname in sorted(os.listdir(input_dir)):
    if fname.endswith(".txt"):
        file_path = os.path.join(input_dir, fname)
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    mmsi, content = line.split("|", 1)
                    mmsi = mmsi.strip()
                    mmsi_to_lines[mmsi].append(content.strip())
                except ValueError:
                    continue  # מדלג על שורות לא תקינות

# כותב את כל הנתונים המאורגנים לקובץ אחד
with open(output_file, "w", encoding="utf-8") as fout:
    for mmsi, lines in mmsi_to_lines.items():
        for line in lines:
            fout.write(line + "\n")
        fout.write("<|endofroute|>\n")  # מפריד בין מסלולים

print(f"[INFO] קובץ מאוחד נוצר בהצלחה: {output_file}")
