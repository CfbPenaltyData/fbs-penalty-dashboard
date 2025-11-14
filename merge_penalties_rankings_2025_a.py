import pandas as pd
import unicodedata
import math

# ---------------------------
# Helper utilities
# ---------------------------
def normalize_name(s):
    """Normalize string for matching: strip, NFC normalize, remove diacritics, lower."""
    if pd.isna(s):
        return ""
    s = str(s).strip()
    # normalize unicode & remove diacritics
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("\u00A0", " ")  # non-breaking space -> normal
    return " ".join(s.split()).lower()

def apply_map_by_normalized(series, mapping_norm_to_preferred):
    """Replace values in a series using normalized keys in mapping.
       If not found, return original value (stripped)."""
    out = []
    for v in series.fillna("").astype(str):
        key = normalize_name(v)
        if key in mapping_norm_to_preferred:
            out.append(mapping_norm_to_preferred[key])
        else:
            out.append(v.strip())
    return pd.Series(out)

# ---------------------------
# Your manual name mapping (use preferred names)
# Source mapping provided earlier by you — expanded with Northern Illinois
# ---------------------------
raw_mapping = {
    # Conferences
    "Mountain West": "MWC",
    "Mid-American": "MAC",
    "Sun Belt": "SBC",
    "American Athletic": "American",
    "Conference USA": "CUSA",
    "Big Ten": "Big 10",
    "FBS Independents": "Independent",
    "Pac-12": "Pac 12",
    # Teams (examples you provided)
    "Central Michigan": "C Michigan",
    "Eastern Michigan": "E Michigan",
    "Florida Atlantic": "FAU",
    "Florida International": "FIU",
    "James Madison": "J Madison",
    "Louisiana Tech": "La Tech",
    "Massachusetts": "UMass",
    "Middle Tennessee": "MTSU",
    "North Texas": "N Texas",
    "Old Dominion": "ODU",
    "San José State": "San Jose St",   # account for diacritic
    "San Jose State": "San Jose St",
    "South Alabama": "S Alabama",
    "South Florida": "USF",
    "Western Kentucky": "WKU",
    "Western Michigan": "W Michigan",
    "Northern Illinois": "N Illinois",
    # keep original team names that were in list like "Mountain West" if also a team name accidentally - mapping ok
}

# Build normalized mapping dict for robust matching
mapping_norm_to_preferred = {}
for k, v in raw_mapping.items():
    mapping_norm_to_preferred[normalize_name(k)] = v

# Also build a conference-specific map (same keys)
conference_norm_map = {}
for k, v in raw_mapping.items():
    # heuristically treat keys that look like conferences: contains 'conference' or common conference names
    if any(term in k.lower() for term in ["conference", "mountain", "mid-american", "sun belt", "american", "big ten", "pac-12", "fbs independents", "conference usa"]):
        conference_norm_map[normalize_name(k)] = v
# Also ensure we include explicit conference keys from raw_mapping that are conferences
conference_norm_map.update({normalize_name(k): v for k, v in raw_mapping.items() if v in ["MWC","MAC","SBC","American","CUSA","Big 10","Independent","Pac 12"]})

# ---------------------------
# Files / load
# ---------------------------
summary_file = "penalties_2025_FBS_summary.csv"
raw_file = "penalties_2025_FBS_raw.csv"
rankings_file = "rankings_2025_fbs.csv"
teams_file = "fbs_teams.csv"
output_file = "penalties_2025_FBS_with_rankings.xlsx"

print("📂 Loading files...")
pen_summary = pd.read_csv(summary_file)
pen_raw = pd.read_csv(raw_file)
rankings = pd.read_csv(rankings_file)
teams = pd.read_csv(teams_file)

print(f"Loaded: summary={len(pen_summary)} raw={len(pen_raw)} rankings={len(rankings)} teams={len(teams)}")

# ---------------------------
# Normalize text columns (strip & remove weird whitespace)
# ---------------------------
def strip_all_text_columns(df):
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].fillna("").astype(str).map(lambda s: " ".join(s.split()))
strip_all_text_columns(pen_summary)
strip_all_text_columns(pen_raw)
strip_all_text_columns(rankings)
strip_all_text_columns(teams)

# ---------------------------
# Apply canonical name mapping across all datasets
# - We will create canonical fields for team names and for conference names
# ---------------------------

