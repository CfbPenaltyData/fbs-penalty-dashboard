import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("📊 Team Penalty Totals — Committed vs Drawn")

# Files (season combined totals produced by pipeline)
COMMITTED_SEASON = "penalties_2025_FBS_committed_season_with_rankings.csv"
DRAWN_SEASON = "penalties_2025_FBS_drawn_season_with_rankings.csv"
COMMITTED_WEEKLY = "penalties_2025_FBS_committed_weekly.csv"
DRAWN_WEEKLY = "penalties_2025_FBS_drawn_weekly.csv"
RANKINGS_PIVOT = "rankings_2025_fbs_latest_week_pivot.csv"

@st.cache_data
def load_committed():
    return pd.read_csv(COMMITTED_SEASON) if os.path.exists(COMMITTED_SEASON) else pd.DataFrame()

@st.cache_data
def load_drawn():
    return pd.read_csv(DRAWN_SEASON) if os.path.exists(DRAWN_SEASON) else pd.DataFrame()

@st.cache_data
def load_weekly_committed():
    return pd.read_csv(COMMITTED_WEEKLY) if os.path.exists(COMMITTED_WEEKLY) else pd.DataFrame()

@st.cache_data
def load_weekly_drawn():
    return pd.read_csv(DRAWN_WEEKLY) if os.path.exists(DRAWN_WEEKLY) else pd.DataFrame()

@st.cache_data
def load_rankings():
    return pd.read_csv(RANKINGS_PIVOT) if os.path.exists(RANKINGS_PIVOT) else pd.DataFrame()


# Load datasets
comm_season = load_committed()
drawn_season = load_drawn()
comm_weekly = load_weekly_committed()
drawn_weekly = load_weekly_drawn()
ranks = load_rankings()

# Normalize team columns to "team"
if "committer" in comm_season.columns:
    comm_season = comm_season.rename(columns={"committer": "team"})
if "drawn_team" in drawn_season.columns:
    drawn_season = drawn_season.rename(columns={"drawn_team": "team"})
if "committer" in comm_weekly.columns:
    comm_weekly = comm_weekly.rename(columns={"committer": "team"})
if "drawn_team" in drawn_weekly.columns:
    drawn_weekly = drawn_weekly.rename(columns={"drawn_team": "team"})

# ---------------------------------------------------------
# 🔧 PRE-BUILD combined list of all teams so the sidebar works
# ---------------------------------------------------------
all_comm = comm_season[["team"]].dropna() if not comm_season.empty else pd.DataFrame(columns=["team"])
all_drawn = drawn_season[["team"]].dropna() if not drawn_season.empty else pd.DataFrame(columns=["team"])

all_totals = pd.concat([all_comm, all_drawn], axis=0).drop_duplicates().reset_index(drop=True)

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
st.sidebar.header("Filters")

# Week options
week_options = ["All Weeks"]
if not comm_weekly.empty and "week" in comm_weekly.columns:
    week_options += sorted(comm_weekly["week"].dropna().unique().tolist())

# Team filter
team_options = sorted(all_totals["team"].dropna().unique())

team_selected = st.sidebar.multiselect(
    "Teams",
    options=team_options,
    default=team_options
)

selected_week = st.sidebar.selectbox("Week (All Weeks = season)", week_options, index=0)
ap_toggle = st.sidebar.checkbox("Show only AP Top 25 (sort by AP rank)", value=False)

# ---------------------------------------------------------
# Build team totals for season or weekly selection
# ---------------------------------------------------------
if selected_week == "All Weeks":
    if not comm_season.empty:
        comm_totals = comm_season.groupby("team", as_index=False).agg(
            off_total_penalties=("total_penalties", "sum"),
            off_total_yards=("total_yards", "sum")
        )
    else:
        comm_totals = pd.DataFrame(columns=["team", "off_total_penalties", "off_total_yards"])

    if not drawn_season.empty:
        drawn_totals = drawn_season.groupby("team", as_index=False).agg(
            def_total_penalties=("total_penalties", "sum"),
            def_total_yards=("total_yards", "sum")
        )
    else:
        drawn_totals = pd.DataFrame(columns=["team", "def_total_penalties", "def_total_yards"])

