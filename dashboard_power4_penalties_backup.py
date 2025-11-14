# dashboard_power4_penalties.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------
# Page config + mobile CSS
# --------------------------
st.set_page_config(page_title="Power 4 Penalties", layout="wide", initial_sidebar_state="auto")

st.markdown(
    """
    <style>
    /* Container padding */
    .block-container { padding-top: 0.8rem; padding-bottom: 1rem; }

    /* Make metric numbers slightly larger on mobile */
    @media (max-width: 600px) {
        [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    }

    /* Reduce plot margins */
    .js-plotly-plot .plotly .main-svg { padding: 0px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏈 Power 4 Penalties — 2025 Dashboard")

# --------------------------
# Helper: find sheet by keyword
# --------------------------
def find_sheet_key(sheet_dict, keywords):
    """Return first sheet name from sheet_dict whose lowercase name contains any keyword."""
    for k in sheet_dict.keys():
        kl = k.lower()
        for kw in keywords:
            if kw in kl:
                return k
    return None

# --------------------------
# Load Excel (all sheets)
# --------------------------
@st.cache_data
def load_all_sheets(path="penalties_2025_FBS_with_rankings.xlsx"):
    try:
        sheets = pd.read_excel(path, sheet_name=None)
        return sheets
    except FileNotFoundError:
        st.error(f"Could not find file: {path}. Make sure it is in the app folder.")
        raise
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        raise

sheets = load_all_sheets()

# Detect reasonable sheet names
off_key = find_sheet_key(sheets, ["offens", "offense", "offensive", "offensive_penalties", "offensive-penalties"])
team_tot_key = find_sheet_key(sheets, ["team_tot", "team totals", "teamtot", "team_totals", "team_totals_summary", "team"])
# fallback: if no explicit found, attempt some common ones
if not off_key:
    off_key = find_sheet_key(sheets, ["penalties", "all", "week"])  # last resort

if not team_tot_key:
    # prefer Team_Totals_Summary or Team Totals
    team_tot_key = find_sheet_key(sheets, ["team_totals", "team totals", "team_totals_summary", "team_totals_summary"])

# Load DataFrames or create friendly errors
if off_key is None:
    st.error("Could not find the Offensive Penalties sheet in the Excel workbook. Expected a sheet with name containing 'offens' or 'offense'.")
    st.stop()
else:
    off_df = sheets[off_key].copy()

# team totals fallback
if team_tot_key:
    team_totals_df = sheets[team_tot_key].copy()
else:
    # derive team totals from offensive data if not present
    team_totals_df = None

# --------------------------
# Clean / canonicalize columns we will use
# --------------------------
def clean_week_col(df, week_col_candidates=["week", "Week", "Wk"]):
    """Make sure df['week'] exists and is integer (extract digits)."""
    # find column
    col = None
    for c in week_col_candidates:
        if c in df.columns:
            col = c
            break
    if col is None:
        # try to find any column named like week ignoring case
        for c in df.columns:
            if str(c).lower().strip() == "week":
                col = c
                break
    if col is None:
        return df  # nothing to do
    # extract digits and coerce to int where possible
    df["week"] = (
        df[col].astype(str).str.extract(r"(\d+)", expand=False)
    )
    # If extraction failed produce NaN; coerce to Int64 if possible
    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")
    return df

# Ensure we have 'team' and 'conference' fields in off_df
if "team" not in off_df.columns and "offense" in off_df.columns:
    off_df = off_df.rename(columns={"offense": "team"})
if "conference" not in off_df.columns:
    # try alternate names
    for alt in ["offenseConference", "conference_offense", "conf"]:
        if alt in off_df.columns:
            off_df = off_df.rename(columns={alt: "conference"})
            break

# Clean week in offense data
off_df = clean_week_col(off_df)

# Ensure total_penalties exists: some sheets are summaries already; if not, set default 1 per play row
if "total_penalties" not in off_df.columns:
    # if this is raw play-level data, assume penalty rows only were selected and use 1
    off_df["total_penalties"] = 1

# Ensure team and conference exist
if "team" not in off_df.columns:
    st.error("Offensive sheet is missing 'team' column. Expected 'team' or 'offense'.")
    st.stop()
if "conference" not in off_df.columns:
    st.info("Conference column not found in offensive sheet — attempting to merge from Team Totals sheet.")
    # If team_totals_df exists try to use it to bring conference data later

# Clean team_totals_df if present
if team_totals_df is not None:
    if "team" not in team_totals_df.columns and "team_canonical" in team_totals_df.columns:
        team_totals_df = team_totals_df.rename(columns={"team_canonical": "team"})
    team_totals_df = clean_week_col(team_totals_df)  # safe

# If team totals absent, build basic team totals from off_df
if team_totals_df is None:
    team_totals_df = (
        off_df.groupby(["team", "conference"], as_index=False)
        .agg(total_penalties=("total_penalties", "sum"))
    )

# Some datasets use "Big 10" vs "Big Ten" naming — we'll accept user's existing conference strings
POWER4 = ["ACC", "Big 10", "Big 12", "SEC"]

# --------------------------
# Sidebar filters (team + week)
# --------------------------
st.sidebar.header("Filters")

# Build master team list (from team_totals_df primary, else from off)
teams_master = sorted(team_totals_df["team"].dropna().unique())
selected_team = st.sidebar.multiselect("Team (optional)", options=teams_master, default=None)

# Weeks: if available in off_df
if "week" in off_df.columns and off_df["week"].notna().any():
    weeks_master = sorted(off_df["week"].dropna().astype(int).unique())
    selected_week = st.sidebar.multiselect("Week (optional)", options=weeks_master, default=None)
else:
    weeks_master = []
    selected_week = None

# Conference pick (quick)
selected_conf = st.sidebar.multiselect("Conference (optional)", options=POWER4, default=POWER4)

# Apply filters
filtered = off_df.copy()
if selected_team:
    filtered = filtered[filtered["team"].isin(selected_team)]
if selected_week:
    # selected_week may be Ints or pandas Int64; coerce
    filtered = filtered[filtered["week"].isin([int(w) for w in selected_week])]
if selected_conf:
    filtered = filtered[filtered["conference"].isin(selected_conf)]

# Also create team totals for the filtered set
filtered_team_totals = (
    filtered.groupby(["team", "conference"], as_index=False)
    .agg(total_penalties=("total_penalties", "sum"))
)

# Merge with existing team_totals_df to get net metrics if present
# if team_totals_df had extra columns like off_total_penalties/def_total_penalties, merge them
if "team" in team_totals_df.columns:
    merged_totals = team_totals_df.merge(filtered_team_totals[["team", "total_penalties"]], how="left", on="team", suffixes=("", "_filtered"))
else:
    merged_totals = filtered_team_totals

# --------------------------
# Tabs for conferences
# --------------------------
tabs = st.tabs(selected_conf if selected_conf else POWER4)

for conf_name, tab in zip(selected_conf if selected_conf else POWER4, tabs):
    with tab:
        st.subheader(f"{conf_name} Penalties")

        conf_df = filtered[filtered["conference"] == conf_name].copy()
        if conf_df.empty:
            st.warning("No data for this conference with current filters.")
            continue

        # Team-level totals (for this conf) aggregated across filtered weeks/teams
        team_tot = (
            conf_df.groupby("team", as_index=False)
            .agg(total_penalties=("total_penalties", "sum"))
            .sort_values("total_penalties", ascending=False)
        )

        # Conference summary metrics
        conf_total = int(team_tot["total_penalties"].sum())
        conf_avg_per_team = round(team_tot["total_penalties"].mean(), 2) if not team_tot.empty else 0
        top_team = team_tot.iloc[0]["team"] if not team_tot.empty else None
        top_team_val = int(team_tot.iloc[0]["total_penalties"]) if not team_tot.empty else 0

        # Display summary metrics
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        col1.metric("Conference Total", f"{conf_total}")
        col2.metric("Avg per Team", f"{conf_avg_per_team}")
        col3.metric("Top Team", f"{top_team} ({top_team_val})" if top_team else "N/A")
        # show weeks available
        if weeks_master:
            col4.metric("Weeks in view", f"{len(filtered['week'].dropna().unique())}")

        st.markdown("---")

        # -----------------------
        # Chart 1: Total penalties per team with conference avg line
        # -----------------------
        fig = px.bar(team_tot, x="team", y="total_penalties", title=f"{conf_name}: Total Penalties by Team")
        # add average horizontal line
        fig.add_hline(y=conf_avg_per_team, line_dash="dash", annotation_text="Conference Avg", annotation_position="top left")
        fig.update_layout(xaxis_title="Team", yaxis_title="Total Penalties", title_x=0.02, margin=dict(l=20, r=20, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # Chart 2: Penalties by week (line per team)
        # -----------------------
        if "week" in conf_df.columns and conf_df["week"].notna().any():
            week_series = (
                conf_df.groupby(["week", "team"], as_index=False)["total_penalties"]
                .sum()
                .sort_values(["week", "team"])
            )

            # pivot to make sure teams are separate lines
            pivot = week_series.pivot(index="week", columns="team", values="total_penalties").fillna(0)

            # build figure
            fig2 = go.Figure()
            for team in pivot.columns:
                fig2.add_trace(go.Scatter(x=pivot.index.astype(int), y=pivot[team], mode="lines+markers", name=str(team)))
            # add conference average per week line
            avg_by_week = pivot.mean(axis=1)
            fig2.add_trace(go.Scatter(x=pivot.index.astype(int), y=avg_by_week, mode="lines", name="Conf Avg (week)", line=dict(color="black", dash="dot")))
            fig2.update_layout(title=f"{conf_name}: Penalties by Week", xaxis_title="Week", yaxis_title="Penalties", margin=dict(l=20, r=20, t=40, b=40))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No week information available — weekly chart is hidden.")

        st.markdown("---")

        # -----------------------
        # Table: Team totals and quick stats
        # -----------------------
        # compute additional columns
        team_tot["pct_of_conf"] = team_tot["total_penalties"] / team_tot["total_penalties"].sum()
        team_tot["pct_of_conf"] = (team_tot["pct_of_conf"] * 100).round(1).astype(str) + "%"

        st.subheader("Team Totals (filtered)")
        st.dataframe(team_tot.reset_index(drop=True), use_container_width=True)

# Footer
st.markdown("---")
st.caption("Notes: Data aggregated from CollegeFootballData-derived sheets. Weeks are parsed from text to integer automatically when possible.")
