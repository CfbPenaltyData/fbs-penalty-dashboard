# pages/1_Penalties_Committed.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("🚫 Penalties Committed — Teams")

# -------------------------
# Files we'll try (fallback order)
# -------------------------
SEASON_CANDIDATES = [
    "penalties_2025_FBS_committed_season_with_rankings.csv",
    "penalties_2025_FBS_committed_season.csv",
    "penalties_2025_FBS_committed_season_with_rankings.csv"
]
WEEKLY_CANDIDATES = [
    "penalties_2025_FBS_committed_weekly.csv"
]
RANKINGS_PIVOT = "rankings_2025_fbs_latest_week_pivot.csv"

@st.cache_data
def load_season_committed():
    for f in SEASON_CANDIDATES:
        if os.path.exists(f):
            try:
                return pd.read_csv(f)
            except Exception:
                continue
    raise FileNotFoundError("Committed season CSV not found. Add one of: " + ", ".join(SEASON_CANDIDATES))

@st.cache_data
def load_weekly_committed():
    for f in WEEKLY_CANDIDATES:
        if os.path.exists(f):
            try:
                return pd.read_csv(f)
            except Exception:
                continue
    return pd.DataFrame()

@st.cache_data
def load_rankings():
    if os.path.exists(RANKINGS_PIVOT):
        try:
            return pd.read_csv(RANKINGS_PIVOT)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# Load both sources (we pick later based on Week selection)
season_df = load_season_committed()
weekly_df = load_weekly_committed()
ranks = load_rankings()

# Normalize columns: committed season probably uses 'committer' as team
if "committer" in season_df.columns:
    season_df = season_df.rename(columns={"committer": "team"})
if "committer" in weekly_df.columns:
    weekly_df = weekly_df.rename(columns={"committer": "team"})

# Ensure penalty_category exists
if "penalty_category" not in season_df.columns:
    def infer_cat(t):
        t = str(t).lower()
        if any(x in t for x in ["false start", "delay of game", "offside", "illegal formation", "encroachment"]):
            return "Procedural"
        if any(x in t for x in ["holding", "block", "clipping", "chop block"]):
            return "Blocking / Holding"
        if any(x in t for x in ["pass interference", "roughing", "targeting", "personal foul", "unsportsmanlike"]):
            return "Personal / Contact"
        if any(x in t for x in ["facemask", "horse collar"]):
            return "Safety / Tackling"
        return "Other"
    season_df["penalty_category"] = season_df.get("penalty_category", season_df.get("penalty_type", "")).apply(infer_cat)

# -------------------------
# Sidebar controls (top)
# -------------------------
st.sidebar.header("Filters")

# Week selector: build from weekly_df if present
week_options = ["All Weeks"]
if not weekly_df.empty and "week" in weekly_df.columns:
    wk_list = sorted(weekly_df["week"].dropna().unique().tolist())
    week_options += [int(w) for w in wk_list]
selected_week = st.sidebar.selectbox("Week (All Weeks = season)", options=week_options, index=0)

# AP toggle
ap_toggle = st.sidebar.checkbox("Show only AP Top 25 (sort by AP rank)", value=False)

# Conference list — dynamic based on chosen dataset
power4_defaults = ["ACC", "Big 10", "Big 12", "SEC"]
# choose source to gather conferences from
if selected_week == "All Weeks":
    confs = sorted(season_df["conference"].dropna().unique().tolist()) if "conference" in season_df.columns else []
else:
    confs = sorted(weekly_df["conference"].dropna().unique().tolist()) if "conference" in weekly_df.columns else []

if not confs:
    confs = power4_defaults

conf_filter = st.sidebar.multiselect("Conference", options=confs, default=power4_defaults if set(power4_defaults).intersection(confs) else confs)

# Team and penalty filters (populated after conference filter applied)
# Load base dataframe based on week selection
if selected_week == "All Weeks":
    df = season_df.copy()
else:
    df = weekly_df.copy()
    # filter to the selected week if weekly
    if selected_week != "All Weeks" and "week" in df.columns:
        df = df[df["week"] == int(selected_week)]

# Filter by conference
if "conference" in df.columns:
    df = df[df["conference"].isin(conf_filter)]

teams = sorted(df["team"].dropna().unique().tolist()) if "team" in df.columns else []
penalties = sorted(df["penalty_type"].dropna().unique().tolist()) if "penalty_type" in df.columns else []

team_filter = st.sidebar.multiselect("Teams", options=teams, default=teams if teams else [])
pen_filter = st.sidebar.multiselect("Penalty Types (Committed)", options=penalties, default=penalties if penalties else [])

# Apply filters
if teams:
    df = df[df["team"].isin(team_filter)]
if penalties:
    df = df[df["penalty_type"].isin(pen_filter)]

# If AP toggle is on, join with rankings and filter/sort by AP Top 25
if ap_toggle and not ranks.empty:
    # ranks file likely has 'school_for_merge' and 'AP Top 25' column
    ap_col = None
    for c in ranks.columns:
        if ("AP" in c and "AP Rank" in c) or c.lower().startswith("ap"):
            ap_col = c
            break
    if ap_col:
        ranks_small = ranks[["school_for_merge", ap_col]].rename(columns={"school_for_merge": "team", ap_col: "AP Rank"})
        # merge and keep only teams with a rank
        df = df.merge(ranks_small, on="team", how="left")
        df = df[df["AP Rank"].notna()]
        df = df.sort_values("AP Rank", ascending=True)
# Create unique ordered team list based on AP Rank sorting
        ordered_teams = df.sort_values("AP Rank")["team"].unique().tolist()

        df["team"] = pd.Categorical(df["team"], categories=ordered_teams, ordered=True)

    else:
        st.sidebar.warning("AP column not found in rankings pivot — AP sort ignored.")
else:
    # default sorting: by total_penalties descending if present
    if "total_penalties" in df.columns:
        df = df.sort_values("total_penalties", ascending=False)

# -------------------------
# Charts
# -------------------------
st.subheader("Total Penalties Committed (by Type)")

if df.empty:
    st.warning("No data available with current filters.")
else:
    fig = px.bar(
        df.groupby(["team", "penalty_type"], as_index=False)["total_penalties"].sum(),
        x="team",
        y="total_penalties",
        color="penalty_type",
        barmode="stack",
        title="Total Penalties Committed"
    )
    fig.update_layout(autosize=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Average Yards Lost — From Penalties Committed")
    if "avg_yards_per_penalty" in df.columns:
        avg_yards = df.groupby("team", as_index=False)["avg_yards_per_penalty"].mean()
        fig2 = px.bar(avg_yards, x="team", y="avg_yards_per_penalty", title="Average Yards Lost Per Penalty")
        fig2.update_layout(autosize=True)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Raw Data (Filtered)")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
