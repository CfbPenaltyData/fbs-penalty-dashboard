# update_penalties_full.py
import os
import json
import time
import requests
import pandas as pd
import re
from datetime import datetime, timedelta, timezone

# --------------------------
# CONFIG
# --------------------------
API_KEY = os.environ.get("CFBD_API_KEY") or "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"
YEAR = 2025
WEEKS = range(1, 16)                 # adjust as needed
CACHE_DIR = "cache"
FBS_TEAMS_FILE = "fbs_teams.csv"     # expected file in repo
OUTPUT_PREFIX = f"penalties_{YEAR}_FBS"
RANKINGS_CSV = f"rankings_{YEAR}_fbs_latest_week_pivot.csv"

os.makedirs(CACHE_DIR, exist_ok=True)
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
BASE = "https://api.collegefootballdata.com"

# Cutoff for weekly inclusion: exclude plays after Sunday 06:00 AM ET for the week.
# We will implement the cutoff check as: if play_game_datetime > cutoff_dt => exclude.
# The script will attempt to parse a game start datetime; if missing, include the play (safer).
WEEKLY_CUTOFF_WEEKDAY = 6   # Sunday (Monday=0 ... Sunday=6) - used for calculation below
CUTOFF_HOUR_ET = 6          # 06:00 ET

# --------------------------
# UTILITIES
# --------------------------
def safe_get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return None

def cache_get(url, params=None):
    """GET with a tiny cache (avoid repeated API calls during development)."""
    key = url.replace("/", "_") + "_" + (str(params) if params else "")
    cache_path = os.path.join(CACHE_DIR, f"{abs(hash(key))}.json")
    if os.path.exists(cache_path):
        try:
            return json.load(open(cache_path, "r", encoding="utf-8"))
        except Exception:
            pass
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code != 200:
            print(f"⚠️  API returned {r.status_code} for {url} params={params}")
            return None
        data = r.json()
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        time.sleep(0.35)
        return data
    except requests.RequestException as e:
        print("Network error:", e)
        return None
    except ValueError:
        print("Non-JSON response for", url)
        return None

# Normalize names mapping (you can expand)
NAME_MAP = {
    "San José State": "San Jose St",
    "San Jose State": "San Jose St",
    # add your preferred replacements if needed; the script will also use fbs_teams.csv as authority
}

def normalize_name(s):
    return s.strip() if isinstance(s, str) else s

# --------------------------
# Penalty text helpers
# --------------------------
PENALTY_KEYWORDS = [
    "penalty","holding","false start","offside","pass interference","targeting",
    "personal foul","unsportsmanlike","delay of game","illegal formation","illegal motion",
    "face mask","facemask","roughing","clipping"
]

def extract_play_text(play):
    if not isinstance(play, dict):
        return ""
    for k in ("playText","play_text","description","playDescription","desc","summary","play"):
        if k in play and isinstance(play[k], str) and play[k].strip():
            return play[k].strip()
    # fallback: find any string-ish large field
    for v in play.values():
        if isinstance(v, str) and len(v) > 15:
            return v.strip()
    return ""

def extract_team_name(play, keys, fallback="Unknown"):
    val = safe_get(play, *keys) if isinstance(play, dict) else None
    if isinstance(val, str) and val.strip():
        return val.strip()
    if isinstance(val, dict):
        for sub in ("name","displayName","teamName","abbreviation"):
            if sub in val and isinstance(val[sub], str) and val[sub].strip():
                return val[sub].strip()
    return fallback

