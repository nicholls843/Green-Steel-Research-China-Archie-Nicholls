import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as pe
from pathlib import Path

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
lcoh_path      = r"C:\Users\archi\Data Visualisations\Heat Maps\LCOH\LCOH.csv"

# === Choose the layer to map ===
# YEAR in {'YCurrent', 'Y2030', 'Y2040', 'Y2050'}
# SCENARIO in {'S1','S2','S3'}
YEAR = 'YCurrent'
SCENARIO = 'S1'
LCOH_COL = f"{YEAR}_{SCENARIO}"   # e.g., 'YCurrent_S1'

# === Load LCOH data (handle Windows-typical encodings) ===
def read_lcoh_csv(path):
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1", "utf-16", "utf-16le", "utf-16be"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)

lcoh_df = read_lcoh_csv(lcoh_path)

# Basic checks and cleanup
if "Province" not in lcoh_df.columns:
    raise ValueError("Expected a 'Province' column in LCOH.csv.")
if LCOH_COL not in lcoh_df.columns:
    available = [c for c in lcoh_df.columns if ('Y' in c and '_S' in c and 'CAPEX' not in c)]
    raise ValueError(f"Column '{LCOH_COL}' not found. Available LCOH columns include: {available}")

lcoh_df["Province"] = lcoh_df["Province"].astype(str).str.strip()

# Province-level aggregation (mean of city-level LCOH by province)
prov_lcoh = (
    lcoh_df.groupby("Province", as_index=False)[LCOH_COL]
           .mean()
           .rename(columns={LCOH_COL: "LCOH_value"})
)

# === Load map ===
china_map = gpd.read_file(shapefile_path)

# === Province name map (UNCHANGED; NO Gansu fix) ===
province_name_map = {
    "Tibet": "Tibet Autonomous Region",
    "Sichuan": "Sichuan Province",
    "Hubei": "Hubei Province",
    "Hebei": "Hebei Province",
    "Zhejiang": "Zhejiang Province",
    "Yunnan": "Yunnan Province",
    "Guangdong": "Guangdong Province",
    "Guizhou": "Guizhou Province",
    "Hunan": "Hunan Province",
    "Anhui": "Anhui Province",
    "Henan": "Henan Province",
    "Jiangsu": "Jiangsu Province",
    "Jiangxi": "Jiangxi Province",
    "Shandong": "Shandong Province",
    "Fujian": "Fujian Province",
    "Gansu": "Gansu province",  # kept as-is
    "Shaanxi": "Shaanxi Province",
    "Qinghai": "Qinghai Province",
    "Liaoning": "Liaoning Province",
    "Heilongjiang": "Heilongjiang Province",
    "Jilin": "Jilin Province",
    "Beijing": "Beijing Municipality",
    "Tianjin": "Tianjin Municipality",
    "Shanghai": "Shanghai Municipality",
    "Chongqing": "Chongqing Municipality",
    "Shanxi": "Shanxi Province",
    "Hainan": "Hainan Province",
    "Inner Mongolia": "Inner Mongolia Autonomous Region",
    "Ningxia": "Ningxia Hui Autonomous Region",
    "Xinjiang": "Xinjiang Uygur Autonomous Region",
    "Taiwan": "Taiwan Province",
    "Guangxi": "Guangxi Zhuang Autonomous Region"
}

# Map names and merge
prov_lcoh["mapped_name"] = prov_lcoh["Province"].map(province_name_map)
china_map = china_map.merge(
    prov_lcoh,
    how="left",
    left_on="name",
    right_on="mapped_name"
)

# Safe province name for labeling (fallback to shapefile 'name')
china_map["Province_for_label"] = (
    china_map.get("Province").astype("string").fillna(china_map["name"])
    if "Province" in china_map.columns else china_map["name"]
)

# === Provinces that should use white label text ===
white_names_shapefile = {
    "Xinjiang Uygur Autonomous Region",
    "Sichuan Province",
    "Hubei Province",
    "Anhui Province",
}
white_prefixes = {"xinjiang", "sichuan", "hubei", "anhui"}

def startswith_any(s: str, prefixes) -> bool:
    s = (s or "").strip().lower()
    return any(s.startswith(p) for p in prefixes)

# === Plot heat map ===
fig, ax = plt.subplots(figsize=(10, 12))
plot = china_map.plot(
    column="LCOH_value",
    cmap="YlGnBu",             # try 'YlOrRd' if you want "hotter" = higher cost
    linewidth=0.5,
    edgecolor="black",
    legend=True,
    ax=ax,
    missing_kwds={
        "color": "lightgrey",
        "edgecolor": "white",
        "hatch": "///",
        "label": "No data"
    }
)

# Colorbar formatting — unit label + 2 decimal places
cbar = plot.get_figure().get_axes()[-1]
cbar.set_ylabel("USD per kg H2", rotation=90, labelpad=15)
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.2f}'))
# For dollar signs on ticks, use:
# cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.2f}'))

# Add province labels — ONLY where we have values (no NaN labels), 2 decimal places
for _, row in china_map.iterrows():
    geom = row.get("geometry")
    if geom is None:
        continue
    if pd.notnull(row.get("LCOH_value")):
        point = geom.representative_point()

        shp_name = row.get("name", "")
        label_text = str(row.get("Province_for_label", ""))
        use_white = (shp_name in white_names_shapefile) or startswith_any(label_text, white_prefixes)

        ax.annotate(
            text=f"{label_text}\n{row['LCOH_value']:.2f}",
            xy=(point.x, point.y),
            ha="center",
            fontsize=7,
            color=("white" if use_white else "black"),
            path_effects=[pe.withStroke(linewidth=1, foreground="black")] if use_white else None,
        )

# ax.set_title(f"LCOH (USD per kg H2) by Province — {YEAR}, {SCENARIO}", fontsize=14)
ax.axis("off")
plt.tight_layout()

# Optional: save image next to your CSV
out_path = Path(lcoh_path).with_name(f"LCOH_heatmap_{YEAR}_{SCENARIO}.png")
plt.savefig(out_path, dpi=300)
plt.show()
print(f"Saved: {out_path}")
