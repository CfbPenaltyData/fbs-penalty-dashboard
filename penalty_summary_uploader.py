import os
import json
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"  # <-- Replace with your CFBD key
YEAR = 2025
LOCAL_SUMMARY_FILE = f"penalties_{YEAR}_allweeks_summary.csv"

# Google Sheets settings
SPREADSHEET_ID = "1ukbajg5iv-hlIW5mOKY-dwls8u7mcj04DOW2aFmS-7E"  # Your sheet ID
TARGET_TAB = "Penalty_Summary_Test"  # Creates/overwrites this tab
SERVICE_ACCOUNT_FILE = "client_secret.json"  # From your earlier setup

# === AUTHENTICATE GOOGLE SHEETS ===
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
client = gspread.authorize(creds)

# === CFBD API SETUP ===
headers = {"Authorization": f"Bearer {API_KEY}"}

def get_json(url, params=None):
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        print(f"⚠️ Failed request: {r.status_code} {url}")
        return []
    try:
        return r.json()
    except:
        return []

# === STEP 1: LOAD PENALTY SUMMARY ===
if not os.path.exists(LOCAL_SUMMARY_FILE):
    raise SystemExit(f"❌ {LOCAL_SUMMARY_FILE} not found. Run the penalty script first.")

summary_df = pd.read_csv(LOCAL_SUMMARY_FILE)
print(f"✅ Loaded {len(summary_df)} penalty summary rows")

# === STEP 2: FETCH TEAM DATA (for conferences, schools, etc.) ===
teams = get_json("https://api.collegefootballdata.com/teams/fbs")
teams_df = pd.DataFrame(teams)[["school", "conference", "abbreviation"]]
print(f"✅ Loaded {len(teams_df)} FBS teams")

# === STEP 3: FETCH RANKINGS ===
rankings = get_json("https://api.collegefootballdata.com/rankings", {"year": YEAR})
expanded = []
for row in rankings:
    season = row.get("season")
    week = row.get("week")
    poll = row.get("poll")
    for entry in row.get("rankings", []):
        expanded.append({
            "season": season,
            "week": week,
            "poll": poll,
            "school": entry.get("school"),
            "rank": entry.get("rank")
        })
rankings_df = pd.DataFrame(expanded)
print(f"✅ Loaded {len(rankings_df)} ranking entries")

# Keep only the latest week for each poll
if not rankings_df.empty:
    rankings_df = rankings_df.sort_values(["poll", "week"], ascending=[True, False]).drop_duplicates(["poll", "school"])

# === STEP 4: MERGE EVERYTHING ===
merged = summary_df.merge(teams_df, how="left", left_on="offense", right_on="school")

if not rankings_df.empty:
    merged = merged.merge(rankings_df[["school", "poll", "rank"]], how="left", on="school")

merged = merged.rename(columns={
    "school": "team_name",
    "conference": "conference",
    "poll": "ranking_poll",
    "rank": "ranking_position"
})

# === STEP 5: CLEANUP ===
merged.fillna("", inplace=True)
print(f"✅ Final merged dataset shape: {merged.shape}")

# === STEP 6: UPLOAD TO GOOGLE SHEETS ===
try:
    sheet = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = sheet.worksheet(TARGET_TAB)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=TARGET_TAB, rows="1000", cols="20")

    ws.update([merged.columns.values.tolist()] + merged.values.tolist())
    print(f"🎉 Successfully uploaded to Google Sheets tab '{TARGET_TAB}'!")
except Exception as e:
    print(f"❌ Google Sheets upload failed: {e}")
