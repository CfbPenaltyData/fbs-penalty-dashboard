import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    return pd.read_csv("rankings_2025_FBS.csv")

df = load_data()

st.title("2025 Power 4 Penalty Dashboard")

# Use the correct column name
team_col = "school"

# Generate list of teams
teams = sorted(df[team_col].unique())

# Sidebar – Select Team
selected_team = st.sidebar.selectbox("Select a Team", teams)

# Filter data for selected team
team_data = df[df[team_col] == selected_team]

# Display team summary
st.subheader(f"{selected_team} Summary")
st.write(team_data)
