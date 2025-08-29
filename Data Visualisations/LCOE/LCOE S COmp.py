import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D

# --- Load LCOE CSV ---
file_path = r"C:\Users\archi\Data Visualisations\LCOE\LCOE.csv"
# If you hit encoding issues, switch to: pd.read_csv(file_path, encoding="ISO-8859-1")
df = pd.read_csv(file_path, encoding="utf-8-sig")

# --- Identify cost columns ---
cost_cols = [col for col in df.columns if "_S" in col and "_Solar" not in col]

# --- Reshape into long format ---
long_df = pd.DataFrame()

for cost_col in cost_cols:
    year_tag, scen_tag = cost_col.split("_")[0], cost_col.split("_")[1]
    scenario = scen_tag.replace("S", "")
    solar_col = f"{year_tag}_S{scenario}_Solar"

    if solar_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, solar_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Solar_share"]

    year_label = year_tag.replace("Y", "") if year_tag != "YCurrent" else "Current"
    temp["Year"] = year_label
    temp["Scenario"] = scenario

    long_df = pd.concat([long_df, temp], ignore_index=True)

# --- Convert to numeric ---
long_df["Cost"] = pd.to_numeric(long_df["Cost"], errors="coerce")
long_df["Solar_share"] = pd.to_numeric(long_df["Solar_share"], errors="coerce")

# --- City label without province ---
long_df["City_Label"] = long_df["City"].fillna("").astype(str).str.strip()

# --- Year and city ordering ---
year_order = ["Current", "2030", "2040", "2050"]
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

avg_costs = (
    long_df.groupby("City_Label")["Cost"]
    .mean()
    .sort_values(ascending=True)
    .index
)
long_df["City_Label"] = pd.Categorical(long_df["City_Label"], categories=avg_costs, ordered=True)

# --- Dumbbell chart setup ---
years = ["Current", "2030", "2040", "2050"]
scenarios = ["1", "2", "3"]
scenario_offsets = {"1": -0.15, "2": 0.0, "3": 0.15}

fig, axes = plt.subplots(2, 2, figsize=(18, 12), sharex=True, sharey=True)
axes = axes.flatten()
last_scatter = None

for ax, yr in zip(axes, years):
    data_y = long_df[long_df["Year"] == yr].copy()
    if data_y.empty:
        ax.set_visible(False)
        continue

    cities = list(long_df["City_Label"].cat.categories)

    # Draw dumbbell connectors
    for i, city_label in enumerate(cities):
        row = data_y[data_y["City_Label"] == city_label]
        if row.empty:
            continue
        xs, ys = [], []
        for s in scenarios:
            r = row[row["Scenario"] == s]
            if r.empty:
                continue
            xs.append(float(r["Cost"].iloc[0]))
            ys.append(i + scenario_offsets[s])
        if len(xs) >= 2:
            ax.plot(xs, ys, linewidth=0.8, alpha=0.35, color="gray")

    # Plot markers
    markers = {"1": "o", "2": "s", "3": "D"}
    for s in scenarios:
        sub = data_y[data_y["Scenario"] == s]
        if sub.empty:
            continue
        y_vals = sub["City_Label"].map({c: i for i, c in enumerate(cities)}).astype(float) + scenario_offsets[s]
        last_scatter = ax.scatter(
            x=sub["Cost"],
            y=y_vals,
            c=sub["Solar_share"] / 100.0,   # 0..1
            cmap="RdBu_r",                  # red = solar-heavy, blue = wind-heavy
            vmin=0.0, vmax=1.0,
            s=80,
            marker=markers[s],
            edgecolors="k",
            linewidths=0.5,
            alpha=0.95,
            label=f"S{s}" if yr == "Current" else None
        )

    ax.set_title(f"{yr}", fontsize=13)
    ax.set_yticks(np.arange(len(cities)))
    ax.set_yticklabels(cities)
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)

# --- Shared settings ---
# fig.suptitle("Levelised Cost of Electricity — Scenario Comparison by City (small multiples by year)", fontsize=16)
for ax in axes[2:]:
    ax.set_xlabel("USD per MWh", fontsize=12)

# Scenario legend
handles = [
    Line2D([0],[0], marker='o', linestyle='None', markeredgecolor='k', markerfacecolor='w', markersize=8, label='S1'),
    Line2D([0],[0], marker='s', linestyle='None', markeredgecolor='k', markerfacecolor='0.8', markersize=8, label='S2'),
    Line2D([0],[0], marker='D', linestyle='None', markeredgecolor='k', markerfacecolor='0.5', markersize=8, label='S3'),
]
axes[0].legend(handles=handles, title="Scenario", loc="upper left", frameon=True)

# Colorbar
if last_scatter is not None:
    cbar = fig.colorbar(last_scatter, ax=axes, fraction=0.02, pad=0.02)
    cbar.set_label("VRE Composition (Solar vs Wind)")
    cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.set_ticklabels([
        "0% Solar\n(100% Wind)",
        "25% Solar\n(75% Wind)",
        "50% Solar\n(50% Wind)",
        "75% Solar\n(25% Wind)",
        "100% Solar\n(0% Wind)"
    ])

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(r"C:\Users\archi\Data Visualisations\LCOE\LCOE_Scenario_Dumbbells_byYear.png", dpi=300)
plt.show()
