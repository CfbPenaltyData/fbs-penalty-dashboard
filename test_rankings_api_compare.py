import requests
import pandas as pd
import json
import os

# === USER SETTINGS ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"  # <-- Replace this with your API key
OUTPUT_DIR = "rankings_test_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === SETUP ===
headers = {"Authorization": f"Bearer {API_KEY}"}
years = [2024, 2025]

def fetch_rankings(year):
    """Fetch rankings data for a specific year and return JSON + DataFrame."""
    url = "https://api.collegefootballdata.com/rankings"
    params = {"year": year}
    print(f"\n📅 Fetching rankings for {year}...")
    r = requests.get(url, headers=headers, params=params, timeout=20)

    if r.status_code != 200:
        print(f"❌ Failed to fetch {year} rankings (HTTP {r.status_code})")
        return None, pd.DataFrame()

    try:
        data = r.json()
        print(f"✅ Retrieved {len(data)} records for {year}")
    except Exception as e:
        print(f"⚠️ JSON decode error for {year}: {e}")
        return None, pd.DataFrame()

    # Convert nested structure to flat DataFrame
    df = pd.json_normalize(data, sep="_")

    # Save raw JSON and flattened CSV
    json_path = os.path.join(OUTPUT_DIR, f"rankings_{year}_raw.json")
    csv_path = os.path.join(OUTPUT_DIR, f"rankings_{year}_flat.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    df.to_csv(csv_path, index=False)

    print(f"💾 Saved JSON → {json_path}")
    print(f"💾 Saved CSV → {csv_path}")
    print(f"🧭 Columns: {', '.join(df.columns[:10])} ...")
    print(f"📊 Sample:\n{df.head(3)}\n")

    return data, df

# === MAIN EXECUTION ===
results = {}
for year in years:
    results[year] = fetch_rankings(year)

print("\n✅ Done. Check the 'rankings_test_output' folder for results.")
print("Compare rankings_2024_flat.csv vs rankings_2025_flat.csv to see structural differences.")
