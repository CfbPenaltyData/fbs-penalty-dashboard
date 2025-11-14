import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🛡️ Defensive Penalties Drawn — Power 4")

@st.cache_data
def load_def():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Defensive_Penalties_Drawn")

df = load_def()

# Filter to Power 4
p4 = ["ACC", "Big 10", "Big 12", "SEC"]
df = df[df["conference"].isin(p4)]

teams = sorted(df["team"].unique())
penalty_types = sorted(df["penalty_type"].unique())
categories = sorted(df["penalty_category"].unique())

# Sidebar filters
st.sidebar.header("Filters")

team_filter = st.sidebar.multiselect("Team", teams, default=teams)
penalty_filter = st.sidebar.multiselect("Penalty Type", penalty_types, default=penalty_types)
category_filter = st.sidebar.multiselect("Penalty Category", categories, default=categories)

filtered = df[
    df["team"].isin(team_filter) &
    df["penalty_type"].isin(penalty_filter) &
    df["penalty_category"].isin(category_filter)
]

# --------------------
# CHART 1: Stacked bar by penalty type
# --------------------
st.subheader("Total Defensive Penalties Drawn — by Team & Type")

fig = px.bar(
    filtered,
    x="team",
    y="total_penalties",
    color="penalty_type",
    barmode="stack",
    title="Defensive Penalties Drawn (Stacked)"
)
st.plotly_chart(fig, use_container_width=True)

# --------------------
# CHART 2: Penalty category breakdown
# --------------------
st.subheader("Penalty Category Breakdown")

cat_summary = (
    filtered.groupby(["team", "penalty_category"])["total_penalties"]
    .sum()
    .reset_index()
)

fig2 = px.bar(
    cat_summary,
    x="team",
    y="total_penalties",
    color="penalty_category",
    barmode="stack"
)
st.plotly_chart(fig2, use_container_width=True)

# --------------------
# CHART 3: Average yards per penalty
# --------------------
st.subheader("Average Yards per Penalty — Defensive")

avg_yards = (
    filtered.groupby("team")["avg_yards_per_penalty"].mean().reset_index()
)

fig3 = px.bar(avg_yards, x="team", y="avg_yards_per_penalty")
st.plotly_chart(fig3, use_container_width=True)

# --------------------
# Table
# --------------------
st.subheader("Raw Data")
st.dataframe(filtered, use_container_width=True)
