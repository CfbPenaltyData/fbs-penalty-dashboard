import requests

# === CONFIG ===
API_KEY = "TDr5Mjoy3TIyYaVryD0Cps2nuxluiK8b7RrCbC5tlqMWTPNbAN6Rl6C4QeAH8PI2"   # <-- Replace this with your actual CFBD key
TEST_URL = "https://api.collegefootballdata.com/teams/fbs"

headers = {"Authorization": f"Bearer {API_KEY}"}

def check_cfbd_usage():
    try:
        r = requests.get(TEST_URL, headers=headers, timeout=10)

        print("\n=== CFBD API USAGE CHECK ===")
        print(f"Status Code: {r.status_code}")

        # Common usage-related headers
        for k, v in r.headers.items():
            if "limit" in k.lower() or "rate" in k.lower():
                print(f"{k}: {v}")

        # If no headers shown, print a note
        if not any("limit" in k.lower() for k in r.headers.keys()):
            print("ℹ️  No rate limit headers returned. "
                  "CFBD may not expose usage via headers in all tiers.")

        print("\nSample data check:", "✅ Success" if r.status_code == 200 else "⚠️ Request failed")

    except Exception as e:
        print("❌ Error checking API usage:", e)

if __name__ == "__main__":
    check_cfbd_usage()
