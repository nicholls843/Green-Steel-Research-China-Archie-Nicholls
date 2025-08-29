import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# === Load CSV ===
file_path = r"C:\Users\archi\Data Visualisations\LCOS exc Ore\LCOS exc ore.csv"  # Adjust path if needed
df = pd.read_csv(file_path, encoding="utf-8-sig")

# Clean headers
df.columns = df.columns.str.strip()

# Identify cost and solar share columns
cost_cols = [col for col in df.columns if "_S" in col and "_Solar" not in col]
solar_cols = [col for col in df.columns if "_Solar" in col]

# === Melt data into long format ===
long_df = pd.DataFrame()

for cost_col in cost_cols:
    year, scenario = cost_col.split("_")[0], cost_col.split("_")[1].replace("S", "")
    solar_col = f"{year}_S{scenario}_Solar"

    if solar_col not in df.columns:
        continue  # skip if solar share column is missing

    temp = df[["City", "Province", cost_col, solar_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Solar_share"]
    temp["Year"] = year.replace("Y", "") if "Y" in year else year
    temp["Scenario"] = scenario
    long_df = pd.concat([long_df, temp], ignore_index=True)

# Order cities alphabetically
long_df["City"] = pd.Categorical(long_df["City"], categories=sorted(df["City"].unique()), ordered=True)

# Marker styles
marker_map = {
    "Current": "P",
    "2030": "o",
    "2040": "s",
    "2050": "D"
}

# === Plot for each scenario ===
for scenario in ["1", "2", "3"]:
    plt.figure(figsize=(16, 8))

    # Light gray lines connecting the years per city
    for city in long_df["City"].cat.categories:
        subset_city = long_df[(long_df["Scenario"] == scenario) & (long_df["City"] == city)]
        subset_city_sorted = subset_city.sort_values(by="Year")
        plt.plot(
            subset_city_sorted["City"],
            subset_city_sorted["Cost"],
            color="gray",
            linewidth=1,
            alpha=0.3
        )

    # Plot each year as a different marker, colored by solar share
    for year, marker in marker_map.items():
        subset = long_df[(long_df["Scenario"] == scenario) & (long_df["Year"] == year)]
        sc = plt.scatter(
            x=subset["City"],
            y=subset["Cost"],
            c=subset["Solar_share"] / 100,
            cmap="RdBu_r",
            vmin=0.3,
            vmax=1.0,
            marker=marker,
            s=120,
            edgecolors="k",
            label=year
        )

    # Titles and labels
    plt.title(f"Levelised Cost of Green Steel (Excl. Ore) — Scenario {scenario}", fontsize=14)
    plt.ylabel("USD per tonne of steel", fontsize=12)
    plt.xlabel("City")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(title="Installation Year")

    # Colorbar for solar share
    cbar = plt.colorbar(sc)
    cbar.set_label("Share of solar in total VRE capacity")
    cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    plt.tight_layout()

    # Save figure
    save_path = fr"C:\Users\archi\Data Visualisations\LCOS\LCOS_Excl_Ore_Scenario_{scenario}.png"
    plt.savefig(save_path, dpi=300)
    plt.show()
    print(f"✅ Saved figure: {save_path}")
