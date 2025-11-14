import requests
import pandas as pd
import json
import re
from tqdm import tqdm

# === USER SETTINGS ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"  # <-- replace with your real API key
YEAR = 2025
WEEK = 1
RAW_JSON_FILE = f"pbp_raw_{YEAR}_week{WEEK}.json"
RAW_OUTPUT = f"penalties_{YEAR}_week{WEEK}_raw.csv"
SUMMARY_OUTPUT = f"penalties_{YEAR}_week{WEEK}_summary.csv"

# === SETUP ===
headers = {"Authorization": f"Bearer {API_KEY}"}
url = f"https://api.collegefootballdata.com/plays?year={YEAR}&week={WEEK}"

print(f"Fetching {YEAR} Week {WEEK} play-by-play data from CollegeFootballData...")
r = requests.get(url, headers=headers)

if r.status_code != 200:
    raise SystemExit(f"❌ API error {r.status_code}: {r.text}")

plays = r.json()
print(f"✅ Retrieved {len(plays)} total plays")

# Save raw JSON for inspection
with open(RAW_JSON_FILE, "w", encoding="utf-8") as fh:
    json.dump(plays, fh, ensure_ascii=False, indent=2)
print(f"Saved raw JSON to {RAW_JSON_FILE}")

# === HELPERS ===
def extract_play_text(play):
    """Get the play description text from possible keys."""
    if not isinstance(play, dict):
        return ""
    for k in ["playText", "play_text", "description", "playDescription", "desc", "summary", "play"]:
        if k in play and isinstance(play[k], str) and play[k].strip():
            return play[k].strip()
    # Fallback: look for any long string value
    for v in play.values():
        if isinstance(v, str) and len(v) > 15:
            return v.strip()
    return ""

def extract_team(play, key_list, fallback="Unknown"):
    """Try multiple key names for a team."""
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
    """Extract penalty yards directly from playText (handles variations)."""
    text = extract_play_text(play)
    if not text:
        return None

    patterns = [
        r"\((\d{1,2})\s*yards?\)",          # e.g. (5 yards)
        r"(\d{1,2})\s*yards?\b",            # e.g. penalty for 10 yards
        r"(\d{1,2})-yard",                  # e.g. 15-yard penalty
        r"penalt(?:y|ies)[^\d]{0,10}(\d{1,2})",  # e.g. penalty 10
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
    """Detect if play text indicates a penalty."""
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
    """Categorize penalty type from text."""
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

# === PARSE PLAYS ===
records = []
for play in tqdm(plays, desc="Parsing plays"):
    text = extract_play_text(play)
    offense = extract_team(play, ["offense", "offenseTeam", "possessionTeam", "posteam"], "Unknown")
    defense = extract_team(play, ["defense", "defenseTeam", "defTeam", "defense_name"], "Unknown")
    yards = extract_penalty_yards(play)
    detected = has_penalty(text)

    if detected:
        records.append({
            "offense": offense,
            "defense": defense,
            "play_text": text,
            "penalty_type": classify_penalty(text),
            "penalty_yards": yards
        })

if not records:
    raise SystemExit("No penalty plays detected. Check raw JSON structure.")

pen_df = pd.DataFrame(records)
pen_df.to_csv(RAW_OUTPUT, index=False)
print(f"✅ Saved {len(pen_df)} penalty plays to {RAW_OUTPUT}")

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

print(f"✅ Saved summary with yards and averages to {SUMMARY_OUTPUT}")
print("Sample of summary:")
print(summary.head(15))