def extract_game_datetime(play):
    # Try multiple known keys (based on CFBD responses)
    # Return a timezone-aware UTC datetime if possible, otherwise None
    cand = None
    for key in ("start","gameDate","startTime","game_time"):
        cand = safe_get(play, key)
        if cand:
            break
    if not cand:
        # sometimes the play includes a nested "game" dict
        if isinstance(play, dict) and "game" in play and isinstance(play["game"], dict):
            for key in ("start","gameDate","startTime"):
                cand = safe_get(play["game"], key)
                if cand:
                    break
    if not cand:
        return None
    # parse many possible ISO-like formats; fall back to naive parse
    try:
        # handle typical ISO: "2025-09-06T20:00:00.000Z"
        dt = datetime.fromisoformat(cand.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc)
    except Exception:
        # try common format detection
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ","%Y-%m-%d %H:%M:%S","%Y-%m-%d"):
            try:
                dt = datetime.strptime(cand, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None

def looks_like_penalty(text):
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k in t for k in PENALTY_KEYWORDS)

def extract_penalty_yards(text):
    if not isinstance(text, str):
        return None
    text_low = text.lower()
    patterns = [r"\((\d{1,2})\s*yards?\)", r"(\d{1,2})\s*yards?\b", r"(\d{1,2})-yard"]
    for p in patterns:
        m = re.search(p, text_low)
        if m:
            try:
                v = int(m.group(1))
                if 0 <= v < 200:
                    return v
            except:
                pass
    return None

# classify to a normalized penalty type (coarse) and category
def classify_penalty_type(text):
    t = str(text).lower()
    if "holding" in t: return "Holding"
    if "false start" in t: return "False Start"
    if "pass interference" in t: return "Pass Interference"
    if "offside" in t or "offsides" in t: return "Offside"
    if "targeting" in t: return "Targeting"
    if "personal foul" in t: return "Personal Foul"
    if "unsportsmanlike" in t: return "Unsportsmanlike Conduct"
    if "delay of game" in t: return "Delay of Game"
    if "illegal formation" in t: return "Illegal Formation"
    if "illegal motion" in t: return "Illegal Motion"
    if "face mask" in t or "facemask" in t: return "Face Mask"
    if "roughing the passer" in t: return "Roughing the Passer"
    if "roughing the kicker" in t: return "Roughing the Kicker"
    if "roughing" in t: return "Roughing"
    if "clipping" in t: return "Clipping"
    if "delay" in t: return "Delay of Game"
    return "Other / Unclassified"

def classify_penalty_category(text):
    t = str(text).lower()
    if any(x in t for x in ["false start", "delay of game", "offside", "encroachment", "illegal formation", "illegal shift"]):
        return "Procedural"
    if any(x in t for x in ["holding", "block", "hands to the face", "clipping", "chop block"]):
        return "Blocking / Holding"
    if any(x in t for x in ["pass interference", "roughing", "unsportsmanlike", "personal foul", "targeting"]):
        return "Personal / Contact"
    if any(x in t for x in ["substitution", "ineligible", "sideline interference", "illegal touching"]):
        return "Administrative"
    if any(x in t for x in ["facemask", "horse collar"]):
        return "Safety / Tackling"
    return "Other"

# heuristics to determine who committed penalty
def determine_committer(text, offense_team, defense_team):
    """
    Returns (committer_team_name_or_None, committer_side) where committer_side is 'offense'/'defense'/'unknown'
    Heuristics:
      - If text mentions one of the team names explicitly -> that team committed
      - If text contains keywords like 'false start' -> offense
      - 'offside' -> defense
      - otherwise None (unknown) — caller can decide default rules (e.g., treat unknown as offense)
    """
    if not isinstance(text, str):
        return (None, "unknown")
    txt = text.lower()
    # check explicit mention of team names
    for candidate in (offense_team, defense_team):
        if not candidate or candidate == "Unknown":
            continue
        name_low = candidate.lower()
        # match basic tokens of the team name
        if re.search(r"\b" + re.escape(name_low) + r"\b", txt):
            return (candidate, "offense" if candidate == offense_team else "defense")
        # also match abbreviations within parentheses like (FAU) etc.
        abbr = "".join([w[0] for w in candidate.split() if w])
        if abbr and abbr.lower() in txt:
            return (candidate, "offense" if candidate == offense_team else "defense")
    # keyword-based defaults
    if "false start" in txt: return (offense_team, "offense")
    if "false start(s)" in txt: return (offense_team, "offense")
    if "delay of game" in txt: return (offense_team, "offense")
    if "illegal formation" in txt: return (offense_team, "offense")
    if "offside" in txt or "offsides" in txt: return (defense_team, "defense")
    if "encroachment" in txt: return (defense_team, "defense")
    # rough heuristics for "holding" - if mentions "offense" or "defense" words
    if "holding" in txt:
        # if 'defensive holding' -> defense; else default to offense
        if "defensive holding" in txt: return (defense_team, "defense")
        return (offense_team, "offense")
    # unknown
    return (None, "unknown")

