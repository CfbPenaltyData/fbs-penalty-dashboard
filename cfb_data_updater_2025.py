import requests
import pandas as pd
from tqdm import tqdm
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# CONFIGURATION
# ==============================
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"
YEAR = 2024  # Change to 2025 once data exists
SPREADSHEET_ID = "1ukbajg5iv-hlIW5mOKY-dwls8u7mcj04DOW2aFmS-7E"
SHEET_NAME = "AutoUpdate_Test"

# ==============================
# STEP 1: FETCH FBS TEAMS
# ==============================
print("Fetching FBS teams...")
teams_url = "https://api.collegefootballdata.com/teams/fbs"
r = requests.get(teams_url, headers={"Authorization": f"Bearer {API_KEY}"})
teams = pd.DataFrame(r.json())
print(f"✅ Fetched {len(teams)} FBS teams.")

# ==============================
# STEP 2: FETCH RANKINGS
# ==============================
print("\nFetching rankings (weekly)...")
rank_url = "https://api.collegefootballdata.com/rankings"
r = requests.get(rank_url, headers={"Authorization": f"Bearer {API_KEY}"}, params={"year": YEAR})
rankings = pd.DataFrame(r.json())

if not rankings.empty and "polls" in rankings.columns:
    # Flatten polls
    records = []
    for week in rankings.itertuples():
        for poll in week.polls:
            for rnk in poll["ranks"]:
                records.append({
                    "week": week.week,
                    "poll": poll["poll"],
                    "school": rnk["school"],
                    "rank": rnk["rank"]
                })
    rankings_df = pd.DataFrame(records)
    rankings_df = rankings_df.drop_duplicates(subset=["school", "poll"], keep="last")
else:
    rankings_df = pd.DataFrame(columns=["school", "poll", "rank"])
print(f"✅ Rankings processed. Unique schools: {rankings_df['school'].nunique()}")

# ==============================
# STEP 3: FETCH PENALTY STATS
# ==============================
print("\nFetching penalty stats...")
stats_url = "https://api.collegefootballdata.com/stats/season"
r = requests.get(stats_url, headers={"Authorization": f"Bearer {API_KEY}"}, params={"year": YEAR})
stats = pd.DataFrame(r.json())

# Filter to penalty-related stats only
penalty_stats = stats[stats["statName"].isin(["penalties", "penaltyYards"])]
penalty_pivot = penalty_stats.pivot_table(
    index=["team", "conference"], columns="statName", values="statValue"
).reset_index()

# Compute average yards per penalty
penalty_pivot["penaltyYardsPerPenalty"] = (
    penalty_pivot["penaltyYards"] / penalty_pivot["penalties"]
).round(2)

print(f"✅ Penalty data processed for {len(penalty_pivot)} teams.")

# ==============================
# STEP 4: MERGE WITH RANKINGS
# ==============================
print("\nMerging with rankings and team info...")
merged = teams[["school", "conference"]].merge(
    penalty_pivot, left_on="school", right_on="team", how="left"
).drop(columns=["team"])

merged = merged.merge(rankings_df[["school", "poll", "rank"]], on="school", how="left")

merged = merged.fillna('').replace([float('inf'), float('-inf')], '')

# Clean cell values for Sheets
def flatten_cell(value):
    if isinstance(value, list):
        return ', '.join(map(str, value))
    elif isinstance(value, dict):
        return ', '.join(f"{k}: {v}" for k, v in value.items())
    else:
        return value

merged = merged.applymap(flatten_cell)

# Save locally too
merged.to_csv(f"cfb_penalties_{YEAR}.csv", index=False)
print(f"✅ Saved merged output to cfb_penalties_{YEAR}.csv")

# ==============================
# STEP 5: UPLOAD TO GOOGLE SHEETS
# ==============================
print("\nUploading to Google Sheets...")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
sheet.clear()
sheet.update([merged.columns.values.tolist()] + merged.values.tolist())

print(f"✅ Successfully uploaded penalty data to Google Sheets tab: {SHEET_NAME}")
