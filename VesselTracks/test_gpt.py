import re
import pandas as pd
from transformers import pipeline, AutoTokenizer

# === טען את המודל והטוקנייזר ===
model_path = "/mnt/new_home/idan7/data_mining/ais_tracks_export/"
tokenizer = AutoTokenizer.from_pretrained(model_path)
generator = pipeline("text-generation", model=model_path, tokenizer=tokenizer)

# === טען קובץ טקסט ===
txt_path = "/mnt/new_home/idan7/data_mining/ais_tracks_export/text_for_GPT_extended/vessel_gpt_1.txt"
with open(txt_path, 'r') as f:
    lines = f.readlines()

# === פרס שורה בודדת למידע ===
def parse_line(line):
    match = re.search(
        r"MMSI:(\d+)\s+\|\s+INPUT:\s+LAT:([-\d.]+)\s+LON:([-\d.]+)\s+SPD:([-\d.]+)\s+BRG:([-\d.]+)\s+ΔT:(\d+)\s+\|\s+OUTPUT:\s+LAT:([-\d.]+)\s+LON:([-\d.]+)",
        line)
    if match:
        return {
            "MMSI": int(match.group(1)),
            "LAT": float(match.group(2)),
            "LON": float(match.group(3)),
            "SPD": float(match.group(4)),
            "BRG": float(match.group(5)),
            "DeltaT": int(match.group(6)),
            "OUT_LAT": float(match.group(7)),
            "OUT_LON": float(match.group(8)),
        }
    return None

# === עיבוד הנתונים ===
parsed = [parse_line(line) for line in lines if parse_line(line) is not None]
df = pd.DataFrame(parsed)

# === סינון לפי MMSI ===
ship_id = 367635620
ship_df = df[df["MMSI"] == ship_id].reset_index(drop=True)

last_line = ""
drop = 0  # how many seed lines to drop from the prompt

for i in range(0, 10):
    # === build seed lines (last 20 rows) ===
    def row_to_prompt(row):
        return f"INPUT: LAT:{row['LAT']:.4f} LON:{row['LON']:.4f} SPD:{row['SPD']:.4f} BRG:{row['BRG']:.4f} ΔT:{row['DeltaT']} |"

    input_lines = [row_to_prompt(row) for _, row in ship_df.iloc[-40:-20].iterrows()]

    # cut ONLY the prompt seed (every 5 iters drop 5 first lines)
    seed_for_prompt = input_lines[drop:] if drop < len(input_lines) else []

    print("==prompt text==")
    prompt_text  = "\n".join(seed_for_prompt)
    prompt_text += f"{last_line}"
    prompt_text += "\n→ Predict next input in the same format:\n"
    print(prompt_text)

    output = generator(prompt_text, max_new_tokens=17, do_sample=True, temperature=0.7, top_k=50)

    # === parse model output ===
    print("\n=== Model Output ===")
    full_text = output[0]["generated_text"]
    lines = [l.strip() for l in full_text.strip().split("\n") if l.strip()]

    if lines:
        # normalize one clean INPUT line
        new_line = lines[-1].replace("PUT:", "INPUT:")
        new_line = new_line.split("|")[0].strip() + " |"
        last_line += new_line + "\n"
        print(last_line, "\n")

    # after every 5 iterations → drop 5 more seed lines from the NEXT prompt
    if (i + 1) % 5 == 0:
        drop = min(drop + 5, len(input_lines))  # cap at 20 (so it won't error)



import re
import pandas as pd
from pathlib import Path

# 1) Regex: תופס גם INPUT וגם PUT, ומחלץ LAT ו-LON כ-float
LINE_RE = re.compile(
    r"(?:INPUT|PUT):\s*LAT:([-]?\d+(?:\.\d+)?)\s*LON:([-]?\d+(?:\.\d+)?)",
    re.IGNORECASE
)

# 2) חלץ את כל הזוגות מהטקסט המצטבר
text = last_line.strip()
matches = list(LINE_RE.finditer(text))

coords = []
for m in matches:
    lat = float(m.group(1))
    lon = float(m.group(2))
    coords.append((lon, lat))  # סדר WKT הוא (lon lat)

if len(coords) < 2:
    raise ValueError("Not enough coordinates to build a MULTILINESTRING (need at least 2).")

# 3) בנה MULTILINESTRING WKT
multilinestring_wkt = "MULTILINESTRING((" + ", ".join(f"{lon} {lat}" for lon, lat in coords) + "))"

# 4) כתיבה ל-CSV לעמודת geometry (לטעינה ב-QGIS כ-WKT)
out_line_csv = "/mnt/new_home/idan7/data_mining/ais_tracks_export/predicted_path_multilinestring.csv"
pd.DataFrame({"geometry": [multilinestring_wkt]}).to_csv(out_line_csv, index=False)

# (אופציונלי) גם קובץ נקודות לכל תחזית
out_points_csv = "/mnt/new_home/idan7/data_mining/ais_tracks_export/predicted_points.csv"
points_wkt = [f"POINT({lon} {lat})" for lon, lat in coords]
pd.DataFrame({"LAT": [lat for _, lat in coords],
              "LON": [lon for lon, _ in coords],
              "geometry": points_wkt}).to_csv(out_points_csv, index=False)

print(f"Saved line WKT to: {Path(out_line_csv).resolve()}")
print(f"Saved points to:   {Path(out_points_csv).resolve()}")
print("Load in QGIS via: Layer → Add Layer → Add Delimited Text Layer (WKT, EPSG:4326).")