# 1) Canonicalize teams table (source of truth for conferences)
teams["school_canonical"] = apply_map_by_normalized(teams["school"], mapping_norm_to_preferred)
teams["school_norm"] = teams["school"].map(normalize_name)
# canonical conference names from conference mapping if possible, else keep existing
if "conference" in teams.columns:
    teams["conference_canonical"] = apply_map_by_normalized(teams["conference"], mapping_norm_to_preferred)
else:
    teams["conference_canonical"] = teams.get("conference", "").fillna("Non-FBS")

# Ensure no duplicates: if two different canonical versions map to same, keep unique by canonical
teams = teams.drop_duplicates(subset=["school_canonical"]).reset_index(drop=True)

# 2) Canonicalize penalty summary team column
# detect which column holds the team/offense in summary (auto-detect)
team_col = None
for candidate in ["team", "offense", "school", "team_name"]:
    if candidate in pen_summary.columns:
        team_col = candidate
        break
if not team_col:
    raise SystemExit("Could not find team/offense column in summary file.")

pen_summary["team_original"] = pen_summary[team_col].astype(str)
pen_summary["team_canonical"] = apply_map_by_normalized(pen_summary["team_original"], mapping_norm_to_preferred)
pen_summary["team_norm"] = pen_summary["team_original"].map(normalize_name)

# 3) Canonicalize raw play offense & defense
if "offense" in pen_raw.columns:
    pen_raw["offense_original"] = pen_raw["offense"].astype(str)
    pen_raw["offense_canonical"] = apply_map_by_normalized(pen_raw["offense_original"], mapping_norm_to_preferred)
    pen_raw["offense_norm"] = pen_raw["offense_original"].map(normalize_name)
else:
    pen_raw["offense_canonical"] = ""

if "defense" in pen_raw.columns:
    pen_raw["defense_original"] = pen_raw["defense"].astype(str)
    pen_raw["defense_canonical"] = apply_map_by_normalized(pen_raw["defense_original"], mapping_norm_to_preferred)
    pen_raw["defense_norm"] = pen_raw["defense_original"].map(normalize_name)
else:
    pen_raw["defense_canonical"] = ""

# 4) Canonicalize rankings school names
if "school" in rankings.columns:
    rankings["school_original"] = rankings["school"].astype(str)
    rankings["school_canonical"] = apply_map_by_normalized(rankings["school_original"], mapping_norm_to_preferred)
    rankings["school_norm"] = rankings["school_original"].map(normalize_name)
else:
    rankings["school_canonical"] = rankings.get("team", "").astype(str)

# ---------------------------
# Build most recent rankings pivot keyed by canonical school
# ---------------------------
if "week" in rankings.columns:
    latest_week = rankings["week"].max()
    rankings_recent = rankings[rankings["week"] == latest_week].copy()
else:
    rankings_recent = rankings.copy()

# Use canonical school for pivot
rankings_recent["school_for_merge"] = rankings_recent.get("school_canonical", rankings_recent.get("school", rankings_recent.get("team", "")))
rankings_pivot = rankings_recent.pivot_table(index="school_for_merge", columns="poll", values="rank", aggfunc="first").reset_index()
rankings_pivot.rename(columns={"school_for_merge": "school_canonical"}, inplace=True)

# ---------------------------
# Prepare teams lookup keyed by canonical school
# ---------------------------
teams_lookup = teams[["school_canonical", "conference_canonical"]].copy().rename(columns={"conference_canonical": "conference"})
teams_lookup["school_canonical"] = teams_lookup["school_canonical"].astype(str)

# ---------------------------
# Merge for Offensive summary (keep canonical names and canonical conference)
# ---------------------------
# create a working offensive DataFrame using the summary (which already has aggregated totals)
off = pen_summary.copy()
off["team_canonical"] = off["team_canonical"].astype(str)

# --- Merge conference and rankings for Offensive Penalties ---
print("\n🔍 Merging offensive penalties with conferences and rankings...")

# Normalize keys for consistent matching
off["team_norm"] = off["team_canonical"].map(normalize_name)
teams_lookup["school_norm"] = teams_lookup["school_canonical"].map(normalize_name)
rankings_pivot["school_norm"] = rankings_pivot["school_canonical"].map(normalize_name)

# Merge conference from teams_lookup
off = off.merge(
    teams_lookup[["school_norm", "conference"]] if "conference" in teams_lookup.columns else teams_lookup,
    how="left",
    left_on="team_norm",
    right_on="school_norm"
)

