import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
bof_path = r"C:\Users\archi\Data Visualisations\Heat Maps\Steel\BOF.xlsx"

# === Load BOF data ===
bof_data = pd.read_excel(bof_path)
bof_data.columns = ['province', 'bof_ttpa']
bof_data['province'] = bof_data['province'].str.strip()

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

# Map province names
bof_data['mapped_name'] = bof_data['province'].map(province_name_map)

# Merge BOF data with shapefile
china_map = china_map.merge(bof_data, how='left', left_on='name', right_on='mapped_name')

# === Plot heat map with brown–rust palette ===
fig, ax = plt.subplots(figsize=(10, 12))

plot = china_map.plot(
    column='bof_ttpa',
    cmap='YlOrBr',           # yellow → orange → brown (rusty/dirty steel look)
    linewidth=0.4,
    edgecolor='dimgray',
    legend=True,
    ax=ax,
    missing_kwds={
        "color": "#eeeeee",  # light grey for provinces with no data
        "edgecolor": "dimgray",
        "hatch": "//",
        "label": "No data"
    }
)

# Format colorbar (legend)
cbar = plot.get_figure().get_axes()[-1]
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,} TTPA'))

# Province name annotations
for idx, row in china_map.iterrows():
    if pd.notnull(row['bof_ttpa']):
        point = row['geometry'].representative_point()
        x, y = point.x, point.y

        # Manual offsets for small municipalities
        if row.get('province') == 'Tianjin':
            x += 1.0
        elif row.get('province') == 'Beijing':
            x -= 0.8; y += 0.3
        elif row.get('province') == 'Shanghai':
            y -= 0.5
        elif row.get('province') == 'Chongqing':
            y += 0.5

        # Keep your original label colour rule
        fontcolor = 'white' if row.get('province') == 'Tibet' else 'black'

        ax.annotate(
            text=row.get('province', ''),
            xy=(x, y),
            ha='center',
            fontsize=10,
            color=fontcolor
        )

# Optional: darken background slightly for industrial vibe
fig.patch.set_facecolor('#f7f4f1')  # parchment/industrial paper tone
ax.set_facecolor('#f7f4f1')

ax.axis('off')
plt.tight_layout()
plt.show()