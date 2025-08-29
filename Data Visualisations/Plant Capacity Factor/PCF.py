import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors as mcolors

# File path (raw string avoids backslash issues on Windows)
file_path = r"C:\Users\archi\Data Visualisations\Plant Capacity Factor\Plant Capacity Factor.csv"

# Load the dataset
df = pd.read_csv(file_path)

# Melt the dataframe for easier heatmap plotting
df_melted = df.melt(id_vars=["City", "Province"], var_name="Year_Scenario", value_name="CapacityFactor")

# Create a pivot table for heatmap: Cities vs Year_Scenario
pivot_table = df_melted.pivot(index="City", columns="Year_Scenario", values="CapacityFactor")

# --- Reorder columns so YCurrent comes first ---
def sort_key(x):
    year_part, scenario = x.split('_')
    if year_part == "YCurrent":
        return (0, scenario)  # Put YCurrent first
    else:
        return (int(year_part[1:]), scenario)

ordered_columns = sorted(pivot_table.columns, key=sort_key)
pivot_table = pivot_table[ordered_columns]

# --- Append province names in brackets for clarity (robust mapping) ---
city_to_prov = df.drop_duplicates(subset=["City"]).set_index("City")["Province"].to_dict()
pivot_table.index = [f"{city} ({city_to_prov.get(city, '')})" for city in pivot_table.index]

# --- Define custom traffic-light colormap (0–90 green, 90–98 yellow, 98–100 red) ---
cmap = mcolors.ListedColormap(["green", "yellow", "red"])
bounds = [0, 90, 98, 100]
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Plot heatmap
plt.figure(figsize=(16, 10))
ax = sns.heatmap(
    pivot_table,
    cmap=cmap,
    norm=norm,
    cbar_kws={'label': 'Capacity Factor (%)', 'ticks': [0, 90, 98, 100]},
    annot=False
)

# Rotate Year_Scenario labels on x-axis by 45 degrees
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

plt.title("Plant Capacity Factor Across Cities, Years, and Scenarios", fontsize=16, pad=20)
plt.xlabel("Year & Scenario")
plt.ylabel("City (Province)")
plt.tight_layout()
plt.show()
