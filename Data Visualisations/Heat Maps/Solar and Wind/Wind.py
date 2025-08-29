import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
wind_path = r"C:\Users\archi\Data Visualisations\Heat Maps\Solar and Wind\Wind.xlsx"

# === Load wind data ===
wind_data = pd.read_excel(wind_path)
wind_data.columns = ['province', 'wind_capacity_MW']
wind_data['province'] = wind_data['province'].str.strip()

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
wind_data['mapped_name'] = wind_data['province'].map(province_name_map)

# Merge with map
china_map = china_map.merge(wind_data, how='left', left_on='name', right_on='mapped_name')

# === Plot wind map ===
fig, ax = plt.subplots(figsize=(10, 12))
plot = china_map.plot(column='wind_capacity_MW',
                      cmap='PuBuGn',
                      linewidth=0.5,
                      edgecolor='black',
                      legend=True,
                      ax=ax)

# Format colorbar
cbar = plot.get_figure().get_axes()[-1]
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,} MW'))

# Add province labels
for idx, row in china_map.iterrows():
    if pd.notnull(row['wind_capacity_MW']):
        point = row['geometry'].representative_point()
        fontcolor = 'black'
        ax.annotate(
            text=row['province'],
            xy=(point.x, point.y),
            ha='center',
            fontsize=7,
            color=fontcolor
        )

# ax.set_title("Prospective Wind Capacity by Province (MW)", fontsize=14)
ax.axis('off')
plt.tight_layout()
plt.show()
