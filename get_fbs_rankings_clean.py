import os
import json
import time
import requests
import pandas as pd

# === CONFIGURATION ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

headers = {"Authorization": f"Bearer {API_KEY}"}
fbs_file = "fbs_teams.csv"
rankings_file = "rankings_2025_FBS.csv"


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


def get_rankings_fbs(year):
    """Fetch and return only FBS rankings for a given year."""
    rankings_url = "https://api.collegefootballdata.com/rankings"
    rankings_df = cached_get(rankings_url, {"year": year})

    if rankings_df.empty or "polls" not in rankings_df.columns:
        print("⚠️ No rankings data available.")
        return pd.DataFrame()

    # Expand the rankings JSON structure
    expanded = []
    for _, row in rankings_df.iterrows():
        week = row.get("week")
        season = row.get("season")
        for poll_entry in row["polls"]:
            poll_name = poll_entry.get("poll", "Unknown Poll")
            for team_entry in poll_entry.get("ranks", []):
                expanded.append({
                    "season": season,
                    "week": week,
                    "poll": poll_name,
                    "rank": team_entry.get("rank"),
                    "school": team_entry.get("school"),
                    "conference": team_entry.get("conference"),
                    "points": team_entry.get("points", 0)
                })

    expanded_df = pd.DataFrame(expanded)
    if expanded_df.empty:
        print("⚠️ No expanded ranking data found.")
        return expanded_df

    # === Filter to FBS schools only ===
    if os.path.exists(fbs_file):
        fbs_teams = pd.read_csv(fbs_file)
        fbs_schools = set(fbs_teams["school"].unique())
        expanded_df = expanded_df[expanded_df["school"].isin(fbs_schools)]
    else:
        print("⚠️ No local FBS team file found — fetching it now.")
        teams_url = "https://api.collegefootballdata.com/teams/fbs"
        fbs_teams = cached_get(teams_url)
        fbs_teams.to_csv(fbs_file, index=False)
        fbs_schools = set(fbs_teams["school"].unique())
        expanded_df = expanded_df[expanded_df["school"].isin(fbs_schools)]

    return expanded_df


if __name__ == "__main__":
    print("📊 Fetching FBS rankings for 2025...")
    rankings_2025 = get_rankings_fbs(2025)

    if not rankings_2025.empty:
        rankings_2025.to_csv(rankings_file, index=False)
        print(f"✅ Saved {len(rankings_2025)} FBS rankings to {rankings_file}")
    else:
        print("⚠️ No FBS rankings were found for 2025.")
