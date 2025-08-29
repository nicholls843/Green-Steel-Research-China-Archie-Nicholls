import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# === File paths ===
shapefile_path = r"C:\Users\archi\Data Visualisations\Heat Maps\cn_shp\cn.shp"
projects_path = r"C:\Users\archi\Data Visualisations\Heat Maps\Hydropower\Hydropower Projects.csv"

# === Load project data ===
projects_data = pd.read_csv(projects_path)
projects_data.columns = ['province', 'project_count']
projects_data['province'] = projects_data['province'].str.strip()

# === Load map ===
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

# Apply mapping
projects_data['mapped_name'] = projects_data['province'].map(province_name_map)

# Merge
china_map = china_map.merge(projects_data, how='left', left_on='name', right_on='mapped_name')

# === Plot ===
fig, ax = plt.subplots(figsize=(10, 12))
plot = china_map.plot(column='project_count',
                      cmap='YlOrRd',
                      linewidth=0.5,
                      edgecolor='black',
                      legend=True,
                      ax=ax)

# Colorbar formatting
cbar = plot.get_figure().get_axes()[-1]
cbar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x)} projects'))

# Source text
fig.text(0.5, 0.01, "Source: Global Energy Monitor, 2025", ha='center', fontsize=9, color='gray', style='italic')

# Labels
for idx, row in china_map.iterrows():
    if pd.notnull(row['project_count']):
        point = row['geometry'].representative_point()
        fontcolor = 'white' if row['province'] == 'Tibet' else 'black'
        ax.annotate(
            text=row['province'],
            xy=(point.x, point.y),
            ha='center',
            fontsize=7,
            color=fontcolor
        )

ax.set_title("Number of Prospective Hydropower Projects by Province", fontsize=14)
ax.axis('off')
plt.tight_layout()
plt.show()