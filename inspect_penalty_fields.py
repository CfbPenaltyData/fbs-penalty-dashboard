import json

RAW_JSON_FILE = "pbp_raw_2025_week1.json"

with open(RAW_JSON_FILE, "r", encoding="utf-8") as fh:
    plays = json.load(fh)

sample_penalties = []

for play in plays:
    # Only look at plays that mention penalties
    text = str(play).lower()
    if "penalt" in text:
        sample_penalties.append(play)
        if len(sample_penalties) >= 5:
            break

print(f"Found {len(sample_penalties)} plays that appear to involve penalties.\n")

for i, p in enumerate(sample_penalties, 1):
    print(f"--- Play {i} ---")
    print(json.dumps(p, indent=2))
    print("\n")