else:
    # weekly
    wk = int(selected_week)
    comm_df = comm_weekly[comm_weekly["week"] == wk] if not comm_weekly.empty else pd.DataFrame()
    drawn_df = drawn_weekly[drawn_weekly["week"] == wk] if not drawn_weekly.empty else pd.DataFrame()

    comm_totals = comm_df.groupby("team", as_index=False).agg(
        off_total_penalties=("total_penalties", "sum"),
        off_total_yards=("total_yards", "sum")
    ) if not comm_df.empty else pd.DataFrame(columns=["team", "off_total_penalties", "off_total_yards"])

    drawn_totals = drawn_df.groupby("team", as_index=False).agg(
        def_total_penalties=("total_penalties", "sum"),
        def_total_yards=("total_yards", "sum")
    ) if not drawn_df.empty else pd.DataFrame(columns=["team", "def_total_penalties", "def_total_yards"])

# ---------------------------------------------------------
# Merge committed + drawn and apply team filter
# ---------------------------------------------------------
team_totals = (
    pd.merge(comm_totals, drawn_totals, on="team", how="outer")
    .fillna(0)
)

team_totals = team_totals[team_totals["team"].isin(team_selected)]

team_totals["net_penalties"] = team_totals["def_total_penalties"] - team_totals["off_total_penalties"]
team_totals["net_yards"] = team_totals["def_total_yards"] - team_totals["off_total_yards"]

# ---------------------------------------------------------
# Conference mapping
# ---------------------------------------------------------
conf_map = {}
if not comm_season.empty and "conference" in comm_season.columns:
    conf_map = comm_season.set_index("team")["conference"].to_dict()
elif os.path.exists("fbs_teams.csv"):
    try:
        tm = pd.read_csv("fbs_teams.csv")
        conf_map = tm.set_index("school")["conference"].to_dict()
    except Exception:
        pass

team_totals["conference"] = team_totals["team"].map(conf_map).fillna("Non-FBS")

# Conference selector
power4 = ["ACC", "Big 10", "Big 12", "SEC"]
confs = sorted(team_totals["conference"].dropna().unique().tolist())
selected_confs = st.sidebar.multiselect(
    "Select Conferences",
    options=confs,
    default=power4 if set(power4).intersection(confs) else confs
)

team_totals = team_totals[team_totals["conference"].isin(selected_confs)]

# ---------------------------------------------------------
# AP sorting
# ---------------------------------------------------------
if ap_toggle and not ranks.empty:
    ap_col = None
    for c in ranks.columns:
        if ("AP" in c and "AP Top" in c) or c.lower().startswith("ap"):
            ap_col = c
            break

    if ap_col:
        ranks_small = ranks[["school_for_merge", ap_col]].rename(
            columns={"school_for_merge": "team", ap_col: "AP Rank"}
        )
        team_totals = team_totals.merge(ranks_small, on="team", how="left")
        team_totals = team_totals[team_totals["AP Rank"].notna()]
        team_totals = team_totals.sort_values("AP Rank", ascending=True)
else:
    team_totals = team_totals.sort_values("net_penalties", ascending=False)

# ---------------------------------------------------------
# Graphs
# ---------------------------------------------------------
display_count = max(25, len(team_totals))

st.subheader("Penalties Committed vs Penalties Drawn — Total Counts")
if team_totals.empty:
    st.warning("No team totals to show for current filters.")
else:
    fig = px.bar(
        team_totals.head(display_count),
        x="team",
        y=["off_total_penalties", "def_total_penalties"],
        labels={"value": "Count", "variable": "Type"},
        barmode="group",
        title="Penalties Committed vs Drawn (Total Counts)"
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Net Penalties (Drawn – Committed)")
if not team_totals.empty:
    fig2 = px.bar(
        team_totals.head(display_count),
        x="team",
        y="net_penalties",
        color="net_penalties",
        title="Net Penalties (Drawn - Committed)"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Net Penalty Yards (Drawn – Committed)")
if not team_totals.empty:
    fig3 = px.bar(
        team_totals.head(display_count),
        x="team",
        y="net_yards",
        color="net_yards",
        title="Net Penalty Yards (Drawn - Committed)"
    )
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("Raw Team Totals (Filtered)")
st.dataframe(team_totals.reset_index(drop=True), use_container_width=True)
