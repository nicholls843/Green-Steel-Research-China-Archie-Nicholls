import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load your CSV
file_path = r"C:\Users\archi\Data Visualisations\Hydropower\Installed capacity Hydro.csv"
df = pd.read_csv(file_path)

# Constants
capacity_factor = 0.46
hours_year = 8760

# Calculate required installed capacity (MW)
gen_cols = [col for col in df.columns if "Generation" in col]
for col in gen_cols:
    new_col = col.replace("Total_VRE_Generation", "Hydro_Installed_Capacity")
    df[new_col] = df[col] / (hours_year * capacity_factor)

df_out = df[["City", "Province"] + [c for c in df.columns if "Hydro_Installed_Capacity" in c]]

# ---- Choose scenario ----
scenario = "S1"   # change to "S2" or "S3"

# Filter relevant columns for that scenario
scenario_cols = [c for c in df_out.columns if scenario in c]

# Reshape for heatmap
df_heat = df_out.melt(
    id_vars=["City", "Province"], 
    value_vars=scenario_cols,
    var_name="Year", 
    value_name="Hydro Capacity (MW)"
)

# Clean year labels
df_heat["Year"] = df_heat["Year"].str.extract(r"(Y\d+|YCurrent)")

# Put Province in brackets after City
df_heat["City"] = df_heat["City"] + " (" + df_heat["Province"] + ")"

# Pivot for heatmap
heat_data = df_heat.pivot(index="City", columns="Year", values="Hydro Capacity (MW)")

# Reorder columns
ordered_cols = ["YCurrent", "Y2030", "Y2040", "Y2050"]
heat_data = heat_data[ordered_cols]

# ---- Rank cities by YCurrent ----
heat_data = heat_data.sort_values(by="YCurrent", ascending=True)

# Plot heatmap
plt.figure(figsize=(12, 14))
sns.heatmap(heat_data, cmap="Blues", annot=False, cbar_kws={'label': 'MW Required'})
plt.title(f"Hydropower Installed Capacity Required (Scenario {scenario})", fontsize=14)
plt.ylabel("City (Province)")
plt.xlabel("Year")
plt.tight_layout()
plt.show()