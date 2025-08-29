import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# --- Load LCOH CSV ---
file_path = r"C:\Users\archi\Data Visualisations\LCOH\LCOH.csv"
df = pd.read_csv(file_path, encoding="ISO-8859-1")

# Fix BOM if needed
if "City" not in df.columns:
    df.rename(columns={df.columns[0]: "City"}, inplace=True)

# --- Identify columns ---
cost_cols = [col for col in df.columns if "_S" in col and "_Ely_oversizing" not in col]
# Keep for completeness (not directly used)
oversize_cols = [col for col in df.columns if "_Ely_oversizing_factor" in col]

# --- Reshape to long format ---
long_df = pd.DataFrame()

for cost_col in cost_cols:
    year_tag, scen_tag = cost_col.split("_")[0], cost_col.split("_")[1]
    scenario = scen_tag.replace("S", "")
    oversize_col = f"{year_tag}_S{scenario}_Ely_oversizing_factor"

    if oversize_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, oversize_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Oversize"]

    # Year formatting
    year_label = year_tag.replace("Y", "") if year_tag != "YCurrent" else "Current"
    temp["Year"] = year_label
    temp["Scenario"] = scenario

    long_df = pd.concat([long_df, temp], ignore_index=True)

# Ensure numeric
long_df["Cost"] = pd.to_numeric(long_df["Cost"], errors="coerce")
long_df["Oversize"] = pd.to_numeric(long_df["Oversize"], errors="coerce")

# --- Create City label with Province in brackets ---
prov = long_df["Province"].fillna("").astype(str).str.strip()
city = long_df["City"].fillna("").astype(str).str.strip()
long_df["City_Label"] = np.where(
    (prov != "") & (prov.str.lower() != "nan"),
    city + " (" + prov + ")",
    city
)

# --- Year order for chronological connectors ---
year_order = ["Current", "2030", "2040", "2050"]
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

# --- Order cities cheapest -> most expensive (overall average across years/scenarios) ---
avg_costs = (
    long_df.groupby("City_Label")["Cost"]
    .mean()
    .sort_values(ascending=True)
    .index
)
long_df["City_Label"] = pd.Categorical(long_df["City_Label"], categories=avg_costs, ordered=True)

# Marker mapping
marker_map = {
    "Current": "P",
    "2030": "o",
    "2040": "s",
    "2050": "D",
}

# --- Plot for each scenario ---
for scenario in ["1", "2", "3"]:
    plt.figure(figsize=(16, 8))

    # Grey connectors (chronological by Year)
    for city_label in long_df["City_Label"].cat.categories:
        subset_city = long_df[(long_df["Scenario"] == scenario) & (long_df["City_Label"] == city_label)]
        subset_city_sorted = subset_city.sort_values(by="Year")
        if not subset_city_sorted.empty:
            plt.plot(
                subset_city_sorted["City_Label"],
                subset_city_sorted["Cost"],
                color="gray",
                linewidth=1,
                alpha=0.3
            )

    # Scatter points coloured by oversizing factor
    last_scatter = None
    for year, marker in marker_map.items():
        subset = long_df[(long_df["Scenario"] == scenario) & (long_df["Year"] == year)]
        if subset.empty:
            continue
        last_scatter = plt.scatter(
            x=subset["City_Label"],
            y=subset["Cost"],
            c=subset["Oversize"],
            cmap="plasma",          # vivid yellow-purple scale
            vmin=2.0, vmax=3.5,     # adjust as needed if your data range differs
            marker=marker,
            s=120,
            edgecolors="k",
            label=year
        )

    # Titles & labels
    # plt.title(f"Levelised Cost of Hydrogen by City (Scenario {scenario})", fontsize=14)
    plt.ylabel("USD per kg H₂", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Installation Year")

    # Colourbar
    if last_scatter is not None:
        cbar = plt.colorbar(last_scatter)
        cbar.set_label("Electrolyser Oversizing Factor (Capacity / Nominal Load)")
        cbar.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    # Save & show
    plt.savefig(f"LCOH_Oversize_Scenario_{scenario}.png", dpi=300)
    plt.show()
