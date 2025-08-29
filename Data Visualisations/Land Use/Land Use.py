import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# === Load data ===
file_path = r"C:\Users\archi\Data Visualisations\Land Use\Land Use.csv"
df = pd.read_csv(file_path, encoding="utf-8-sig")
df.columns = df.columns.str.strip()

# === Melt to long format ===
value_vars = [col for col in df.columns if "_S" in col]
long_df = df.melt(id_vars=["City", "Province"], value_vars=value_vars,
                  var_name="Year_Scenario", value_name="Land_km2")

# === Extract Year and Scenario ===
long_df["Year"] = long_df["Year_Scenario"].str.extract(r"Y(\w+)_S\d+")[0]
long_df["Scenario"] = long_df["Year_Scenario"].str.extract(r"_S(\d+)")[0]

# === Standardize Year values ===
long_df["Year"] = long_df["Year"].replace({
    "Current": "Current",  # already fine
    "2030": "2030",
    "2040": "2040",
    "2050": "2050"
})

# === Marker and color settings ===
year_markers = {
    "Current": "P",   # Plus
    "2030": "o",      # Circle
    "2040": "s",      # Square
    "2050": "D"       # Diamond
}
year_order = ["Current", "2030", "2040", "2050"]
year_palette = sns.color_palette("RdBu", n_colors=4)
year_color_map = dict(zip(year_order, year_palette))

# === Output folder ===
output_folder = r"C:\Users\archi\Data Visualisations\Land Use"
os.makedirs(output_folder, exist_ok=True)

# === Loop through scenarios ===
for scenario in ["1", "2", "3"]:
    scenario_df = long_df[long_df["Scenario"] == scenario].copy()

    # Order cities alphabetically
    city_order = sorted(scenario_df["City"].unique())
    scenario_df["City"] = pd.Categorical(scenario_df["City"], categories=city_order, ordered=True)
    scenario_df = scenario_df.sort_values("City")

    cities = scenario_df["City"].cat.categories
    x_positions = range(len(cities))

    # === Plot ===
    plt.figure(figsize=(16, 9))
    ax = plt.gca()

    # Draw vertical connectors
    for x, city in zip(x_positions, cities):
        y_vals = scenario_df[scenario_df["City"] == city].sort_values("Year")["Land_km2"].values
        if len(y_vals) > 1:
            ax.plot([x] * len(y_vals), y_vals, color='gray', alpha=0.4, zorder=1)

    # Plot points for each year
    for year in year_order:
        df_year = scenario_df[scenario_df["Year"] == year]
        x = df_year["City"].cat.codes
        y = df_year["Land_km2"]
        ax.scatter(x, y,
                   label=year,
                   s=100,
                   marker=year_markers[year],
                   edgecolor="black",
                   linewidth=0.5,
                   color=year_color_map[year],
                   zorder=2)

    # Aesthetics
    ax.set_xticks(x_positions)
    ax.set_xticklabels(cities, rotation=45, ha="right")
    ax.set_ylabel("Land Use (km²)")
    ax.set_title(f"Land Use per City by Installation Year (Scenario {scenario})")
    ax.legend(title="Installation Year")
    ax.grid(True, axis='y', linestyle="--", alpha=0.5)
    plt.tight_layout()

    # Save
    save_path = os.path.join(output_folder, f"Land_Use_Scenario_{scenario}_stripplot.png")
    plt.savefig(save_path, dpi=300)
    plt.show()