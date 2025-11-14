import requests
import pandas as pd
import json
import re
from tqdm import tqdm
import time

# === USER SETTINGS ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"   # <-- Replace this
YEAR = 2025
WEEKS = range(1, 16)              # Adjust if season has more or fewer weeks
RAW_OUTPUT = f"penalties_{YEAR}_allweeks_raw.csv"
SUMMARY_OUTPUT = f"penalties_{YEAR}_allweeks_summary.csv"

# === SETUP ===
headers = {"Authorization": f"Bearer {API_KEY}"}

def extract_play_text(play):
    """Get play description text from possible keys."""
    if not isinstance(play, dict):
        return ""
    for k in ["playText", "play_text", "description", "playDescription", "desc", "summary", "play"]:
        if k in play and isinstance(play[k], str) and play[k].strip():
            return play[k].strip()
    for v in play.values():
        if isinstance(v, str) and len(v) > 15:
            return v.strip()
    return ""

def extract_team(play, key_list, fallback="Unknown"):
    if not isinstance(play, dict):
        return fallback
    for k in key_list:
        if k in play:
            val = play[k]
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, dict):
                for sub in ["name", "displayName", "teamName", "abbreviation"]:
                    if sub in val and isinstance(val[sub], str) and val[sub].strip():
                        return val[sub].strip()
    return fallback

def extract_penalty_yards(play):
    text = extract_play_text(play)
    if not text:
        return None

    patterns = [
        r"\((\d{1,2})\s*yards?\)",
        r"(\d{1,2})\s*yards?\b",
        r"(\d{1,2})-yard",
        r"penalt(?:y|ies)[^\d]{0,10}(\d{1,2})",
    ]

    for pat in patterns:
        m = re.search(pat, text.lower())
        if m:
            try:
                val = int(m.group(1))
                if 0 < val < 100:
                    return val
            except Exception:
                continue
    return None

def has_penalty(text):
    if not isinstance(text, str):
        return False
    t = text.lower()
    keywords = [
        "penalty", "holding", "false start", "offside", "pass interference",
        "targeting", "personal foul", "unsportsmanlike", "delay of game",
        "illegal formation", "illegal motion", "face mask", "roughing", "clipping"
    ]
    return any(k in t for k in keywords)

def classify_penalty(text):
    if not isinstance(text, str):
        return "Other / Unclassified"
    t = text.lower()
    if "holding" in t:
        return "Holding"
    if "false start" in t:
        return "False Start"
    if "pass interference" in t:
        return "Pass Interference"
    if "offside" in t or "offsides" in t:
        return "Offside"
    if "targeting" in t:
        return "Targeting"
    if "personal foul" in t:
        return "Personal Foul"
    if "unsportsmanlike" in t:
        return "Unsportsmanlike Conduct"
    if "delay of game" in t:
        return "Delay of Game"
    if "illegal formation" in t:
        return "Illegal Formation"
    if "illegal motion" in t:
        return "Illegal Motion"
    if "face mask" in t or "facemask" in t:
        return "Face Mask"
    if "roughing the passer" in t:
        return "Roughing the Passer"
    if "roughing the kicker" in t:
        return "Roughing the Kicker"
    if "roughing" in t:
        return "Roughing"
    if "clipping" in t:
        return "Clipping"
    return "Other / Unclassified"

# === MAIN LOOP ===
all_records = []

for week in WEEKS:
    url = f"https://api.collegefootballdata.com/plays?year={YEAR}&week={week}"
    print(f"\n📅 Fetching Week {week}...")
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"⚠️  Skipping Week {week} (API Error {r.status_code})")
        continue

    plays = r.json()
    if not plays:
        print(f"⚠️  No data for Week {week}")
        continue

    print(f"✅ Retrieved {len(plays)} plays for Week {week}")

    week_records = []
    for play in tqdm(plays, desc=f"Processing Week {week}", leave=False):
        text = extract_play_text(play)
        if not has_penalty(text):
            continue

        offense = extract_team(play, ["offense", "offenseTeam", "possessionTeam", "posteam"], "Unknown")
        defense = extract_team(play, ["defense", "defenseTeam", "defTeam", "defense_name"], "Unknown")
        yards = extract_penalty_yards(play)

        week_records.append({
            "year": YEAR,
            "week": week,
            "offense": offense,
            "defense": defense,
            "penalty_type": classify_penalty(text),
            "penalty_yards": yards,
            "play_text": text,
        })

    if week_records:
        all_records.extend(week_records)
        print(f"✅ Found {len(week_records)} penalty plays in Week {week}")
    else:
        print(f"ℹ️  No penalties found in Week {week}")

    time.sleep(1.2)  # Be polite to API

if not all_records:
    raise SystemExit("❌ No penalty plays found across all weeks.")

pen_df = pd.DataFrame(all_records)
pen_df.to_csv(RAW_OUTPUT, index=False)
print(f"\n💾 Saved all raw penalty plays to {RAW_OUTPUT}")

# === SUMMARY ===
summary = (
    pen_df.groupby(["offense", "defense", "penalty_type"])
    .agg(
        total_penalties=("penalty_type", "count"),
        total_yards=("penalty_yards", "sum")
    )
    .reset_index()
)
summary["average_yards_per_penalty"] = (
    summary["total_yards"] / summary["total_penalties"]
).round(2)
summary = summary.sort_values(["offense", "total_penalties"], ascending=[True, False])
summary.to_csv(SUMMARY_OUTPUT, index=False)

print(f"✅ Saved season summary to {SUMMARY_OUTPUT}")
print("Sample of summary:")
print(summary.head(15))
