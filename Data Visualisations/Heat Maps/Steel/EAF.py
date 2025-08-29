import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
eaf_path = r"C:\Users\archi\Data Visualisations\Heat Maps\Steel\EAF.xlsx"

# === Load EAF data ===
eaf_data = pd.read_excel(eaf_path)
eaf_data.columns = ['province', 'eaf_ttpa']
eaf_data['province'] = eaf_data['province'].str.strip()

# === Load China shapefile ===
china_map = gpd.read_file(shapefile_path)

# === Province name mapping ===
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
    "Gansu": "Gansu province",
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

# Apply mapping
eaf_data['mapped_name'] = eaf_data['province'].map(province_name_map)

# Merge EAF data with shapefile
china_map = china_map.merge(eaf_data, how='left', left_on='name', right_on='mapped_name')

# === Plot heat map with clean-tech blue–purple palette ===
fig, ax = plt.subplots(figsize=(10, 12))
plot = china_map.plot(
    column='eaf_ttpa',
    cmap='BuPu',            # clean tech: blue → purple
    linewidth=0.4,
    edgecolor='dimgray',
    legend=True,
    ax=ax,
    missing_kwds={
        "color": "#f0f0f0",  # light grey for no data
        "edgecolor": "dimgray",
        "hatch": "//",
        "label": "No data"
    }
)

# Format colorbar
cbar = plot.get_figure().get_axes()[-1]
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,} TTPA'))

# Labels with manual adjustments
for idx, row in china_map.iterrows():
    if pd.notnull(row['eaf_ttpa']):
        point = row['geometry'].representative_point()
        x, y = point.x, point.y

        if row.get('province') == 'Tianjin':
            x += 0.8
        elif row.get('province') == 'Beijing':
            x -= 0.8; y += 0.3
        elif row.get('province') == 'Shanghai':
            y -= 0.5
        elif row.get('province') == 'Chongqing':
            y += 0.5

        fontcolor = 'white' if row.get('province') == 'Tibet' else 'black'
        ax.annotate(
            text=row.get('province', ''),
            xy=(x, y),
            ha='center',
            fontsize=10,
            color=fontcolor
        )

# Clean, light background
fig.patch.set_facecolor('#f9f9fc')   # soft clean tone
ax.set_facecolor('#f9f9fc')

# ax.set_title("EAF Operating Steel Capacity by Province (TTPA)", fontsize=17)  # optional
ax.axis('off')
plt.tight_layout()
plt.show()
