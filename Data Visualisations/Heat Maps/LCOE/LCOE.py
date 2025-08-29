import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as pe
from pathlib import Path

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
lcoe_path      = r"C:\Users\archi\Data Visualisations\Heat Maps\LCOE\LCOE.csv"

# === Choose the layer to map ===
# YEAR in {'YCurrent', 'Y2030', 'Y2040', 'Y2050'}
# SCENARIO in {'S1','S2','S3'}
YEAR = 'YCurrent'
SCENARIO = 'S1'
LCOE_COL = f"{YEAR}_{SCENARIO}"   # e.g., 'YCurrent_S1'

# === Load LCOE data (handle Windows-typical encodings) ===
def read_lcoe_csv(path):
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1", "utf-16", "utf-16le", "utf-16be"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)

lcoe_df = read_lcoe_csv(lcoe_path)

# Basic checks and cleanup
if "Province" not in lcoe_df.columns:
    raise ValueError("Expected a 'Province' column in LCOE.csv.")
if LCOE_COL not in lcoe_df.columns:
    available = [c for c in lcoe_df.columns if ('Y' in c and '_S' in c and 'CAPEX' not in c)]
    raise ValueError(f"Column '{LCOE_COL}' not found. Available LCOE columns include: {available}")

lcoe_df["Province"] = lcoe_df["Province"].astype(str).str.strip()

# Province-level aggregation (mean of city-level LCOE by province)
prov_lcoe = (
    lcoe_df.groupby("Province", as_index=False)[LCOE_COL]
           .mean()
           .rename(columns={LCOE_COL: "LCOE_value"})
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
prov_lcoe["mapped_name"] = prov_lcoe["Province"].map(province_name_map)
china_map = china_map.merge(
    prov_lcoe,
    how="left",
    left_on="name",
    right_on="mapped_name"
)

# Safe province name for labeling (fallback to shapefile 'name')
china_map["Province_for_label"] = (
    china_map.get("Province").astype("string").fillna(china_map["name"])
    if "Province" in china_map.columns else china_map["name"]
)

# === Provinces that should use white label text (by shapefile name and label text) ===
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
    column="LCOE_value",
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

# Colorbar formatting — unit label for LCOE
cbar = plot.get_figure().get_axes()[-1]
cbar.set_ylabel("USD per MWh", rotation=90, labelpad=15)
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
# For dollar signs on ticks, use:
# cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))

# Add province labels — ONLY where we have values (no NaN labels)
for _, row in china_map.iterrows():
    geom = row.get("geometry")
    if geom is None:
        continue
    if pd.notnull(row.get("LCOE_value")):
        point = geom.representative_point()

        shp_name = row.get("name", "")
        label_text = str(row.get("Province_for_label", ""))
        use_white = (shp_name in white_names_shapefile) or startswith_any(label_text, white_prefixes)

        ax.annotate(
            text=f"{label_text}\n{row['LCOE_value']:.0f}",
            xy=(point.x, point.y),
            ha="center",
            fontsize=7,
            color=("white" if use_white else "black"),
            path_effects=[pe.withStroke(linewidth=1, foreground="black")] if use_white else None,
        )

# ax.set_title(f"LCOE (USD per MWh) by Province — {YEAR}, {SCENARIO}", fontsize=14)
ax.axis("off")
plt.tight_layout()

# Optional: save image next to your CSV
out_path = Path(lcoe_path).with_name(f"LCOE_heatmap_{YEAR}_{SCENARIO}.png")
plt.savefig(out_path, dpi=300)
plt.show()
print(f"Saved: {out_path}")