# --------------------------
# Fetch FBS teams mapping (canonical)
# --------------------------
def load_fbs_teams(local_file=FBS_TEAMS_FILE):
    if os.path.exists(local_file):
        df = pd.read_csv(local_file)
    else:
        data = cache_get(f"{BASE}/teams/fbs")
        if not data:
            raise SystemExit("Could not fetch FBS teams from API and none exists locally.")
        df = pd.DataFrame(data)
        df.to_csv(local_file, index=False)
    # normalize names with your NAME_MAP
    df["school"] = df["school"].replace(NAME_MAP).astype(str)
    return df

# --------------------------
# Fetch rankings, pivot latest week
# --------------------------
def fetch_and_pivot_rankings(year=YEAR):
    raw = cache_get(f"{BASE}/rankings", params={"year": year})
    if not raw:
        return pd.DataFrame()
    # raw likely returns a list of weekly entries; expand polls->ranks
    rows = []
    for row in raw:
        week = row.get("week")
        season = row.get("season")
        polls = row.get("polls") or row.get("rankings") or []
        for poll in polls:
            poll_name = poll.get("poll") or poll.get("name") or "Poll"
            ranks = poll.get("ranks") or poll.get("rankings") or []
            for t in ranks:
                rows.append({
                    "season": season,
                    "week": week,
                    "poll": poll_name,
                    "rank": t.get("rank"),
                    "school": (t.get("school") or t.get("team") or "").strip(),
                    "conference": t.get("conference"),
                    "points": t.get("points", 0)
                })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # canonicalize school names lightly
    df["school"] = df["school"].replace(NAME_MAP)
    # identify latest week and pivot
    latest = df["week"].max()
    latest_df = df[df["week"] == latest].copy()
    pivot = latest_df.pivot_table(index="school", columns="poll", values="rank", aggfunc="first").reset_index()
    pivot.rename(columns={"school": "school_for_merge"}, inplace=True)
    pivot.to_csv(RANKINGS_CSV, index=False)
    return pivot