# Merge rankings (Top 25)
off = off.merge(
    rankings_pivot,
    how="left",
    left_on="team_norm",
    right_on="school_norm",
    suffixes=("", "_rank")
)

# Drop temp merge columns
off.drop(columns=["team_norm", "school_norm"], errors="ignore", inplace=True)

# --- Diagnostic: check what columns exist now ---
print(f"Available columns in offensive dataset after merge: {list(off.columns)}")

# If no 'conference' column exists, try to locate similar ones
possible_confs = [c for c in off.columns if "conf" in c.lower()]
if not "conference" in off.columns and possible_confs:
    print(f"⚠️ 'conference' column not found, but found similar columns: {possible_confs}")
    off.rename(columns={possible_confs[0]: "conference"}, inplace=True)

# --- Sanity check for missing conferences ---
if "conference" in off.columns:
    missing_conf = off[off["conference"].isna()]
    if not missing_conf.empty:
        print(f"⚠️ Missing conference for {len(missing_conf)} offensive teams:")
        print(missing_conf["team"].unique())
    else:
        print("✅ All offensive teams successfully matched to conferences.")
else:
    print("❌ 'conference' column missing entirely after merge — please verify fbs_teams.csv headers.")

# --- Sanity check for missing conferences ---
missing_conf = off[off["conference"].isna()]
if not missing_conf.empty:
    print(f"⚠️ Missing conference for {len(missing_conf)} offensive teams:")
    print(missing_conf["team"].unique())
else:
    print("✅ All offensive teams successfully matched to conferences.")


# Ensure we have a conference column and only one
if "conference" not in off.columns:
    off["conference"] = "Non-FBS"
else:
    off["conference"] = off["conference"].fillna("Non-FBS")

# compute avg yards per penalty if fields exist (support older column names)
if "total_yards" in off.columns and "total_penalties" in off.columns:
    off["avg_yards_per_penalty"] = off.apply(lambda r: round(r["total_yards"]/r["total_penalties"], 2) if r["total_penalties"] and not math.isnan(r["total_penalties"]) else 0, axis=1)
else:
    # try alternative names
    if "penalty_yards" in off.columns and "total_penalties" in off.columns:
        off["avg_yards_per_penalty"] = off.apply(lambda r: round(r["penalty_yards"]/r["total_penalties"], 2) if r["total_penalties"] and not math.isnan(r["total_penalties"]) else 0, axis=1)
    else:
        off["avg_yards_per_penalty"] = 0

# Keep desired columns and rename for clarity
# prefer: team_canonical, conference, penalty_type, penalty_category (if exists), totals
cols_to_keep = [c for c in ["team_canonical", "conference", "penalty_type", "penalty_category", "total_penalties", "total_yards", "avg_yards_per_penalty"] if c in off.columns]
off_output = off[cols_to_keep].copy()
off_output = off_output.rename(columns={"team_canonical": "team"})

# ---------------------------
# Defensive summary (use raw plays, filter to FBS defenses using canonical names)
# ---------------------------
# filter raw to only FBS defenses by mapping: teams_lookup.school_canonical set
fbs_canonical_set = set(teams_lookup["school_canonical"].astype(str))

# make canonical defense column present
pen_raw["defense_canonical"] = pen_raw.get("defense_canonical", pen_raw.get("defense_original", "")).astype(str)

# Filter to rows where defense canonical is in FBS canonical set
defense_only = pen_raw[pen_raw["defense_canonical"].isin(fbs_canonical_set)].copy()

# Ensure penalty_category is present — prefer play_text to classify
def classify_using_playtext(row):
    # if play_text exists in raw, use it, otherwise fall back to penalty_type
    text = ""
    if "play_text" in row and pd.notna(row["play_text"]) and str(row["play_text"]).strip():
        text = row["play_text"]
    else:
        text = row.get("penalty_type", "")
    return text

# Create penalty_category in defense_only using classify
def categorize_text(t):
    t = str(t).lower()
    if any(x in t for x in ["false start", "delay of game", "offside", "encroachment", "illegal formation", "illegal shift"]):
        return "Procedural"
    elif any(x in t for x in ["holding", "block", "hands to the face", "clipping", "chop block"]):
        return "Blocking / Holding"
    elif any(x in t for x in ["pass interference", "roughing", "unsportsmanlike", "personal foul", "targeting"]):
        return "Personal / Contact"
    elif any(x in t for x in ["substitution", "ineligible", "sideline interference", "illegal touching"]):
        return "Administrative"
    elif any(x in t for x in ["facemask", "horse collar"]):
        return "Safety / Tackling"
    else:
        return "Other"

