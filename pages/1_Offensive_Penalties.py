<<<<<<< HEAD
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🚀 Offensive Penalties — Power 4")

@st.cache_data
def load_off():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Offensive_Penalties")

df = load_off()

p4 = ["ACC", "Big 10", "Big 12", "SEC"]
df = df[df["conference"].isin(p4)]

teams = sorted(df["team"].unique())
penalties = sorted(df["penalty_type"].unique())

# Filters
team_filter = st.multiselect("Filter by Team", teams, default=teams)
pen_filter = st.multiselect("Filter by Penalty Type", penalties, default=penalties)

filtered = df[
    df["team"].isin(team_filter) &
    df["penalty_type"].isin(pen_filter)
]

st.subheader("Total Penalties by Type")
fig = px.bar(filtered, x="team", y="total_penalties", color="penalty_type", barmode="stack")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Average Yards per Penalty — by Team")
fig2 = px.bar(filtered.groupby("team")["avg_yards_per_penalty"].mean().reset_index(),
              x="team", y="avg_yards_per_penalty")
st.plotly_chart(fig2, use_container_width=True)
=======
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🚀 Offensive Penalties — Power 4")

@st.cache_data
def load_off():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Offensive_Penalties")

df = load_off()

p4 = ["ACC", "Big 10", "Big 12", "SEC"]
df = df[df["conference"].isin(p4)]

teams = sorted(df["team"].unique())
penalties = sorted(df["penalty_type"].unique())

# Filters
team_filter = st.multiselect("Filter by Team", teams, default=teams)
pen_filter = st.multiselect("Filter by Penalty Type", penalties, default=penalties)

filtered = df[
    df["team"].isin(team_filter) &
    df["penalty_type"].isin(pen_filter)
]

st.subheader("Total Penalties by Type")
fig = px.bar(filtered, x="team", y="total_penalties", color="penalty_type", barmode="stack")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Average Yards per Penalty — by Team")
fig2 = px.bar(filtered.groupby("team")["avg_yards_per_penalty"].mean().reset_index(),
              x="team", y="avg_yards_per_penalty")
st.plotly_chart(fig2, use_container_width=True)
>>>>>>> 91a4d0368a585a7fbf66dd97bc16685e67c89aad
