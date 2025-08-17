import pandas as pd

# הטקסט שלך
text = "PUT: LAT:25.9448 LON:-82.7411 | OUTPUT: LAT:25.9447 LON:-82.7447 | OUTPUT: LAT:25.9448 LON:-82.7446 | OUTPUT: LAT:25.9452 LON:-82.7462 | OUTPUT: LAT:25.9452 LON:-82.7441 | OUTPUT: LAT:25.9448 LON:-82.7451"

# חילוץ כל נקודת LAT/LON
coords = []
for part in text.split("|"):
    part = part.strip()
    lat_str = part.split("LAT:")[1].split(" ")[0]
    lon_str = part.split("LON:")[1]
    lat = float(lat_str)
    lon = float(lon_str)
    coords.append(f"{lon} {lat}")  # MULTILINESTRING הוא בפורמט "lon lat"

# יצירת מחרוזת MULTILINESTRING
multilinestring_wkt = f"MULTILINESTRING(({', '.join(coords)}))"

# יצירת DataFrame עם עמודה geometry
df = pd.DataFrame({"geometry": [multilinestring_wkt]})

# שמירה לקובץ CSV
df.to_csv("/mnt/new_home/idan7/data_mining/ais_tracks_export/multilinestring.csv", index=False)

print(df)
