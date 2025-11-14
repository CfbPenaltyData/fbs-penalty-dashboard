import gspread
from google.oauth2.service_account import Credentials

# Path to your service account JSON key file
SERVICE_ACCOUNT_FILE = "service_account.json"  # update if you renamed it

# Define the scope of access (Sheets + Drive)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate and open the client
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Your Google Sheet ID
SHEET_ID = "1ukbajg5iv-hlIW5mOKY-dwls8u7mcj04DOW2aFmS-7E"

# Open the sheet (first worksheet)
sheet = client.open_by_key("1ukbajg5iv-hlIW5mOKY-dwls8u7mcj04DOW2aFmS-7E").worksheet("AutoUpdate_Test")

# Test writing to the sheet
sheet.update('A1', [['YaBoi is in the House']])

print("✅ Successfully updated your Google Sheet!")
