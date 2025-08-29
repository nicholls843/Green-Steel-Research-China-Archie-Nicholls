import pandas as pd
import matplotlib.pyplot as plt
from adjustText import adjust_text

# === SETTINGS ===
YEAR = "YCurrent"  # Change to "Y2030", "Y2040", "Y2050" as needed
file_path = r"C:\Users\archi\Data Visualisations\LCOH_Land Use Ratio\LCOH_LU Ratio.csv"

# === LOAD DATA ===
df = pd.read_csv(file_path, encoding="ISO-8859-1")
scenarios = ["S1", "S2", "S3"]
colors = ["blue", "green", "red"]
markers = ["o", "s", "D"]

# === PLOT ===
plt.figure(figsize=(14, 8))
texts = []

for sc, color, marker in zip(scenarios, colors, markers):
    lcoh_col = f"{YEAR}_{sc}"               # e.g. "YCurrent_S1"
    land_col = f"{YEAR}_{sc}_Land_Use"      # e.g. "YCurrent_S1_Land_Use"

    lcoh = df[lcoh_col]
    land = df[land_col]

    plt.scatter(
        lcoh, land,
        label=sc,
        color=color,
        marker=marker,
        s=80,
        alpha=0.75,
        edgecolor='black',
        linewidth=0.5
    )

    # Add city labels
    for i in range(len(df)):
        city = df["City"][i]
        texts.append(plt.text(lcoh[i], land[i], city, fontsize=8, alpha=0.7))

# === GUIDE LINES (Median Thresholds) ===
all_lcoh = pd.concat([df[f"{YEAR}_S1"], df[f"{YEAR}_S2"], df[f"{YEAR}_S3"]])
all_land = pd.concat([df[f"{YEAR}_S1_Land_Use"], df[f"{YEAR}_S2_Land_Use"], df[f"{YEAR}_S3_Land_Use"]])

plt.axvline(all_lcoh.median(), linestyle="--", color="gray", alpha=0.4)
plt.axhline(all_land.median(), linestyle="--", color="gray", alpha=0.4)

# === ADJUST TEXT TO AVOID OVERLAP ===
adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

# === AXES AND TITLES ===
plt.xlabel(f"LCOH (USD/kg) – {YEAR}", fontsize=12)
plt.ylabel(f"Land Use (km²) – {YEAR}", fontsize=12)
plt.title(f"LCOH vs Land Use by Scenario – {YEAR}", fontsize=14, fontweight='bold')

# === LEGEND BOX ===
plt.legend(
    title="Scenario",
    title_fontsize=11,
    fontsize=10,
    loc="upper right",
    frameon=True,
    facecolor="white",
    edgecolor="black",
    framealpha=0.9
)

plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()

# === SAVE HIGH-RES IMAGE ===
plt.savefig(f"LCOH_vs_LandUse_{YEAR}.png", dpi=300, bbox_inches="tight")
plt.show()
