import os
import time
import json
import requests
import pandas as pd
from tqdm import tqdm

# === CONFIGURATION ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"
CACHE_DIR = "cache"
OUTPUT_FILE = "cfb_penalty_data_2025.csv"
os.makedirs(CACHE_DIR, exist_ok=True)

headers = {"Authorization": f"Bearer {API_KEY}"}

# === SAFE GET FUNCTION ===
def cached_get(url, params=None):
    """Cache GET requests locally and safely handle empty or invalid responses."""
    key = url.replace("/", "_") + "_" + (str(params) if params else "")
    cache_path = os.path.join(CACHE_DIR, f"{hash(key)}.json")

    # Try cache first
    if os.path.exists(cache_path):
        try:
            return pd.read_json(cache_path)
        except Exception:
            pass  # Ignore bad cache, re-fetch

    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)

        if r.status_code != 200:
            print(f"⚠️  Skipping {url} (HTTP {r.status_code})")
            return pd.DataFrame()

        text = (r.text or "").strip()
        if not text:
            print(f"⚠️  Skipping {url} — empty response body")
            return pd.DataFrame()
        if not (text.startswith("[") or text.startswith("{")):
            print(f"⚠️  Skipping {url} — non-JSON response: {text[:30]!r}")
            return pd.DataFrame()

        try:
            data = json.loads(text)
        except Exception as e:
            print(f"⚠️  JSON decode failed for {url}: {e}")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df.to_json(cache_path, orient="records")
        time.sleep(0.5)
        return df

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Network error fetching {url}: {e}")
        return pd.DataFrame()


# === STEP 1: FBS TEAM LIST ===
print("Fetching FBS teams...")
teams_url = "https://api.collegefootballdata.com/teams/fbs"
teams_df = cached_get(teams_url)
if teams_df.empty:
    raise SystemExit("❌ Could not fetch FBS teams.")

print(f"✅ Found {len(teams_df)} FBS teams.\n")

team_list = teams_df["school"].tolist()


# === STEP 2: RANKINGS ===
print("Fetching rankings...")
rankings_url = "https://api.collegefootballdata.com/rankings"
rankings_df = cached_get(rankings_url, {"year": 2025})
rankings_df.to_csv("rankings_raw.csv", index=False)
print(f"✅ Retrieved {len(rankings_df)} ranking records.\n")


# === STEP 3: TEAM STATS ===
print("Fetching team stats...")
team_stats_all = []
team_stats_url = "https://api.collegefootballdata.com/team/stats"

for team in tqdm(team_list, desc="Team Stats"):
    params = {"year": 2025, "team": team}
    df = cached_get(team_stats_url, params)
    if df.empty:
        continue
    df["team"] = team
    team_stats_all.append(df)

if team_stats_all:
    team_stats_df = pd.concat(team_stats_all, ignore_index=True)
    print(f"✅ Retrieved stats for {len(team_stats_df['team'].unique())} teams.\n")
else:
    team_stats_df = pd.DataFrame()
    print("⚠️ No team stats returned.\n")


# === STEP 4: EXTRACT PENALTY STATS ===
print("Extracting penalty data...")
def extract_penalty_stats(df):
    """Extract total penalties and penalty yards per team."""
    if df.empty or "statName" not in df.columns:
        return pd.DataFrame()
    penalty_df = df[df["statName"].isin(["penalties", "penaltyYards"])].copy()
    if penalty_df.empty:
        return pd.DataFrame()
    penalty_pivot = penalty_df.pivot_table(
        index=["team"], columns="statName", values="statValue", aggfunc="first"
    ).reset_index()
    penalty_pivot["penaltyYardsPerPenalty"] = (
        penalty_pivot["penaltyYards"] / penalty_pivot["penalties"]
    ).round(2)
    return penalty_pivot

penalty_stats_df = extract_penalty_stats(team_stats_df)
print(f"✅ Extracted penalty data for {len(penalty_stats_df)} teams.\n")


# === STEP 5: FLATTEN RANKINGS ===
print("Processing rankings...")
if not rankings_df.empty and "rankings" in rankings_df.columns:
    expanded_rankings = []
    for _, row in rankings_df.iterrows():
        for item in row["rankings"]:
            expanded_rankings.append({
                "season": row.get("season"),
                "week": row.get("week"),
                "poll": row.get("poll"),
                "school": item.get("school"),
                "rank": item.get("rank"),
                "points": item.get("points"),
                "firstPlaceVotes": item.get("firstPlaceVotes")
            })
    rankings_df = pd.DataFrame(expanded_rankings)
else:
    rankings_df = pd.DataFrame()

print(f"✅ Rankings flattened with {len(rankings_df)} entries.\n")


# === STEP 6: MERGE EVERYTHING ===
print("Merging datasets...")
merged = teams_df[["school", "conference"]].copy()

if not penalty_stats_df.empty:
    merged = merged.merge(penalty_stats_df, how="left", left_on="school", right_on="team")

if not rankings_df.empty:
    merged = merged.merge(rankings_df, how="left", on="school")

merged.drop_duplicates(subset=["school"], inplace=True)
merged.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Saved merged dataset to {OUTPUT_FILE}\n")
print("🎉 Done! Your 2025 FBS penalty data with rankings is ready.")
