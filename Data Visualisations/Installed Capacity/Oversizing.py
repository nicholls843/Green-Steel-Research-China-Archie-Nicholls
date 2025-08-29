import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from textwrap import wrap

# ==== CONFIG ====
CSV_PATH = r"C:\Users\archi\Data Visualisations\Installed Capacity\Oversizing Factors.csv"
SAVE_BAR = "oversizing_factors_bar.png"

# ==== LOAD ====
df = pd.read_csv(CSV_PATH)

# ---- find only solar and wind oversizing columns ----
col_map = {}
for col in df.columns:
    low = col.lower()
    if "oversizing" in low:
        if "solar" in low:
            col_map[col] = "Solar"
        elif "wind" in low:
            col_map[col] = "Wind"

if not col_map:
    raise ValueError("No Solar or Wind oversizing columns found.")

# ---- use City column as label ----
city_col = next((c for c in df.columns if c.lower() == "city"), None)
if not city_col:
    raise ValueError("No 'City' column found in CSV.")
df["Label"] = df[city_col].astype(str)

# ---- reshape to long format ----
long_df = df.melt(
    id_vars=["Label"],
    value_vars=list(col_map.keys()),
    var_name="Technology_raw",
    value_name="Oversizing factor"
)
long_df["Technology"] = long_df["Technology_raw"].map(col_map)
long_df.drop(columns=["Technology_raw"], inplace=True)

# ---- pivot ----
plot_df = long_df.pivot_table(index="Label", columns="Technology",
                              values="Oversizing factor", aggfunc="mean")

# ---- define consistent Solar/Wind colours ----
solar_color = "#e07b39"  # warm sunlight orange-red
wind_color = "#2a7ab0"   # fresh sky blue

# ---- plot ----
ax = plot_df[["Solar", "Wind"]].plot(
    kind="bar",
    figsize=(14, 6),
    color=[solar_color, wind_color]
)

ax.set_xlabel("City")
ax.set_ylabel("Oversizing factor (Installed / Avg load)")
title = "Solar and Wind Oversizing Factors by City"
ax.set_title("\n".join(wrap(title, 80)))
ax.legend(title="Technology", frameon=False)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

# annotate bars
for container in ax.containers:
    ax.bar_label(container, fmt="%.2f", padding=2, fontsize=8)

plt.savefig(SAVE_BAR, dpi=200, bbox_inches="tight")
print(f"Saved grouped bar chart to: {Path(SAVE_BAR).resolve()}")
