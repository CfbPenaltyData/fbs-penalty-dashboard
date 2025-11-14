import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🏈 Conference Penalty Comparison — Penalties Committed Only")

@st.cache_data
def load_committed():
    return pd.read_excel(
        "penalties_2025_FBS_with_rankings.xlsx",
        sheet_name="Offensive_Penalties"   # You can change this if needed
    )

df = load_committed()

# -------------------------------------------------------
# Sidebar — Conference Filter
# -------------------------------------------------------
power4 = ["ACC", "Big 10", "Big 12", "SEC"]

selected_conferences = st.sidebar.multiselect(
    "Select Conferences",
    options=power4,
    default=power4
)

df = df[df["conference"].isin(selected_conferences)]

# -------------------------------------------------------
# 1. Distribution of Penalty TYPE per conference
# -------------------------------------------------------
st.subheader("📌 Distribution of Penalty Types per Conference")

type_dist = df.groupby(["conference", "penalty_type"]).size().reset_index(name="count")

fig1 = px.bar(
    type_dist,
    x="penalty_type",
    y="count",
    color="conference",
    barmode="group",
    labels={
        "penalty_type": "Penalty Type",
        "count": "Total Penalties Committed"
    }
)

st.plotly_chart(fig1, use_container_width=True)

# -------------------------------------------------------
# 2. Distribution of Penalty CATEGORY per conference
# -------------------------------------------------------
st.subheader("📌 Distribution of Penalty Categories per Conference")

cat_dist = df.groupby(["conference", "penalty_category"]).size().reset_index(name="count")

fig2 = px.bar(
    cat_dist,
    x="penalty_category",
    y="count",
    color="conference",
    barmode="group",
    labels={
        "penalty_category": "Penalty Category",
        "count": "Total Penalties Committed"
    }
)

st.plotly_chart(fig2, use_container_width=True)

# -------------------------------------------------------
# 3. Most-Committed Penalty TYPE in each conference
# -------------------------------------------------------
st.subheader("🏆 Most Committed Penalty Type in Each Conference")

top_type = (
    df.groupby(["conference", "penalty_type"])
      .size()
      .reset_index(name="count")
      .sort_values(["conference", "count"], ascending=[True, False])
      .groupby("conference")
      .head(1)
)

fig3 = px.bar(
    top_type,
    x="conference",
    y="count",
    color="penalty_type",
    text="penalty_type",
    labels={
        "count": "Most Frequent Penalty (Committed)",
        "penalty_type": "Penalty Type"
    }
)

fig3.update_traces(textposition="outside")

st.plotly_chart(fig3, use_container_width=True)

# -------------------------------------------------------
# 4. Most-Committed Penalty CATEGORY in each conference
# -------------------------------------------------------
st.subheader("🏆 Most Committed Penalty Category in Each Conference")

top_cat = (
    df.groupby(["conference", "penalty_category"])
      .size()
      .reset_index(name="count")
      .sort_values(["conference", "count"], ascending=[True, False])
      .groupby("conference")
      .head(1)
)

fig4 = px.bar(
    top_cat,
    x="conference",
    y="count",
    color="penalty_category",
    text="penalty_category",
    labels={
        "count": "Most Frequent Penalty Category (Committed)",
        "penalty_category": "Penalty Category"
    }
)

fig4.update_traces(textposition="outside")

st.plotly_chart(fig4, use_container_width=True)

# -------------------------------------------------------
# Show Raw Data (Optional)
# -------------------------------------------------------
with st.expander("🔎 Raw Filtered Data"):
    st.dataframe(df, use_container_width=True)
