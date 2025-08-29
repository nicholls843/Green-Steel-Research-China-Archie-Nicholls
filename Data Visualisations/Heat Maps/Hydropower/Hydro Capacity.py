import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
excel_path = r"C:\Users\archi\Data Visualisations\Heat Maps\Hydropower\Hydropower Capacity.xlsx"

# === Load data ===
hydro_data = pd.read_excel(excel_path)
hydro_data.columns = ['province', 'hydro_capacity_MW']
hydro_data['province'] = hydro_data['province'].str.strip()

china_map = gpd.read_file(shapefile_path)

# === Manual province name map ===
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

# Apply the mapping
hydro_data['mapped_name'] = hydro_data['province'].map(province_name_map)

# Merge with shapefile using mapped names
china_map = china_map.merge(hydro_data, how='left', left_on='name', right_on='mapped_name')

# === Plot heat map ===
fig, ax = plt.subplots(figsize=(10, 12))
plot = china_map.plot(column='hydro_capacity_MW',
               cmap='YlGnBu',
               linewidth=0.5,
               edgecolor='black',
               legend=True,
               ax=ax)

# Access the colorbar (legend)
cbar = plot.get_figure().get_axes()[-1]  # get the colorbar axis (usually the last one)

# Format colorbar tick labels to include ' MW'
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,} MW'))
# === Add labels ===
for idx, row in china_map.iterrows():
    if pd.notnull(row['hydro_capacity_MW']):
        point = row['geometry'].representative_point()

        # Default style
        fontcolor = 'black'

        # Special case: Tibet
        if row['province'] == 'Tibet':
            fontcolor = 'white'

        ax.annotate(
            text=row['province'],
            xy=(point.x, point.y),
            ha='center',
            fontsize=7,
            color=fontcolor
        )


# ax.set_title("Prospective Hydropower Capacity by Province (Megawatts)", fontsize=14)
ax.axis('off')
plt.tight_layout()
plt.show()

print(sorted(china_map['name'].unique()))