input_file = "/mnt/new_home/idan7/data_mining/ais_tracks_export/cleaned_data/vessel_tracks.txt"

valid_lines = 0
invalid_lines = 0
empty_lines = 0
routes = 0
preview_lines = 5  # how many valid lines to preview

print("[START] Checking file integrity...")

with open(input_file, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()

        if not line:
            empty_lines += 1
            continue

        if line == "<|endofroute|>":
            routes += 1
            continue

        if "INPUT:" in line and "OUTPUT:" in line:
            valid_lines += 1
            if preview_lines > 0:
                print(f"[VALID] Line {i}: {line}")
                preview_lines -= 1
        else:
            print(f"[WARNING] Suspicious line {i}: {line}")
            invalid_lines += 1

print("\n[SUMMARY]")
print(f"Valid lines: {valid_lines}")
print(f"Suspicious lines: {invalid_lines}")
print(f"Empty lines: {empty_lines}")
print(f"Routes found (endofroute): {routes}")
print("[DONE] File check completed.")
