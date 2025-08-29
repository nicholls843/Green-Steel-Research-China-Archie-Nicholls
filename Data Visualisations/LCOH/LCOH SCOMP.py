import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D

# --- Load LCOH CSV ---
file_path = r"C:\Users\archi\Data Visualisations\LCOH\LCOH.csv"
df = pd.read_csv(file_path, encoding="ISO-8859-1")

# Fix BOM if needed
if "City" not in df.columns:
    df.rename(columns={df.columns[0]: "City"}, inplace=True)

# --- Identify columns ---
# cost columns like: Y2030_S1, Y2040_S2, etc. (exclude any helper columns)
cost_cols = [col for col in df.columns if "_S" in col and "_Ely_oversizing" not in col]
# oversizing columns like: Y2030_S1_Ely_oversizing_factor
oversize_cols = [col for col in df.columns if "_Ely_oversizing_factor" in col]  # not used directly

# --- Reshape to long format ---
long_df = pd.DataFrame()

for cost_col in cost_cols:
    year_tag, scen_tag = cost_col.split("_")[0], cost_col.split("_")[1]
    scenario = scen_tag.replace("S", "")
    oversize_col = f"{year_tag}_S{scenario}_Ely_oversizing_factor"

    if oversize_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, oversize_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Oversize"]

    # Year label
    year_label = year_tag.replace("Y", "") if year_tag != "YCurrent" else "Current"
    temp["Year"] = year_label
    temp["Scenario"] = scenario

    long_df = pd.concat([long_df, temp], ignore_index=True)

# --- Ensure numeric ---
long_df["Cost"] = pd.to_numeric(long_df["Cost"], errors="coerce")
long_df["Oversize"] = pd.to_numeric(long_df["Oversize"], errors="coerce")

# --- City label WITHOUT province ---
long_df["City_Label"] = long_df["City"].fillna("").astype(str).str.strip()

# --- Year ordering ---
year_order = ["Current", "2030", "2040", "2050"]
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

# --- Plot settings ---
years = ["Current", "2030", "2040", "2050"]
scenarios = ["1", "2", "3"]
scenario_offsets = {"1": -0.15, "2": 0.0, "3": 0.15}
markers = {"1": "o", "2": "s", "3": "D"}

# Determine a robust color scale from the data (2nd–98th percentiles)
valid_oversize = long_df["Oversize"].replace([np.inf, -np.inf], np.nan).dropna()
if len(valid_oversize) >= 2:
    vmin = np.nanpercentile(valid_oversize, 2)
    vmax = np.nanpercentile(valid_oversize, 98)
    if vmin == vmax:
        vmin, vmax = float(valid_oversize.min()), float(valid_oversize.max() + 1e-6)
else:
    vmin, vmax = 2.0, 3.5  # fallback

# --- Figure (2x2 small multiples) ---
fig, axes = plt.subplots(2, 2, figsize=(18, 12), sharex=True, sharey=False)
axes = axes.flatten()
last_scatter = None

for ax, yr in zip(axes, years):
    data_y = long_df[long_df["Year"] == yr].copy()
    if data_y.empty:
        ax.set_visible(False)
        continue

    # PER-YEAR sorting so dumbbells are straight (cheapest -> most expensive in THIS year)
    cities_sorted = (
        data_y.groupby("City_Label")["Cost"]
        .mean()
        .sort_values(ascending=True)
        .index
        .tolist()
    )
    city_to_idx = {c: i for i, c in enumerate(cities_sorted)}

    # Draw dumbbell connectors (across scenarios within the year)
    for city_label in cities_sorted:
        row = data_y[data_y["City_Label"] == city_label]
        if row.empty:
            continue
        xs, ys = [], []
        for s in scenarios:
            r = row[row["Scenario"] == s]
            if r.empty:
                continue
            xs.append(float(r["Cost"].iloc[0]))
            ys.append(city_to_idx[city_label] + scenario_offsets[s])
        if len(xs) >= 2:
            ax.plot(xs, ys, linewidth=0.8, alpha=0.35, color="gray")

    # Plot markers for each scenario
    for s in scenarios:
        sub = data_y[data_y["Scenario"] == s]
        if sub.empty:
            continue
        y_vals = sub["City_Label"].map(city_to_idx).astype(float) + scenario_offsets[s]
        last_scatter = ax.scatter(
            x=sub["Cost"],
            y=y_vals,
            c=sub["Oversize"],
            cmap="plasma",      # vivid yellow–purple
            vmin=vmin, vmax=vmax,
            s=80,
            marker=markers[s],
            edgecolors="k",
            linewidths=0.5,
            alpha=0.95,
            label=f"S{s}" if yr == "Current" else None
        )

    # Y-axis labels for this year
    ax.set_yticks(np.arange(len(cities_sorted)))
    ax.set_yticklabels(cities_sorted)
    ax.set_title(f"{yr}", fontsize=13)
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)

# --- Shared settings ---
# fig.suptitle("Levelised Cost of Hydrogen — Scenario Comparison by City (sorted per year; straight dumbbells)", fontsize=16)
for ax in axes[2:]:
    ax.set_xlabel("USD per kg H\u2082", fontsize=12)  # H₂

# Scenario legend (one-time)
handles = [
    Line2D([0],[0], marker='o', linestyle='None', markeredgecolor='k', markerfacecolor='w', markersize=8, label='S1'),
    Line2D([0],[0], marker='s', linestyle='None', markeredgecolor='k', markerfacecolor='0.8', markersize=8, label='S2'),
    Line2D([0],[0], marker='D', linestyle='None', markeredgecolor='k', markerfacecolor='0.5', markersize=8, label='S3'),
]
axes[0].legend(handles=handles, title="Scenario", loc="upper left", frameon=True)

# Colorbar for oversizing factor
if last_scatter is not None:
    cbar = fig.colorbar(last_scatter, ax=axes, fraction=0.02, pad=0.02)
    cbar.set_label("Electrolyser Oversizing Factor")
    cbar.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(r"C:\Users\archi\Data Visualisations\LCOH\LCOH_StraightDumbbells_byYear.png", dpi=300)
plt.show()
