import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ================= USER SETTINGS =================
CSV_PATH = r"C:\Users\archi\Data Visualisations\Emissions\Emissions.csv"

TOP_N = 10   # Only show top 10 cities

OUTPUT_PNG = r"C:\Users\archi\Data Visualisations\Emissions\figures\Top10_TotalEmissions_tonnes.png"
SAVE_DPI = 220
# =================================================

# Years & scenarios
years       = ["YCurrent", "Y2030", "Y2040", "Y2050"]
year_labels = {"YCurrent": "Current", "Y2030": "2030", "Y2040": "2040", "Y2050": "2050"}
scenarios   = ["S1", "S2", "S3"]
scrap_labels = {"S1": "0% scrap", "S2": "25% scrap", "S3": "50% scrap"}

# Load
df = pd.read_csv(CSV_PATH)

# Add province to city labels
df["CityLabel"] = df["City"] + " (" + df["Province"] + ")"

# Determine baseline for ranking (Current, S1)
baseline_col = "YCurrent_S1_VRE_CO2_tonnes"
df_ranked = df.sort_values(baseline_col, ascending=False).reset_index(drop=True)
df_top = df_ranked.head(TOP_N).copy()

cities = df_top["CityLabel"].tolist()
n_cities = len(cities)

# Colors
colors = {"S1": "#4C78A8", "S2": "#F58518", "S3": "#54A24B"}
bar_h, gap = 0.24, 0.06
offsets = {"S1": -(bar_h + gap), "S2": 0.0, "S3": +(bar_h + gap)}
ypos = np.arange(n_cities)

# Figure: 2x2 grid (one per year)
fig, axes = plt.subplots(2, 2, figsize=(14, max(6, 0.5 * n_cities * 2)))
axes = axes.flatten()

for ax, y in zip(axes, years):
    for s in scenarios:
        col = f"{y}_{s}_VRE_CO2_tonnes"
        vals = df_top[col].values  # already in tonnes
        ax.barh(
            ypos + offsets[s],
            vals,
            height=bar_h,
            color=colors[s],
            edgecolor="none",
            label=scrap_labels[s] if y == "YCurrent" else None,
        )

    ax.set_yticks(ypos)
    ax.set_yticklabels(cities)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle=":", alpha=0.3)

    # Remove X-axis labels for Current and 2030
    if y in ["Y2040", "Y2050"]:
        ax.set_xlabel("Total CO₂ emissions (tCO₂/year)")
    else:
        ax.set_xlabel("")

    ax.set_title(year_labels[y])

# Legend once, below
handles = [plt.Line2D([0], [0], color=colors[s], lw=10) for s in scenarios]
labels = [scrap_labels[s] for s in scenarios]
fig.legend(handles, labels, ncols=3, frameon=False,
           loc="lower center", bbox_to_anchor=(0.5, -0.04))

# === Main title at very top ===
fig.suptitle(
    f"Top {TOP_N} Cities — 1 mtpa Green Steel Total Annual Emissions",
    y=1.04, fontsize=15, fontweight="bold"
)

plt.tight_layout(rect=[0, 0, 1, 0.95])

if OUTPUT_PNG:
    os.makedirs(os.path.dirname(OUTPUT_PNG), exist_ok=True)
    plt.savefig(OUTPUT_PNG, dpi=SAVE_DPI, bbox_inches="tight")
    print(f"Saved: {OUTPUT_PNG}")

plt.show()
