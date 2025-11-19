# pages/4_Conference_Comparisons.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("🏆 Conference Penalty Comparisons — Committed Only")

# We'll use the committed season file for conference-level committed views
COMMITTED_SEASON = "penalties_2025_FBS_committed_season_with_rankings.csv"
COMMITTED_WEEKLY = "penalties_2025_FBS_committed_weekly.csv"
RANKINGS_PIVOT = "rankings_2025_fbs_latest_week_pivot.csv"

@st.cache_data
def load_committed_season():
    if os.path.exists(COMMITTED_SEASON):
        return pd.read_csv(COMMITTED_SEASON)
    return pd.DataFrame()

@st.cache_data
def load_rankings():
    if os.path.exists(RANKINGS_PIVOT):
        return pd.read_csv(RANKINGS_PIVOT)
    return pd.DataFrame()

season_df = load_committed_season()
ranks = load_rankings()

# normalize
if "committer" in season_df.columns:
    season_df = season_df.rename(columns={"committer":"team"})

# Sidebar
st.sidebar.header("Filters")

ap_toggle = st.sidebar.checkbox("Show only AP Top 25 (sort by AP rank)", value=False)

# choose df
df = season_df.copy()

# default conference list (Power4)
power4_defaults = ["ACC", "Big 10", "Big 12", "SEC"]
confs = sorted(df["conference"].dropna().unique().tolist()) if "conference" in df.columns else power4_defaults
if not confs:
    confs = power4_defaults

conf_filter = st.sidebar.multiselect("Select Conferences", options=confs, default=power4_defaults if set(power4_defaults).intersection(confs) else confs)
df = df[df["conference"].isin(conf_filter)]

# Optional AP behavior for ordering / filtering the conferences' team lists
if ap_toggle and not ranks.empty:
    ap_col = None
    for c in ranks.columns:
        if ("AP" in c and "AP Top" in c) or c.lower().startswith("ap"):
            ap_col = c
            break
    if ap_col:
        ranks_small = ranks[["school_for_merge", ap_col]].rename(columns={"school_for_merge":"team", ap_col:"AP Rank"})
        df = df.merge(ranks_small, on="team", how="left")
        df = df[df["AP Rank"].notna()]
        df = df.sort_values("AP Rank", ascending=True)
    else:
        st.sidebar.warning("AP column not found in rankings pivot — AP sort ignored.")

# 1) Distribution of penalty TYPE per conference (committed)
st.subheader("📌 Distribution of Penalty Types per Conference")
type_dist = df.groupby(["conference", "penalty_type"], as_index=False)["total_penalties"].sum()
if type_dist.empty:
    st.warning("No committed data available for chosen filters.")
else:
    fig1 = px.bar(type_dist, x="penalty_type", y="total_penalties", color="conference", barmode="group",
                  labels={"penalty_type":"Penalty Type","total_penalties":"Total Penalties Committed"})
    fig1.update_layout(autosize=True)
    st.plotly_chart(fig1, use_container_width=True)

# 2) Distribution of penalty CATEGORY per conference (committed)
st.subheader("📌 Distribution of Penalty Categories per Conference")
cat_dist = df.groupby(["conference","penalty_category"], as_index=False)["total_penalties"].sum()
if cat_dist.empty:
    st.info("No penalty category data available.")
else:
    fig2 = px.bar(cat_dist, x="penalty_category", y="total_penalties", color="conference", barmode="group",
                  labels={"penalty_category":"Penalty Category","total_penalties":"Total Penalties Committed"})
    fig2.update_layout(autosize=True)
    st.plotly_chart(fig2, use_container_width=True)

# 3) Most-Committed Penalty TYPE in each conference
st.subheader("🏆 Most Committed Penalty Type in Each Conference")
top_type = (df.groupby(["conference","penalty_type"], as_index=False)["total_penalties"].sum()
            .sort_values(["conference","total_penalties"], ascending=[True, False])
            .groupby("conference").head(1))
if top_type.empty:
    st.info("No data to show most-committed penalty types.")
else:
    fig3 = px.bar(top_type, x="conference", y="total_penalties", color="penalty_type", text="penalty_type")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(autosize=True)
    st.plotly_chart(fig3, use_container_width=True)

# 4) Most-Committed Penalty CATEGORY in each conference
st.subheader("🏆 Most Committed Penalty Category in Each Conference")
top_cat = (df.groupby(["conference","penalty_category"], as_index=False)["total_penalties"].sum()
           .sort_values(["conference","total_penalties"], ascending=[True, False])
           .groupby("conference").head(1))
if top_cat.empty:
    st.info("No data to show most-committed penalty categories.")
else:
    fig4 = px.bar(top_cat, x="conference", y="total_penalties", color="penalty_category", text="penalty_category")
    fig4.update_traces(textposition="outside")
    fig4.update_layout(autosize=True)
    st.plotly_chart(fig4, use_container_width=True)

with st.expander("🔎 Raw Filtered Data"):
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
