import streamlit as st

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="Home – FBS Penalty Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------
st.sidebar.title("🏠 Home")
st.sidebar.markdown("Welcome to the dashboard!")

# ----------------------------------------------------------
# STYLED TITLE
# ----------------------------------------------------------
st.markdown("""
<h1 style='text-align: center; margin-bottom: 0;'>
    🏈 FBS Penalty Analytics Dashboard<br>(2025 Season)
</h1>
<p style='text-align: center; color: #555; font-size: 18px;'>
    Explore team discipline, penalty patterns, and conference tendencies across the FBS.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------------------------------------------------
# MAIN CONTENT
# ----------------------------------------------------------
st.markdown("""
## 👋 Welcome!

This dashboard provides an interactive way to explore **penalties across every team and conference in FBS**.  
The analysis focuses primarily on the **Power 4 conferences**, but the filters on each page allow you to view **any conference** in the country.

### 🔄 About the Data & Categories
- All data is sourced from the **College Football Data API**.  
- Penalty categories are **still being refined**, and may change as the dataset improves.  
- **Weekly (by-game) penalty data will not work with conference filters.** It will be fixed as soon as **CFB Data** is up and running again.  
- All code and the app framework were created **with the assistance of AI**.

---

## 🧭 How to Navigate the Dashboard

Use the menu on the **left sidebar** to move between sections:

### 🟥 **Penalties Committed**
See which penalties each team commits most frequently.  
Focus on discipline, systemic issues, and high-impact categories.

### 🟦 **Penalties Drawn**
Analyze penalties *drawn against opponents*.  
Useful for understanding aggressiveness, pressure, and matchup behavior.

### 🟩 **Team Penalty Totals**
A full summary of each team’s penalty landscape:
- Total penalties committed  
- Total penalties drawn  
- Net penalty advantage/disadvantage  
- Category breakdowns

### 🟨 **Conference Comparisons**
Explore how entire conferences differ in:
- Penalty tendencies  
- Category distributions  
- Discipline vs aggressiveness markers  

---

## 📈 Tips for Finding Meaningful Trends

- Look at **which categories are consistently high** for teams — these often reflect coaching, scheme, or culture.  
- Compare teams within the **same conference** for normalized evaluation.  
- A high number of **penalties drawn** may indicate strong pass rush, aggressive DB play, or mismatch creation.  
- Use penalty totals to identify **hidden advantages or disadvantages** that never show up in the final score.

---

## 🚧 Coming Soon

### Weekly & Game-Level Data 📅  
CFB Data is currently experiencing an outage. The weekly filters currently won't work with any of the conference data. We are waiting on that resolution, then all filters will work together.

Stay tuned. This website will stay consistent and, as soon as I can get it sorted, will update every week on Sunday for game data and Wednesday for CFP Rankings.

---

## 🙌 Enjoy Exploring!

If you’d like additional visuals, advanced breakdowns, new metrics, or custom team reports, I’m happy to build them!
""", unsafe_allow_html=True)
