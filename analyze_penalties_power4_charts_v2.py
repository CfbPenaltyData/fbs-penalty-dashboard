import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------------------------
# CONFIG
# ---------------------------
input_file = "penalties_2025_FBS_with_rankings.xlsx"
output_file = "penalty_analysis_power4.xlsx"
chart_dir = "charts"
power4 = ["ACC", "Big 10", "Big 12", "SEC"]

# ---------------------------
# LOAD DATA
# ---------------------------
print("📂 Loading data...")
off = pd.read_excel(input_file, sheet_name="Offensive_Penalties")
defn = pd.read_excel(input_file, sheet_name="Defensive_Penalties_Drawn")
rankings = pd.read_excel(input_file, sheet_name="Team_Rankings_and_Confs")
team_totals = pd.read_excel(input_file, sheet_name="Team_Totals_Summary")

print(f"✅ Loaded: Offense={len(off)} Defense={len(defn)} Rankings={len(rankings)} Teams={len(team_totals)}")

# ---------------------------
# FILTER TO POWER 4
# ---------------------------
off_p4 = off[off["conference"].isin(power4)].copy()
defn_p4 = defn[defn["conference"].isin(power4)].copy()
teams_p4 = team_totals[team_totals["conference"].isin(power4)].copy()

print(f"🎯 Power 4 Teams: {teams_p4['team'].nunique()}")

# ---------------------------
# AGGREGATIONS
# ---------------------------
# Offensive patterns
off_summary_type = (
    off_p4.groupby(["conference", "penalty_type"], as_index=False)
    .agg(total_penalties=("total_penalties", "sum"), total_yards=("total_yards", "sum"))
)
off_summary_type["avg_yards_per_penalty"] = round(off_summary_type["total_yards"] / off_summary_type["total_penalties"], 2)

# Defensive patterns
def_summary_type = (
    defn_p4.groupby(["conference", "penalty_type"], as_index=False)
    .agg(total_penalties=("total_penalties", "sum"), total_yards=("total_yards", "sum"))
)
def_summary_type["avg_yards_per_penalty"] = round(def_summary_type["total_yards"] / def_summary_type["total_penalties"], 2)

# Top teams
off_top_teams = (
    off_p4.groupby(["team", "conference"], as_index=False)
    .agg(total_penalties=("total_penalties", "sum"), total_yards=("total_yards", "sum"))
    .sort_values("total_penalties", ascending=False)
    .head(10)
)
def_top_teams = (
    defn_p4.groupby(["team", "conference"], as_index=False)
    .agg(total_penalties=("total_penalties", "sum"), total_yards=("total_yards", "sum"))
    .sort_values("total_penalties", ascending=False)
    .head(10)
)

# Conference summary
conf_summary = (
    teams_p4.groupby("conference", as_index=False)
    .agg(
        total_off_penalties=("off_total_penalties", "sum"),
        total_def_penalties=("def_total_penalties", "sum"),
        total_off_yards=("off_total_yards", "sum"),
        total_def_yards=("def_total_yards", "sum"),
    )
)
conf_summary["net_penalties"] = conf_summary["total_def_penalties"] - conf_summary["total_off_penalties"]
conf_summary["net_yards"] = conf_summary["total_def_yards"] - conf_summary["total_off_yards"]

# Cleanest / dirtiest teams
teams_p4["total_penalties"] = teams_p4["off_total_penalties"] + teams_p4["def_total_penalties"]
cleanest = teams_p4.sort_values("total_penalties").head(10)
dirtiest = teams_p4.sort_values("total_penalties", ascending=False).head(10)

# ---------------------------
# EXPORT EXCEL
# ---------------------------
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    off_summary_type.to_excel(writer, sheet_name="Offensive_Patterns", index=False)
    off_top_teams.to_excel(writer, sheet_name="Top_Off_Teams", index=False)
    def_summary_type.to_excel(writer, sheet_name="Defensive_Patterns", index=False)
    def_top_teams.to_excel(writer, sheet_name="Top_Def_Teams", index=False)
    conf_summary.to_excel(writer, sheet_name="Conference_Comparison", index=False)
    cleanest.to_excel(writer, sheet_name="Cleanest_Teams", index=False)
    dirtiest.to_excel(writer, sheet_name="Dirtiest_Teams", index=False)

print(f"✅ Analysis complete. Results saved to: {output_file}")

# ---------------------------
# CHARTS
# ---------------------------
os.makedirs(chart_dir, exist_ok=True)

def save_bar(df, x, y, title, filename, hue=None, topn=None):
    plt.figure(figsize=(10,6))
    plot_df = df.copy()
    if topn:
        plot_df = plot_df.nlargest(topn, y)
    if hue:
        for conf in plot_df[hue].unique():
            subset = plot_df[plot_df[hue] == conf]
            plt.bar(subset[x], subset[y], label=conf)
        plt.legend()
    else:
        plt.bar(plot_df[x], plot_df[y])
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, filename))
    plt.show()

print("📊 Generating charts...")

# Offensive penalty types by conference
save_bar(
    off_summary_type,
    x="penalty_type", y="total_penalties",
    title="Offensive Penalty Types by Conference (Power 4)",
    filename="offensive_penalty_types.png",
    hue="conference"
)

# Defensive penalty types by conference
save_bar(
    def_summary_type,
    x="penalty_type", y="total_penalties",
    title="Defensive Penalty Types by Conference (Power 4)",
    filename="defensive_penalty_types.png",
    hue="conference"
)

# Cleanest teams
save_bar(
    cleanest,
    x="team", y="total_penalties",
    title="Cleanest Power 4 Teams (Fewest Total Penalties)",
    filename="cleanest_teams.png"
)

# Dirtiest teams
save_bar(
    dirtiest,
    x="team", y="total_penalties",
    title="Dirtiest Power 4 Teams (Most Total Penalties)",
    filename="dirtiest_teams.png"
)

# NEW: Offense vs Defense Penalties by Conference
plt.figure(figsize=(8,6))
width = 0.35
x = range(len(conf_summary))
plt.bar([p - width/2 for p in x], conf_summary["total_off_penalties"], width=width, label="Offense (Committed)")
plt.bar([p + width/2 for p in x], conf_summary["total_def_penalties"], width=width, label="Defense (Drawn)")
plt.xticks(x, conf_summary["conference"])
plt.ylabel("Total Penalties")
plt.title("Offensive vs Defensive Penalties by Conference (Power 4)")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(chart_dir, "conf_off_vs_def.png"))
plt.show()

print(f"✅ All charts saved in '{chart_dir}' folder.")
