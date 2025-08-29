import pandas as pd
import matplotlib.pyplot as plt

# === Parameters ===
file_path = r"C:\Users\archi\Data Visualisations\LCOS Grid vs Island\LCOS Grid vs Island.csv"
year = "Y2050"  # Change accordingly
scenario = "S1"
grid_emissions = {"YCurrent": 500, "Y2030": 450, "Y2040": 300, "Y2050": 200}  # in gCO₂/kWh
BF_BOF_COST = 539
BF_BOF_CO2 = 2.1
ETS_price = 12.57  # USD per tCO₂

# === Load data ===
df = pd.read_csv(file_path, encoding="ISO-8859-1")

# === Define column names ===
island_col = f"{year}_{scenario}"
grid_col = f"{year}_{scenario}_Grid_Cost"
island_co2_col = f"{year}_{scenario}_CO2_per_tonne_steel"
energy_col = f"{year}_{scenario}_Energy_Per_Tonne"  # MWh/tonne

# === Prepare DataFrame ===
df_plot = df[["City", island_col, island_co2_col, grid_col, energy_col]].copy()
df_plot.columns = ["City", "Island_Cost", "Island_CO2", "Grid_Cost", "Energy_per_tonne"]

# === Compute Grid CO₂ Intensity ===
g_per_kwh = grid_emissions[year]
df_plot["Grid_CO2"] = df_plot["Energy_per_tonne"] * 1000 * g_per_kwh / 1e6  # tonnes CO₂

# === Add ETS-adjusted cost ===
df_plot["Grid_Cost_w_tax"] = df_plot["Grid_Cost"] + df_plot["Grid_CO2"] * ETS_price
df_plot["BF_BOF_Cost_w_tax"] = BF_BOF_COST + BF_BOF_CO2 * ETS_price

# === Sort by city ===
df_plot = df_plot.sort_values("City")

# === Plotting ===
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

# --- a) Cost Panel ---
ax1.scatter(df_plot["City"], df_plot["Island_Cost"], label="H2-DRI-EAF [islanded]",
            marker='o', edgecolor='black', color='deepskyblue', s=80)
ax1.scatter(df_plot["City"], df_plot["Grid_Cost"], label="H2-DRI-EAF [grid]",
            marker='o', color='navy', s=80)
ax1.scatter(df_plot["City"], [BF_BOF_COST]*len(df_plot), label="BF-BOF",
            marker='D', color='orange', s=80)

# Add ETS-adjusted versions
ax1.scatter(df_plot["City"], df_plot["Grid_Cost_w_tax"], label="H2-DRI-EAF [grid] + C tax",
            marker='s', color='lightblue', s=80)
ax1.scatter(df_plot["City"], df_plot["BF_BOF_Cost_w_tax"], label="BF-BOF + C tax",
            marker='s', color='gold', s=80)

ax1.set_ylabel("USD/t steel")
ax1.set_title(f"a) Levelised Cost of Green Steel by City ({year})")
ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
ax1.legend()

# --- b) CO₂ Panel ---
ax2.scatter(df_plot["City"], df_plot["Island_CO2"], label="H2-DRI-EAF [islanded]",
            marker='o', edgecolor='black', color='deepskyblue', s=80)
ax2.scatter(df_plot["City"], df_plot["Grid_CO2"], label="H2-DRI-EAF [grid]",
            marker='o', color='navy', s=80)
ax2.scatter(df_plot["City"], [BF_BOF_CO2]*len(df_plot), label="BF-BOF",
            marker='D', color='orange', s=80)
ax2.set_ylabel("tCO₂/t steel")
ax2.set_xlabel("City")
ax2.set_title("b) CO₂ Intensity by City")
ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
ax2.legend()

# Final layout
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
