import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="2025 Power 4 Penalty Dashboard",
    layout="wide"
)

st.title("🏈 2025 Power 4 Penalty Analytics Dashboard")

st.markdown("""
Welcome to the interactive dashboard.  
Use the **left sidebar** to navigate:

- **Offensive Penalties**
- **Defensive Penalties**
- **Conference Comparisons**
- **Team Totals**

All pages update automatically when the dataset changes.
""")

# Load the main dataset once here (optional)
@st.cache_data
def load_data():
    return pd.read_excel("penalties_2025_FBS_with_rankings.xlsx")

df = load_data()

st.dataframe(df.head(), use_container_width=True)