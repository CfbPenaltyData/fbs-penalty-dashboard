import os
import requests
import pandas as pd

BASE_URL = "https://api.collegefootballdata.com"
API_KEY = os.getenv("CFBD_API_KEY")
YEAR = 2024

def fetch_json(endpoint, params=None):
    url = BASE_URL + endpoint
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(url, headers=headers, params=params)

    try:
        response.raise_for_status()
    except Exception:
        print("\n--- CFBD ERROR ---")
        print("URL:", response.url)
        print("Status:", response.status_code)
        print("Body:", response.text[:1000])
        print("------------------\n")
        raise

    try:
        return response.json()
    except Exception:
        print("\n--- JSON DECODE ERROR ---")
        print("URL:", response.url)
        print("Raw:", response.text[:1000])
        print("--------------------------\n")
        raise


def get_teams():
    print("Fetching FBS teams...")
    data = fetch_json("/teams/fbs", params={"year": YEAR})
    return {team["id"]: team["school"] for team in data}


def get_penalties():
    print("Fetching penalties (committed + drawn)...")

    # NEW CORRECT ENDPOINT
    data = fetch_json(
        "/stats/season/penalties",
        params={"year": YEAR}
    )

    return data


def main():
    teams = get_teams()
    penalties = get_penalties()

    df = pd.DataFrame(penalties)

    # Rename for clarity
    df = df.rename(
        columns={
            "teamId": "team_id",
            "team": "team",
            "committed": "committed_penalties",
            "committedYards": "committed_yards",
            "drawn": "drawn_penalties",
            "drawnYards": "drawn_yards",
        }
    )

    # Add team names (safety)
    df["team"] = df["team_id"].map(teams)

    df = df[
        [
            "team_id",
            "team",
            "committed_penalties",
            "committed_yards",
            "drawn_penalties",
            "drawn_yards",
        ]
    ]

    df = df.sort_values("team")

    output = f"penalties_{YEAR}.csv"
    df.to_csv(output, index=False)

    print(f"\n✔ Saved to {output}")
    print(df.head())


if __name__ == "__main__":
    main()
