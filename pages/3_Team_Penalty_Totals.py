import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Team Penalty Summary — Power 4")

@st.cache_data
def load_totals():
    return pd.read_excel(
        "penalties_2025_FBS_with_rankings.xlsx",
        sheet_name="Team_Totals_Summary"
    )

df = load_totals()

# ------------------------------------------
# Sidebar Filters
# ------------------------------------------
st.sidebar.header("Filters")

# Conference list
power4 = ["ACC", "Big Ten", "Big 12", "SEC"]

selected_conferences = st.sidebar.multiselect(
    "Select Conferences",
    options=power4,
    default=power4
)

df = df[df["conference"].isin(selected_conferences)]

# Team filter (updates based on selected conferences)
teams = sorted(df["team"].unique())

team_filter = st.sidebar.multiselect(
    "Select Teams",
    options=teams,
    default=teams
)

filtered = df[df["team"].isin(team_filter)]

# ------------------------------------------
# Committed vs Drawn Totals
# ------------------------------------------
st.subheader("Penalties Committed vs Penalties Drawn — Total Counts")

fig = px.bar(
    filtered,
    x="team",
    y=["off_total_penalties", "def_total_penalties"],
    labels={
        "off_total_penalties": "Penalties Committed",
        "def_total_penalties": "Penalties Drawn"
    },
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# Net Penalties
# ------------------------------------------
st.subheader("Net Penalties (Drawn – Committed)")

fig2 = px.bar(
    filtered,
    x="team",
    y="net_penalties",
    color="net_penalties",
    labels={"net_penalties": "Net Penalties (Drawn – Committed)"}
)
st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------
# Net Penalty Yards
# ------------------------------------------
st.subheader("Net Penalty Yards (Drawn – Committed)")

fig3 = px.bar(
    filtered,
    x="team",
    y="net_yards",
    color="net_yards",
    labels={"net_yards": "Net Penalty Yards (Drawn – Committed)"}
)
st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------
# Raw Table
# ------------------------------------------
st.subheader("Raw Team Penalty Totals")
st.dataframe(filtered, use_container_width=True)
