import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Team Total Penalty Summary — Power 4")

@st.cache_data
def load_totals():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Team_Totals_Summary")

df = load_totals()

p4 = ["ACC", "Big 10", "Big 12", "SEC"]
df = df[df["conference"].isin(p4)]

teams = sorted(df["team"].unique())

team_filter = st.multiselect("Select Teams to Display", teams, default=teams)
filtered = df[df["team"].isin(team_filter)]

# -----------------------
# Offense vs. Defense totals
# -----------------------
st.subheader("Offense vs Defense Penalties — Total Counts")

fig = px.bar(
    filtered,
    x="team",
    y=["off_total_penalties", "def_total_penalties"],
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------
# Net penalty count (good vs bad teams)
# -----------------------
st.subheader("Net Penalties (Defense – Offense)")

fig2 = px.bar(
    filtered,
    x="team",
    y="net_penalties",
    color="net_penalties",
)
st.plotly_chart(fig2, use_container_width=True)

# -----------------------
# Yards
# -----------------------
st.subheader("Net Penalty Yards (Defense – Offense)")

fig3 = px.bar(
    filtered,
    x="team",
    y="net_yards",
    color="net_yards",
)
st.plotly_chart(fig3, use_container_width=True)

# -----------------------
# Table view
# -----------------------
st.subheader("Raw Team Totals Data")
st.dataframe(filtered, use_container_width=True)
