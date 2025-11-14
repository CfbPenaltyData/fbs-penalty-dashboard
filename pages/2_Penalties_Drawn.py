import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🎯 Penalties Drawn — Beneficial Penalties Against Opponents")

@st.cache_data
def load_drawn():
    return pd.read_excel(
        "penalties_2025_FBS_with_rankings.xlsx",
        sheet_name="Defensive_Penalties_Drawn"
    )

df = load_drawn()

# All conferences available in the data
conferences = sorted(df["conference"].unique())

# ----------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    # Conference filter (defaults to Power 4)
    conf_filter = st.multiselect(
        "Conference",
        conferences,
        default=["ACC", "Big 10", "Big 12", "SEC"]
    )

# Apply conference filter
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
        "Penalty Types (Drawn From Opponents)",
        penalties,
        default=penalties
    )

# Apply final filters
filtered = df[
    df["team"].isin(team_filter) &
    df["penalty_type"].isin(pen_filter)
]

# ----------------------------------------------------------
# CHARTS
# ----------------------------------------------------------

st.subheader("Total Penalties Drawn — by Type")
fig = px.bar(
    filtered,
    x="team",
    y="total_penalties",
    color="penalty_type",
    barmode="stack",
    title="Total Opponent Penalties (Drawn)"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Average Yards Gained — From Penalties Drawn")
avg_yards = (
    filtered.groupby("team")["avg_yards_per_penalty"]
    .mean()
    .reset_index()
)

fig2 = px.bar(
    avg_yards,
    x="team",
    y="avg_yards_per_penalty",
    title="Average Yards Gained Per Penalty Drawn"
)
st.plotly_chart(fig2, use_container_width=True)
