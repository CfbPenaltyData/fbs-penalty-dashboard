import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="FBS Penalty Dashboard", layout="wide")

st.title("🏈 FBS Penalty Dashboard")
st.markdown("Power 4 Penalties — Updated Automatically")

# -------------------------------
# Load Data
# -------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("rankings_2025_FBS.csv")

df = load_data()

# --------------------------------
# Sidebar Filters (No WEEK Filter)
# --------------------------------
teams = sorted(df["team"].unique())
selected_team = st.sidebar.selectbox("Select a Team", teams)

metric_options = [
    "penalty_yards_per_game",
    "penalties_per_game",
    "penalty_yards",
    "penalties",
]
selected_metric = st.sidebar.selectbox("Select Metric", metric_options)

# --------------------------------
# Filter Data
# --------------------------------
team_df = df[df["team"] == selected_team]

# --------------------------------
# Summary section
# --------------------------------
st.subheader(f"{selected_team} — Season Totals")

left, right = st.columns(2)

with left:
    st.metric("Penalties", int(team_df["penalties"].sum()))

with right:
    st.metric("Penalty Yards", int(team_df["penalty_yards"].sum()))

# --------------------------------
# Rankings Table
# --------------------------------
st.subheader("📊 National Rankings")

ranking_cols = [
    "team",
    "penalties",
    "penalties_per_game",
    "penalty_yards",
    "penalty_yards_per_game",
]

st.dataframe(df[ranking_cols].sort_values("penalty_yards_per_game"))

# --------------------------------
# Chart (no week on x-axis now)
# --------------------------------
st.subheader(f"📈 Team Trend — {selected_metric.replace('_', ' ').title()}")

# If there's no time axis, create a bar or dot plot
chart = (
    alt.Chart(team_df)
    .mark_bar()
    .encode(
        x=alt.X("opponent:N", title="Opponent"),
        y=alt.Y(f"{selected_metric}:Q", title=selected_metric.replace("_", " ").title()),
        tooltip=["team", "opponent", selected_metric],
    )
)

st.altair_chart(chart, use_container_width=True)

st.markdown("---")
st.caption("Data provided by CfbPenaltyData — Auto-updated dashboard")
