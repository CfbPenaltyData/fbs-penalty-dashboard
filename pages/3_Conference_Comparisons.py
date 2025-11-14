<<<<<<< HEAD
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🏆 Power 4 Conference Penalty Comparisons")

@st.cache_data
def load_all():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Offensive_Penalties"), \
           pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Defensive_Penalties_Drawn")

off, deff = load_all()

p4 = ["ACC", "Big 10", "Big 12", "SEC"]
off = off[off["conference"].isin(p4)]
deff = deff[deff["conference"].isin(p4)]

# ---------------------------
# Aggregate totals
# ---------------------------
off_tot = off.groupby("conference")["total_penalties"].sum().reset_index()
def_tot = deff.groupby("conference")["total_penalties"].sum().reset_index()

# ---------------------------
# Combined total penalties
# ---------------------------
combined = off_tot.merge(def_tot, on="conference", how="outer", suffixes=("_off", "_def"))
combined["total_combined"] = combined["total_penalties_off"] + combined["total_penalties_def"]

st.subheader("Total Penalties — Offense vs Defense by Conference")
fig = px.bar(
    combined,
    x="conference",
    y=["total_penalties_off", "total_penalties_def"],
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Combined totals
# ---------------------------
st.subheader("Combined Penalties (Offense + Defense)")
fig2 = px.bar(
    combined,
    x="conference",
    y="total_combined"
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# Penalty type distribution (offense)
# ---------------------------
st.subheader("Offensive Penalty Type Distribution Across Conferences")

off_dist = (
    off.groupby(["conference", "penalty_type"])["total_penalties"]
    .sum()
    .reset_index()
)

fig3 = px.bar(
    off_dist,
    x="conference",
    y="total_penalties",
    color="penalty_type",
    barmode="stack"
)
st.plotly_chart(fig3, use_container_width=True)

# ---------------------------
# Penalty category (defense)
# ---------------------------
st.subheader("Defensive Penalty Category Distribution Across Conferences")

def_dist = (
    deff.groupby(["conference", "penalty_category"])["total_penalties"]
    .sum()
    .reset_index()
)

fig4 = px.bar(
    def_dist,
    x="conference",
    y="total_penalties",
    color="penalty_category",
    barmode="stack"
)
st.plotly_chart(fig4, use_container_width=True)
=======
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🏆 Power 4 Conference Penalty Comparisons")

@st.cache_data
def load_all():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Offensive_Penalties"), \
           pd.read_excel("penalties_2025_FBS_with_rankings.xlsx", sheet_name="Defensive_Penalties_Drawn")

off, deff = load_all()

p4 = ["ACC", "Big 10", "Big 12", "SEC"]
off = off[off["conference"].isin(p4)]
deff = deff[deff["conference"].isin(p4)]

# ---------------------------
# Aggregate totals
# ---------------------------
off_tot = off.groupby("conference")["total_penalties"].sum().reset_index()
def_tot = deff.groupby("conference")["total_penalties"].sum().reset_index()

# ---------------------------
# Combined total penalties
# ---------------------------
combined = off_tot.merge(def_tot, on="conference", how="outer", suffixes=("_off", "_def"))
combined["total_combined"] = combined["total_penalties_off"] + combined["total_penalties_def"]

st.subheader("Total Penalties — Offense vs Defense by Conference")
fig = px.bar(
    combined,
    x="conference",
    y=["total_penalties_off", "total_penalties_def"],
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Combined totals
# ---------------------------
st.subheader("Combined Penalties (Offense + Defense)")
fig2 = px.bar(
    combined,
    x="conference",
    y="total_combined"
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# Penalty type distribution (offense)
# ---------------------------
st.subheader("Offensive Penalty Type Distribution Across Conferences")

off_dist = (
    off.groupby(["conference", "penalty_type"])["total_penalties"]
    .sum()
    .reset_index()
)

fig3 = px.bar(
    off_dist,
    x="conference",
    y="total_penalties",
    color="penalty_type",
    barmode="stack"
)
st.plotly_chart(fig3, use_container_width=True)

# ---------------------------
# Penalty category (defense)
# ---------------------------
st.subheader("Defensive Penalty Category Distribution Across Conferences")

def_dist = (
    deff.groupby(["conference", "penalty_category"])["total_penalties"]
    .sum()
    .reset_index()
)

fig4 = px.bar(
    def_dist,
    x="conference",
    y="total_penalties",
    color="penalty_category",
    barmode="stack"
)
st.plotly_chart(fig4, use_container_width=True)
>>>>>>> 91a4d0368a585a7fbf66dd97bc16685e67c89aad
