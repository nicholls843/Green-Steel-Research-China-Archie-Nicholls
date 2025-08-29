import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

# --- Read the CSV with proper encoding ---
file_path = r"C:\Users\archi\Data Visualisations\LCOS Comparisons\LCOS Comparisons.csv"
df = pd.read_csv(file_path, encoding="ISO-8859-1")

# --- Identify cost and solar share columns ---
cost_cols = [col for col in df.columns if "_S" in col and "_Solar" not in col]
solar_cols = [col for col in df.columns if "_Solar" in col]

# --- Helper to normalize year labels ---
def normalize_year_label(yraw: str) -> str:
    y = yraw[1:] if yraw.lower().startswith("y") else yraw
    return "Current" if y.lower() == "current" else y

# --- Melt wide -> long ---
long_df = pd.DataFrame()
for cost_col in cost_cols:
    parts = cost_col.split("_")
    if len(parts) < 2:
        continue
    year_raw, scen_raw = parts[0], parts[1]
    scenario = scen_raw.replace("S", "")
    solar_col = f"{year_raw}_S{scenario}_Solar"
    if solar_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, solar_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Solar_share"]
    temp["Year"] = normalize_year_label(year_raw)
    temp["Scenario"] = scenario
    long_df = pd.concat([long_df, temp], ignore_index=True)

# --- Ensure City alphabetical order ---
long_df["City"] = pd.Categorical(long_df["City"],
                                 categories=sorted(df["City"].unique()),
                                 ordered=True)

# --- Order Year ---
year_order = ["Current", "2030", "2040", "2050"]
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

# --- Marker styles ---
marker_map = {
    "Current": "P",
    "2030": "o",
    "2040": "s",
    "2050": "D"
}

# --- BF–BOF references ---
bf_bof_low, bf_bof_high = 500, 600
bf_bof_2024 = 539.00

# --- Plot for each scenario ---
for scenario in ["1", "2", "3"]:
    fig, ax = plt.subplots(figsize=(16, 8))

    # BF–BOF range band
    ax.axhspan(bf_bof_low, bf_bof_high, facecolor='lightgray', alpha=0.28, zorder=0)

    # City connectors
    for city in long_df["City"].cat.categories:
        subset_city = long_df[(long_df["Scenario"] == scenario) & (long_df["City"] == city)]
        subset_city_sorted = subset_city.sort_values(by="Year")
        ax.plot(subset_city_sorted["City"], subset_city_sorted["Cost"],
                color="gray", linewidth=1, alpha=0.3, zorder=1)

    # Scatter points
    sc = None
    for year, marker in marker_map.items():
        subset = long_df[(long_df["Scenario"] == scenario) & (long_df["Year"] == year)]
        if subset.empty:
            continue
        sc = ax.scatter(subset["City"], subset["Cost"],
                        c=subset["Solar_share"] / 100.0,
                        cmap="RdBu_r", vmin=0.0, vmax=1.0,
                        marker=marker, s=120,
                        edgecolors="k", linewidths=0.6,
                        label=year, zorder=2)

    # BF–BOF average line
    ax.axhline(y=bf_bof_2024, color='dimgray', linestyle='--', linewidth=1.5, zorder=1)
    ax.annotate(f"Avg = ${bf_bof_2024:,.0f}",
                xy=(0.995, bf_bof_2024),
                xycoords=("axes fraction", "data"),
                xytext=(-6, 4),
                textcoords="offset points",
                ha="right", va="bottom", fontsize=9)

    # Formatting
    # ax.set_title(f"Levelised Cost of Green Steel by City (Scenario {scenario})", fontsize=14)
    ax.set_ylabel("USD per tonne of steel", fontsize=12)
    ax.set_xticks(range(len(long_df["City"].cat.categories)))
    ax.set_xticklabels(long_df["City"].cat.categories, rotation=45, ha="right")
    ax.grid(True, linestyle='--', alpha=0.3)

    # Legend 1: Installation Year
    leg1 = ax.legend(title="Installation Year", loc="upper left", bbox_to_anchor=(1.23, 1))
    ax.add_artist(leg1)

    # Legend 2: BF–BOF references (with $ sign in range)
    range_patch = mpatches.Patch(facecolor='lightgray', alpha=0.28,
                                 label=f'BF–BOF range (${bf_bof_low}–${bf_bof_high})')
    avg_line_h = mlines.Line2D([], [], color='dimgray', linestyle='--', linewidth=1.5,
                               label=f'BF–BOF avg 2024 (${bf_bof_2024:,.0f})')
    ax.legend(handles=[range_patch, avg_line_h], title="BF–BOF reference",
              loc="upper left", bbox_to_anchor=(1.23, 0.68))

    # Colorbar with clear meaning for 100% / 0%
    if sc is not None:
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label("Solar share in VRE mix (100% = Solar, 0% = Wind)")
        cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    fig.subplots_adjust(right=0.85)
    plt.savefig(f"LCOS_Scenario_{scenario}.png", dpi=300, bbox_inches='tight')
    plt.show()
