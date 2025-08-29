import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import os

# =========================
# User choices
# =========================
hydro_file = r"C:\Users\archi\Data Visualisations\Hydropower\Installed capacity Hydro.csv"
sw_file = r"C:\Users\archi\Data Visualisations\Installed Capacity\Installed Capacity .csv"
SCENARIO = "S1"   # "S1", "S2", "S3"
SAVE_FIG = True
output_folder = r"C:\Users\archi\Data Visualisations\Installed Capacity\charts"

YEARS = ["YCurrent", "Y2030", "Y2040", "Y2050"]

COLORS = {
    "Solar": "#e41a1c",   # Red
    "Wind": "#4daf4a",    # Green
    "Hydro": "#1f77b4"    # Dark blue
}

# =========================
# Load hydro data
# =========================
capacity_factor = 0.46
hours_year = 8760

df_h = pd.read_csv(hydro_file)
df_h["City"] = df_h["City"].astype(str).str.strip()
df_h["Province"] = df_h["Province"].astype(str).str.strip()

gen_cols = [c for c in df_h.columns if "Generation" in c]
for col in gen_cols:
    new_col = col.replace("Total_VRE_Generation", "Hydro_Installed_Capacity")
    df_h[new_col] = df_h[col] / (hours_year * capacity_factor)

df_h = df_h[["City", "Province"] + [c for c in df_h.columns if "Hydro_Installed_Capacity" in c]]
df_h["City"] = df_h["City"] + " (" + df_h["Province"] + ")"

# =========================
# Load Solar/Wind data
# =========================
df_sw = pd.read_csv(sw_file, encoding="utf-8-sig")
df_sw["City"] = df_sw["City"].astype(str).str.strip()
df_sw["Province"] = df_sw["Province"].astype(str).str.strip()
df_sw["City"] = df_sw["City"] + " (" + df_sw["Province"] + ")"

# Extract relevant columns (Solar + Wind only)
cols = ["City"] + [f"{yr}_{SCENARIO}_{t}" for yr in YEARS for t in ["Solar","Wind"]]
df_sw = df_sw[cols]

# =========================
# Merge hydro with Solar/Wind
# =========================
df_merged = df_h.merge(df_sw, on="City", how="inner")

# ---- Sort reverse alphabetical Z → A ----
df_merged = df_merged.sort_values("City", ascending=False)

# Build per-year dataset
plot_data = {}
for yr in YEARS:
    plot_data[yr] = pd.DataFrame({
        "City": df_merged["City"],
        "Hydro": df_merged[f"{yr}_{SCENARIO}_Hydro_Installed_Capacity"],
        "Solar": df_merged[f"{yr}_{SCENARIO}_Solar"],
        "Wind": df_merged[f"{yr}_{SCENARIO}_Wind"]
    })

# =========================
# Plot comparison (Hydro vs Solar+Wind)
# =========================
cities = df_merged["City"].tolist()
ypos = np.arange(len(cities))
fig_h = max(6, 0.35 * len(cities) + 2)

fig, axes = plt.subplots(nrows=1, ncols=4, sharey=True, figsize=(24, fig_h))

for i, yr in enumerate(YEARS):
    ax = axes[i]
    df_y = plot_data[yr]

    # Hydro bars (left group)
    ax.barh(ypos-0.2, df_y["Hydro"], height=0.4, color=COLORS["Hydro"], label="Hydro" if i==0 else None)

    # Solar+Wind stacked (right group)
    left = np.zeros(len(cities))
    for tech in ["Solar","Wind"]:
        ax.barh(ypos+0.2, df_y[tech], height=0.4, left=left, color=COLORS[tech], label=tech if i==0 else None)
        left += df_y[tech]

    ax.set_title(yr)
    ax.set_yticks(ypos)
    if i == 0:
        ax.set_yticklabels(cities, fontsize=9)
    elif i == len(YEARS)-1:
        ax.set_yticklabels([])
        ax_right = ax.twinx()
        ax_right.set_ylim(ax.get_ylim())
        ax_right.set_yticks(ypos)
        ax_right.set_yticklabels(cities, fontsize=9)
        ax_right.tick_params(axis="y", which="both", length=0)
    else:
        ax.set_yticklabels([])

    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f"{int(x):,}"))
    ax.set_xlabel("Installed Capacity (MW)")
    ax.grid(axis="x", linestyle="--", alpha=0.35)

fig.suptitle(f"Hydro vs Installed Capacity (Solar + Wind) by City — {SCENARIO}", y=0.995, fontsize=14)
axes[0].set_ylabel("City")

fig.subplots_adjust(left=0.22, right=0.86, wspace=0.08, bottom=0.08, top=0.92)

if SAVE_FIG:
    os.makedirs(output_folder, exist_ok=True)
    # Save main figure (no legend)
    fname = f"Hydro_vs_SW_{SCENARIO}_by_city_ZtoA.png"
    save_path = os.path.join(output_folder, fname)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"Saved main figure: {save_path}")

plt.show()

# =========================
# Save legend as separate PNG
# =========================
handles = [
    plt.Rectangle((0,0),1,1, color=COLORS["Hydro"]),
    plt.Rectangle((0,0),1,1, color=COLORS["Solar"]),
    plt.Rectangle((0,0),1,1, color=COLORS["Wind"])
]
labels = ["Hydro", "Solar", "Wind"]

fig_leg = plt.figure(figsize=(4,1.2))
plt.legend(handles, labels, loc="center", ncol=3, frameon=False)
plt.axis("off")

if SAVE_FIG:
    legend_path = os.path.join(output_folder, f"Legend_Hydro_vs_SW_{SCENARIO}.png")
    fig_leg.savefig(legend_path, dpi=300, bbox_inches="tight")
    print(f"Saved legend: {legend_path}")

plt.close(fig_leg)
