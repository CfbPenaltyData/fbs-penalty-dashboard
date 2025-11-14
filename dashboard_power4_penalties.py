import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------------------------------
# PAGE CONFIG (MOBILE OPTIMIZED)
# ----------------------------------------------------------
st.set_page_config(
    page_title="Power 4 Penalty Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------
# STYLING FOR MOBILE
# ----------------------------------------------------------
st.markdown("""
<style>
/* Reduce padding for better mobile layout */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx")

df = load_data()

# ----------------------------------------------------------
# TITLE + ONBOARDING MESSAGE
# ----------------------------------------------------------
st.title("🏈 Power 4 Penalties — 2025 Dashboard")

with st.expander("👉 First time here? Click to learn how to use the dashboard."):
    st.markdown("""
### How to Use This Dashboard
- **Use the tabs below** to switch between conferences.
- **Filter by team and week** in the sidebar.
- Charts automatically update based on your filters.
- Works great on **mobile** — rotate your phone for full-width charts.
""")

# ----------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------
st.sidebar.header("Filters")

# Tooltip explanation
st.sidebar.info("Use these filters to compare penalties across teams, weeks, and conferences.")

teams = sorted(df["team"].unique())
weeks = sorted(df["week"].unique())

selected_team = st.sidebar.multiselect(
    "Team (optional):",
    options=teams,
    help="Select one or more teams to highlight"
)

selected_week = st.sidebar.multiselect(
    "Week (optional):",
    options=weeks,
    help="Filter the data to specific weeks"
)

# Apply filters
filtered_df = df.copy()
if selected_team:
    filtered_df = filtered_df[filtered_df["team"].isin(selected_team)]
if selected_week:
    filtered_df = filtered_df[filtered_df["week"].isin(selected_week)]

# ----------------------------------------------------------
# CONFERENCE TABS (MOBILE FRIENDLY)
# ----------------------------------------------------------
power4 = ["ACC", "Big Ten", "Big 12", "SEC"]

tabs = st.tabs(power4)

for i, conf in enumerate(power4):
    with tabs[i]:
        st.subheader(f"{conf} Penalties")

        conf_df = filtered_df[filtered_df["conference"] == conf]

        if conf_df.empty:
            st.warning("No data matches the current filters.")
            continue

        # ------------------------------------------------------
        # CHART: Total penalties per team
        # ------------------------------------------------------
        fig1 = px.bar(
            conf_df.groupby("team")["total_penalties"].sum().reset_index(),
            x="team",
            y="total_penalties",
            title=f"{conf}: Total Penalties by Team",
            text_auto=True
        )
        fig1.update_layout(
            xaxis_title="Team",
            yaxis_title="Total Penalties",
            title_x=0.3
        )
        st.plotly_chart(fig1, use_container_width=True)

        # ------------------------------------------------------
        # CHART: Penalties per week
        # ------------------------------------------------------
        fig2 = px.line(
            conf_df.groupby(["week", "team"])["total_penalties"].sum().reset_index(),
            x="week",
            y="total_penalties",
            color="team",
            markers=True,
            title=f"{conf}: Penalties by Week"
        )
        fig2.update_layout(
            xaxis_title="Week",
            yaxis_title="Penalties",
            legend_title="Team"
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