# apply penalty_category (use play_text if present)
if "play_text" in defense_only.columns:
    defense_only["penalty_category"] = defense_only["play_text"].apply(categorize_text)
else:
    defense_only["penalty_category"] = defense_only["penalty_type"].apply(categorize_text)

# Summarize by defense_canonical, penalty_type, penalty_category
defense_summary = (
    defense_only.groupby(["defense_canonical", "penalty_type", "penalty_category"], as_index=False)
    .agg(total_penalties=("penalty_type", "count"), total_yards=("penalty_yards", "sum"))
)

# compute average yards per penalty
defense_summary["avg_yards_per_penalty"] = defense_summary.apply(lambda r: round(r["total_yards"]/r["total_penalties"], 2) if r["total_penalties"] else 0, axis=1)

# Merge conference & rankings (using canonical keys)
defense_summary = defense_summary.merge(teams_lookup, how="left", left_on="defense_canonical", right_on="school_canonical")
defense_summary = defense_summary.merge(rankings_pivot, how="left", left_on="defense_canonical", right_on="school_canonical")

# rename canonical defense to team for output
defense_output = defense_summary.rename(columns={"defense_canonical": "team", "penalty_type": "penalty_type", "penalty_category": "penalty_category"})
# Keep consistent columns order
def_cols = ["team", "conference", "penalty_type", "penalty_category", "total_penalties", "total_yards", "avg_yards_per_penalty"]
defense_output = defense_output[[c for c in def_cols if c in defense_output.columns]]

# ---------------------------
# Rankings + conferences sheet: ensure canonical school and canonical conference are used
# ---------------------------
rankings_with_confs = rankings_pivot.merge(teams_lookup, how="left", on="school_canonical")
# if conference missing, fill
if "conference" in rankings_with_confs.columns:
    rankings_with_confs["conference"] = rankings_with_confs["conference"].fillna("Non-FBS")
# rename school_canonical back to team
rankings_with_confs = rankings_with_confs.rename(columns={"school_canonical": "team"})

# ---------------------------
# Team totals summary (combine offense & defense totals per canonical team)
# ---------------------------
# offense totals: sum totals in off_output grouped by team
if "team" in off_output.columns:
    off_totals = off_output.groupby("team", as_index=False).agg(
        off_total_penalties=("total_penalties", "sum"),
        off_total_yards=("total_yards", "sum")
    )
else:
    off_totals = pd.DataFrame(columns=["team", "off_total_penalties", "off_total_yards"])

# defense totals: group defense_output by team
def_totals = defense_output.groupby("team", as_index=False).agg(
    def_total_penalties=("total_penalties", "sum"),
    def_total_yards=("total_yards", "sum")
)

# merge both
team_totals = pd.merge(off_totals, def_totals, on="team", how="outer").fillna(0)

# add conference & ranking info from teams_lookup and rankings_pivot
team_totals = team_totals.merge(teams_lookup, how="left", left_on="team", right_on="school_canonical")
team_totals = team_totals.merge(rankings_pivot, how="left", left_on="team", right_on="school_canonical")
team_totals["conference"] = team_totals["conference"].fillna("Non-FBS")
team_totals.drop(columns=["school_canonical_x", "school_canonical_y"], errors="ignore", inplace=True)

# compute net metrics
team_totals["net_penalties"] = team_totals["def_total_penalties"] - team_totals["off_total_penalties"]
team_totals["net_yards"] = team_totals["def_total_yards"] - team_totals["off_total_yards"]

# ---------------------------
# Final exports to Excel (single workbook, consistent sheets)
# ---------------------------
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    off_output.to_excel(writer, sheet_name="Offensive_Penalties", index=False)
    defense_output.to_excel(writer, sheet_name="Defensive_Penalties_Drawn", index=False)
    rankings_with_confs.to_excel(writer, sheet_name="Team_Rankings_and_Confs", index=False)
    team_totals.to_excel(writer, sheet_name="Team_Totals_Summary", index=False)

print(f"✅ Done — wrote: {output_file}")
