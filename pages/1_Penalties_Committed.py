import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🚫 Penalties Committed — Power 4 Teams")

@st.cache_data
def load_committed():
    return pd.read_excel(
        "penalties_2025_FBS_with_rankings.xlsx",
        sheet_name="Offensive_Penalties"
    )

df = load_committed()

# All conferences available in the data
conferences = sorted(df["conference"].unique())

# Build options dynamically AFTER conference filter is applied
with st.sidebar:
    st.header("Filters")

    # Conference filter
    conf_filter = st.multiselect(
        "Conference",
        conferences,
        default=["ACC", "Big 10", "Big 12", "SEC"]  # Power 4 default
    )

# Apply conference filter first
df = df[df["conference"].isin(conf_filter)]

teams = sorted(df["team"].unique())
penalties = sorted(df["penalty_type"].unique())

with st.sidebar:
    # Team filter
    team_filter = st.multiselect(
        "Teams",
        teams,
        default=teams
    )

    # Penalty type filter
    pen_filter = st.multiselect(
        "Penalty Types (Committed)",
        penalties,
        default=penalties
    )

# Apply remaining filters
filtered = df[
    df["team"].isin(team_filter) &
    df["penalty_type"].isin(pen_filter)
]

# ————————————
# CHARTS
# ————————————

st.subheader("Total Penalties Committed (by Type)")
fig = px.bar(
    filtered,
    x="team",
    y="total_penalties",
    color="penalty_type",
    barmode="stack",
    title="Total Penalties Committed"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Average Yards Lost — From Penalties Committed")
avg_yards = (
    filtered.groupby("team")["avg_yards_per_penalty"]
    .mean()
    .reset_index()
)

fig2 = px.bar(
    avg_yards,
    x="team",
    y="avg_yards_per_penalty",
    title="Average Yards Lost Per Penalty"
)
st.plotly_chart(fig2, use_container_width=True)
