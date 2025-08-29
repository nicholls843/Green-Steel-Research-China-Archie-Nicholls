import pandas as pd
import matplotlib.pyplot as plt
from adjustText import adjust_text

# === SETTINGS ===
YEAR = "YCurrent"  # Change to "Y2040", "Y2050", etc.
file_path = r"C:\Users\archi\Data Visualisations\LCOS_Land Use Ratio\LCOS_LU Ratio.csv"

# === LOAD DATA ===
df = pd.read_csv(file_path, encoding="ISO-8859-1")
scenarios = ["S1", "S2", "S3"]
colors = ["blue", "green", "red"]
markers = ["o", "s", "D"]

# === PLOT ===
plt.figure(figsize=(14, 8))
texts = []

for sc, color, marker in zip(scenarios, colors, markers):
    lcos_col = f"{YEAR}_{sc}"
    land_col = f"{YEAR}_{sc}_Land_Use"

    lcos = df[lcos_col]
    land = df[land_col]

    plt.scatter(
        lcos, land,
        label=sc,
        color=color,
        marker=marker,
        s=80,
        alpha=0.75,
        edgecolor='black',
        linewidth=0.5
    )

    # Add text labels for each point
    for i in range(len(df)):
        city = df["City"][i]
        texts.append(plt.text(lcos[i], land[i], city, fontsize=8, alpha=0.7))

# === GUIDE LINES (Median Thresholds) ===
all_lcos = pd.concat([df[f"{YEAR}_S1"], df[f"{YEAR}_S2"], df[f"{YEAR}_S3"]])
all_land = pd.concat([df[f"{YEAR}_S1_Land_Use"], df[f"{YEAR}_S2_Land_Use"], df[f"{YEAR}_S3_Land_Use"]])

plt.axvline(all_lcos.median(), linestyle="--", color="gray", alpha=0.4)
plt.axhline(all_land.median(), linestyle="--", color="gray", alpha=0.4)

# === ADJUST TEXT TO AVOID OVERLAP ===
adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

# === AXES AND TITLES ===
plt.xlabel(f"LCOS (USD/tonne) – {YEAR}", fontsize=12)
plt.ylabel(f"Land Use (km²) – {YEAR}", fontsize=12)
plt.title(f"LCOS vs Land Use by Scenario – {YEAR}", fontsize=14, fontweight='bold')

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
plt.savefig(f"LCOS_vs_LandUse_{YEAR}.png", dpi=300, bbox_inches="tight")
plt.show()