# --------------------------
# MAIN: collect plays and build outputs
# --------------------------
def main():
    print("Loading FBS teams ...")
    teams_df = load_fbs_teams()
    fbs_set = set(teams_df["school"].astype(str).tolist())

    print("Fetching rankings (latest week pivot)...")
    rankings_pivot = fetch_and_pivot_rankings()
    # make a quick mapping for conference from teams_df
    conf_map = teams_df.set_index("school")["conference"].to_dict()

    all_rows = []
    for week in WEEKS:
        print(f"\n--- Fetching plays for week {week} ---")
        plays = cache_get(f"{BASE}/plays", params={"year": YEAR, "week": week})
        if not plays:
            print("No plays returned for week", week)
            continue
        print(f"Retrieved {len(plays)} plays for week {week}")

        # compute cutoff: find Sunday prior to week end? We'll apply simple rule:
        # For each play, if we can find a game datetime, and it is after the Sunday 06:00 ET cutoff for that game's week -> exclude
        # We'll assume ET = UTC-5 or -4 depending on DST; for simplicity, compute cutoff in UTC as 11:00 (06:00 ET -> 11:00 UTC) when ET = UTC-5,
        # but DST handling is messy. We'll use 06:00 ET approximate as 11:00 UTC, which is fine for week-exclusion (conservative).
        # If no game datetime, keep the play (to avoid accidentally losing data).
        for play in plays:
            text = extract_play_text(play)
            if not text or not looks_like_penalty(text):
                continue

            offense_name = extract_team_name(play, ["offense", "offenseTeam", "possessionTeam", "posteam"], fallback="Unknown")
            defense_name = extract_team_name(play, ["defense", "defenseTeam", "defTeam", "defense_name"], fallback="Unknown")
            # normalize small variations
            offense_name = NAME_MAP.get(offense_name, offense_name)
            defense_name = NAME_MAP.get(defense_name, defense_name)

            # parse time to apply cutoff
            game_dt = extract_game_datetime(play)  # in UTC
            exclude_by_cutoff = False
            if game_dt:
                # approximated cutoff: Sunday 06:00 ET -> approx 11:00 UTC (naive)
                # compute the most recent Sunday for that game_dt (week boundary) and set cutoff
                # We will set cutoff as the Sunday of the game's week at 11:00 UTC
                # find that Sunday's date:
                days_to_sunday = (6 - game_dt.weekday()) % 7
                sunday = (game_dt + timedelta(days=days_to_sunday)).date()
                cutoff_dt_utc = datetime.combine(sunday, datetime.min.time()).replace(tzinfo=timezone.utc) + timedelta(hours=11)
                if game_dt > cutoff_dt_utc:
                    exclude_by_cutoff = True
            # If you want to always include (no cutoff), set exclude_by_cutoff = False

            if exclude_by_cutoff:
                continue

            yards = extract_penalty_yards(text)
            ptype = classify_penalty_type(text)
            pcat = classify_penalty_category(text)

            committer, side = determine_committer(text, offense_name, defense_name)  # may be None
            # If committer is None, choose a safe default: assume offense committed (common), but mark as guessed
            committer_guessed = False
            if committer is None:
                # default rule: false start -> offense; offside -> defense; else assume offense
                if "offside" in (text or "").lower():
                    committer = defense_name
                    side = "defense"
                else:
                    committer = offense_name
                    side = "offense"
                committer_guessed = True

            # determine drawn team (the other team)
            drawn = None
            if committer == offense_name:
                drawn = defense_name
            elif committer == defense_name:
                drawn = offense_name
            else:
                # fallback: if committer equals neither, skip drawn assignment
                drawn = offense_name if committer == defense_name else defense_name

            # add row
            all_rows.append({
                "year": YEAR,
                "week": week,
                "game_datetime_utc": game_dt.isoformat() if game_dt else "",
                "offense": offense_name,
                "defense": defense_name,
                "penalty_text": text,
                "penalty_type": ptype,
                "penalty_category": pcat,
                "penalty_yards": yards,
                "committer": committer,
                "committer_side": side,
                "committer_guessed": committer_guessed,
                "drawn_team": drawn
            })

        # polite pause
        time.sleep(0.8)

    if not all_rows:
        print("No penalty plays collected.")
        return

    raw_df = pd.DataFrame(all_rows)
    raw_out = f"{OUTPUT_PREFIX}_raw_with_meta.csv"
    raw_df.to_csv(raw_out, index=False)
    print(f"Saved raw plays to {raw_out} ({len(raw_df)} rows)")

    # Only keep rows where either committer or drawn team is an FBS school (we want FBS-focused outputs)
    raw_df["committer_is_fbs"] = raw_df["committer"].isin(fbs_set)
    raw_df["drawn_is_fbs"] = raw_df["drawn_team"].isin(fbs_set)
    # include plays where either side is FBS (so drawn vs FCS still included)
    fbs_filter_df = raw_df[(raw_df["committer_is_fbs"]) | (raw_df["drawn_is_fbs"])].copy()

    # -------------------------
    # COMMITTED: weekly and season summary for FBS teams (teams that committed penalties)
    # -------------------------
    committed_weekly = (
        fbs_filter_df[fbs_filter_df["committer_is_fbs"]]
        .groupby(["week","committer","penalty_type","penalty_category"], as_index=False)
        .agg(total_penalties=("penalty_type","count"), total_yards=("penalty_yards","sum"))
    )
    committed_weekly["avg_yards_per_penalty"] = (committed_weekly["total_yards"] / committed_weekly["total_penalties"]).round(2)

    committed_season = (
        committed_weekly.groupby(["committer","penalty_type","penalty_category"], as_index=False)
        .agg(total_penalties=("total_penalties","sum"), total_yards=("total_yards","sum"))
    )
    committed_season["avg_yards_per_penalty"] = (committed_season["total_yards"]/committed_season["total_penalties"]).round(2)

    committed_weekly.to_csv(f"{OUTPUT_PREFIX}_committed_weekly.csv", index=False)
    committed_season.to_csv(f"{OUTPUT_PREFIX}_committed_season.csv", index=False)
    print("Wrote committed summaries (weekly & season).")

    # -------------------------
    # DRAWN: weekly and season summary for FBS teams (teams that drew penalties)
    # -------------------------
    drawn_weekly = (
        fbs_filter_df[fbs_filter_df["drawn_is_fbs"]]
        .groupby(["week","drawn_team","penalty_type","penalty_category"], as_index=False)
        .agg(total_penalties=("penalty_type","count"), total_yards=("penalty_yards","sum"))
    )
    drawn_weekly["avg_yards_per_penalty"] = (drawn_weekly["total_yards"] / drawn_weekly["total_penalties"]).round(2)

    drawn_season = (
        drawn_weekly.groupby(["drawn_team","penalty_type","penalty_category"], as_index=False)
        .agg(total_penalties=("total_penalties","sum"), total_yards=("total_yards","sum"))
    )
    drawn_season["avg_yards_per_penalty"] = (drawn_season["total_yards"]/drawn_season["total_penalties"]).round(2)

    drawn_weekly.to_csv(f"{OUTPUT_PREFIX}_drawn_weekly.csv", index=False)
    drawn_season.to_csv(f"{OUTPUT_PREFIX}_drawn_season.csv", index=False)
    print("Wrote drawn summaries (weekly & season).")

    # -------------------------
    # Merge canonical conference names & rankings to season outputs (committed & drawn)
    # -------------------------
    # teams_df has authoritative mapping of school -> conference
    teams_df["school"] = teams_df["school"].astype(str)
    teams_lookup = teams_df[["school","conference"]].copy()

    # committed season: rename committer -> team
    committed_season = committed_season.rename(columns={"committer":"team"})
    committed_season = committed_season.merge(teams_lookup, how="left", left_on="team", right_on="school")
    committed_season = committed_season.merge(rankings_pivot, how="left", left_on="team", right_on="school_for_merge")
    committed_season["conference"] = committed_season["conference"].fillna("Non-FBS")

    committed_season.to_csv(f"{OUTPUT_PREFIX}_committed_season_with_rankings.csv", index=False)

    drawn_season = drawn_season.rename(columns={"drawn_team":"team"})
    drawn_season = drawn_season.merge(teams_lookup, how="left", left_on="team", right_on="school")
    drawn_season = drawn_season.merge(rankings_pivot, how="left", left_on="team", right_on="school_for_merge")
    drawn_season["conference"] = drawn_season["conference"].fillna("Non-FBS")

    drawn_season.to_csv(f"{OUTPUT_PREFIX}_drawn_season_with_rankings.csv", index=False)

    print("Merged conferences and rankings into season outputs.")

    # Save the filtered raw csv as a convenience
    fbs_filter_df.to_csv(f"{OUTPUT_PREFIX}_raw_with_fbs_filter.csv", index=False)
    print("All done. Files generated.")

if __name__ == "__main__":
    main()
