import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from collections import Counter

# --- Load LCOS CSV ---
file_path = r"C:\Users\archi\Data Visualisations\LCOS\LCOS.csv"
df = pd.read_csv(file_path, encoding="ISO-8859-1")

# --- Identify columns ---
cost_cols = [c for c in df.columns if "_S" in c and "_CAPEX_share" not in c]
capex_cols = [c for c in df.columns if "_CAPEX_share" in c]

# --- Reshape into long format ---
long_df = pd.DataFrame()
for cost_col in cost_cols:
    year_tag, scen_tag = cost_col.split("_")[0], cost_col.split("_")[1]
    scenario = scen_tag.replace("S", "")
    capex_col = f"{year_tag}_S{scenario}_CAPEX_share_pct"
    if capex_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, capex_col]].copy()
    temp.columns = ["City", "Province", "Cost", "CAPEX_share"]
    year_label = "Current" if year_tag == "YCurrent" else year_tag.replace("Y", "")
    temp["Year"] = year_label
    temp["Scenario"] = scenario
    long_df = pd.concat([long_df, temp], ignore_index=True)

# --- Create province labels with cities in brackets ---
prov_label_map = (
    long_df.groupby("Province")["City"]
    .apply(lambda x: ", ".join(sorted(x.unique())))
    .to_dict()
)
prov_label_map = {p: f"{p} ({cities})" for p, cities in prov_label_map.items()}

# --- Aggregate to province level (average of cities) ---
prov_agg = (
    long_df.groupby(["Province", "Year", "Scenario"], as_index=False)
    .agg({"Cost": "mean", "CAPEX_share": "mean"})
)
prov_agg["Province_Label"] = prov_agg["Province"].map(prov_label_map)

# --- Order provinces alphabetically ---
province_order = sorted(prov_label_map.keys())  # Alphabetical by province name
ordered_labels = [prov_label_map[p] for p in province_order]
# Remove duplicates while keeping order
ordered_labels = list(dict.fromkeys(ordered_labels))

prov_agg["Province_Label"] = pd.Categorical(
    prov_agg["Province_Label"], categories=ordered_labels, ordered=True
)
# Remove duplicates while keeping order
ordered_labels = list(dict.fromkeys(ordered_labels))

# Debug duplicates if any
dups = [k for k, v in Counter(ordered_labels).items() if v > 1]
if dups:
    print("Duplicate categories removed:", dups)

prov_agg["Province_Label"] = pd.Categorical(
    prov_agg["Province_Label"], categories=ordered_labels, ordered=True
)

# --- Marker shapes ---
marker_map = {"Current": "P", "2030": "o", "2040": "s", "2050": "D"}

# --- Plot per scenario ---
for scenario in ["1", "2", "3"]:
    fig, ax = plt.subplots(figsize=(20, 9))

    # Connectors per province
    for label in prov_agg["Province_Label"].cat.categories:
        subset_prov = prov_agg[(prov_agg["Scenario"] == scenario) &
                               (prov_agg["Province_Label"] == label)]
        subset_prov_sorted = subset_prov.sort_values(by="Year")
        if not subset_prov_sorted.empty:
            ax.plot(
                subset_prov_sorted["Province_Label"],
                subset_prov_sorted["Cost"],
                color="gray", linewidth=1, alpha=0.3, zorder=1
            )

    # Scatter points
    last_scatter = None
    for year, marker in marker_map.items():
        subset = prov_agg[(prov_agg["Scenario"] == scenario) & (prov_agg["Year"] == year)]
        if subset.empty:
            continue
        last_scatter = ax.scatter(
            x=subset["Province_Label"],
            y=subset["Cost"],
            c=subset["CAPEX_share"] / 100.0,
            cmap="PRGn", vmin=0.0, vmax=1.0,
            marker=marker, s=120,
            edgecolors="k", linewidths=0.6,
            label=year, zorder=2
        )

    ax.set_title(f"Average Levelised Cost of Green Steel by Province (Cities in Brackets) — Scenario {scenario}",
                 fontsize=14)
    ax.set_ylabel("USD per tonne of steel", fontsize=12)
    plt.xticks(rotation=40, ha="right", fontsize=9)
    ax.legend(title="Installation Year")

    # Colourbar
    if last_scatter is not None:
        cbar = plt.colorbar(last_scatter, ax=ax)
        cbar.set_label("Cost Structure (% CAPEX vs OPEX)")
        cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
        cbar.set_ticklabels([
            "0% CAPEX\n(100% OPEX)",
            "25% CAPEX",
            "50% CAPEX",
            "75% CAPEX",
            "100% CAPEX\n(0% OPEX)"
        ])

    ax.grid(True, linestyle="--", alpha=0.25)
    plt.subplots_adjust(bottom=0.25)
    plt.tight_layout()
    plt.savefig(f"LCOS_CAPEXshare_ProvinceAvg_Scenario_{scenario}.png", dpi=300)
    plt.show()
