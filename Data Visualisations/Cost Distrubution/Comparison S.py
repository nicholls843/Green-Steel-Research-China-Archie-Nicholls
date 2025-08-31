import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

# === USER INPUTS ===
selected_ycase = "YCurrent"   # Options: YCurrent, Y2030, Y2040, Y2050
normalize_to_pct = False    # True -> make each bar 100% stacked (composition only)
save_path = None            

# === Load & clean data ===
df = pd.read_csv(r"C:\Users\archi\Data Visualisations\Cost Distrubution\Cost Distrubution.csv")
df.columns = df.columns.str.strip()

for col in ["City", "Province", "Ycase", "Scase"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# Filter to selected year; keep all scenarios (S1, S2, S3)
df_year = df[df["Ycase"] == selected_ycase].copy()

# === Group definitions (split CAPEX/OPEX) ===
group_map = {
    # CAPEX
    'Renewables': ['aCAPEX_s', 'aCAPEX_w'],
    'Hydrogen Production': ['aCAPEX_ely', 'aCAPEX_cmp2b', 'aCAPEX_CGH2', 'aCAPEX_FC'],
    'Steelmaking': ['aCAPEX_DRP', 'aCAPEX_EAF'],
    'Caster': ['aCAPEX_cst'],
    # OPEX
    'Transport': ['TotalTransportCost_mUSD'],
    'Iron Feed': ['aOPEX_pel', 'aOPEX_lmp'],
    'Scrap': ['aOPEX_scr'],
    'Alloy & Additives': ['aOPEX_aly', 'aOPEX_lime', 'aOPEX_eld'],
    'Labour & Maint.': ['aOPEX_labour', 'aOPEX_maint']
}

capex_groups = ['Renewables', 'Hydrogen Production', 'Steelmaking', 'Caster']
opex_groups  = ['Transport', 'Iron Feed', 'Scrap', 'Alloy & Additives', 'Labour & Maint.']
final_groups = capex_groups + opex_groups  

# Sum source columns into grouped categories 
tmp = df_year.copy()
for group, cols in group_map.items():
    exist = [c for c in cols if c in tmp.columns]
    tmp[group] = tmp[exist].sum(axis=1) if exist else 0.0

# City label (city name only)
tmp["City_Prov"] = tmp["City"]

# Aggregate by City_Prov and Scenario (mean in case of duplicates)
agg = tmp.groupby(["City_Prov", "Scase"], as_index=False)[final_groups].mean()

# Pivot to MultiIndex columns: (Component, Scenario)
pivot = agg.pivot(index="City_Prov", columns="Scase", values=final_groups)

# Ensure all three scenarios exist 
for s in ["S1", "S2", "S3"]:
    if s not in pivot.columns.levels[1]:
        for g in final_groups:
            pivot[(g, s)] = 0.0

# Order columns consistently: components × (S1,S2,S3)
pivot = pivot.reindex(columns=pd.MultiIndex.from_product([final_groups, ["S1", "S2", "S3"]]))

# Sort cities by average total cost across scenarios (ascending)
totals_across_scen = pivot.groupby(level=1, axis=1).sum()
avg_total = totals_across_scen.mean(axis=1)
pivot = pivot.loc[avg_total.sort_values().index]

# normalize each city-scenario bar to 100% (composition view)
if normalize_to_pct:
    totals = totals_across_scen.copy()
    for s in ["S1", "S2", "S3"]:
        denom = totals[s].replace(0, np.nan)
        for g in final_groups:
            pivot[(g, s)] = pivot[(g, s)].div(denom) * 100.0
    y_label = "Share of City Total (%)"
else:
    y_label = "Cost (Million USD/year)"

cities = pivot.index.tolist()
n_cities = len(cities)

# === Colors (consistent across scenarios) ===
group_colors = {
    'Renewables': '#6baed6',
    'Hydrogen Production': '#66c2a5',
    'Steelmaking': '#2171b5',
    'Caster': '#08306b',
    'Transport': '#9ecae1',
    'Iron Feed': '#bdbdbd',
    'Scrap': '#969696',
    'Alloy & Additives': '#636363',
    'Labour & Maint.': '#238b45'
}

# === Plot ===
fig_w = max(14, 0.5 * n_cities)
fig, ax = plt.subplots(figsize=(fig_w, 8))

x = np.arange(n_cities)
bar_width = 0.22
offsets = {"S1": -bar_width, "S2": 0.0, "S3": bar_width}

# Plot each scenario as stacked bars (CAPEX first -> OPEX second)
for s in ["S1", "S2", "S3"]:
    bottom = np.zeros(n_cities, dtype=float)
    for g in final_groups:  # respects CAPEX->OPEX order
        heights = pivot[(g, s)].values.astype(float)
        ax.bar(
            x + offsets[s],
            heights,
            width=bar_width * 0.95,
            bottom=bottom,
            color=group_colors.get(g, "#999999"),
            edgecolor="black",
            linewidth=0.4
        )
        bottom += heights

# X labels
ax.set_xticks(x)
ax.set_xticklabels(cities, rotation=45, ha="right")

# Title & labels
year_title = selected_ycase.replace("YCurrent", "Current").replace("Y", "Year ")
# ax.set_title(f"Grouped CAPEX + OPEX Breakdown by City — All Scenarios ({year_title})")
ax.set_ylabel(y_label)

# === Split legends: CAPEX block + OPEX block + Scenario note (all as separate artists) ===
capex_handles = [Patch(facecolor=group_colors[g], edgecolor='black', label=g) for g in capex_groups]
opex_handles  = [Patch(facecolor=group_colors[g], edgecolor='black', label=g) for g in opex_groups]

# CAPEX legend (top)
leg_capex = ax.legend(capex_handles, capex_groups, title="CAPEX",
                      bbox_to_anchor=(1.02, 1.0), loc="upper left")
ax.add_artist(leg_capex)

# OPEX legend (middle)
leg_opex = ax.legend(opex_handles, opex_groups, title="OPEX",
                     bbox_to_anchor=(1.02, 0.62), loc="upper left")
ax.add_artist(leg_opex)

# Scenario note (bottom)
note_patch = Rectangle((0,0), 1, 1, facecolor="white", edgecolor="black", linewidth=0.8)
leg_scen = ax.legend(handles=[note_patch],
                     labels=["S1 left \u2192 S3 right"],
                     title="Scenario",
                     bbox_to_anchor=(1.02, 0.40), loc="upper left",
                     frameon=True)
ax.add_artist(leg_scen)

# Grid
ax.grid(axis='y', linestyle='--', linewidth=0.7, alpha=0.6)

plt.tight_layout()
if save_path:
    plt.savefig(save_path, dpi=300)
plt.show()
