import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# === USER INPUTS ===
selected_ycase = "Y2050"   # Options: YCurrent, Y2030, Y2050
selected_scase = "S1"         # Options: S1, S2, S3
# ====================

# === Load and clean data ===
df = pd.read_csv(r"C:\Users\archi\Data Visualisations\Cost Distrubution\Cost Distrubution.csv")
df.columns = df.columns.str.strip()

for col in ["City", "Province", "Ycase", "Scase"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# === Filter for selected year and scenario ===
filtered_df = df[(df['Ycase'] == selected_ycase) & (df['Scase'] == selected_scase)].copy()

# === Group definitions ===
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

# Split groups into CAPEX and OPEX for ordering + legend
capex_groups = ['Renewables', 'Hydrogen Production', 'Steelmaking', 'Caster']
opex_groups = ['Transport', 'Iron Feed', 'Scrap', 'Alloy & Additives', 'Labour & Maint.']

# === Sum into grouped columns ===
grouped_df = filtered_df.copy()
for group, cols in group_map.items():
    existing = [c for c in cols if c in grouped_df.columns]
    grouped_df[group] = grouped_df[existing].sum(axis=1) if existing else 0.0

# === Label and aggregate ===
grouped_df['City_Prov'] = grouped_df['City'] + " (" + grouped_df['Province'] + ")"
final_groups = capex_groups + opex_groups
city_grouped = grouped_df.groupby('City_Prov', as_index=True)[final_groups].mean()

# Sort cities by total cost
city_grouped['TotalCost'] = city_grouped[final_groups].sum(axis=1)
city_grouped = city_grouped.sort_values(by='TotalCost', ascending=True)

stack_plot_df = city_grouped.drop(columns=['TotalCost'])
stacked_data = stack_plot_df[final_groups].T  # maintain CAPEX first, OPEX second

# === Colors ===
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
fig, ax = plt.subplots(figsize=(14, 7))
bottom = pd.Series([0.0] * len(stacked_data.columns), index=stacked_data.columns)

# Plot in CAPEX → OPEX order
for component in stacked_data.index:
    ax.bar(
        stacked_data.columns,
        stacked_data.loc[component],
        bottom=bottom,
        label=component,
        color=group_colors.get(component, '#999999')
    )
    bottom += stacked_data.loc[component]

# === Styling ===
year_title = selected_ycase.replace("YCurrent", "Current").replace("Y", "Year ")
scenario_title = "Scenario " + selected_scase.replace("S", "")

ax.set_ylabel("Cost (Million USD/year)")
# ax.set_title(f"Grouped CAPEX + OPEX Breakdown by City ({year_title}, {scenario_title})")

x_labels = list(stacked_data.columns)
ax.set_xticks(range(len(x_labels)))
ax.set_xticklabels(x_labels, rotation=45, ha='right')

ax.grid(axis='y', linestyle='--', linewidth=0.7)

# === Custom Legend with CAPEX/OPEX separation ===
capex_handles = [Line2D([0], [0], color=group_colors[g], lw=8) for g in capex_groups]
opex_handles = [Line2D([0], [0], color=group_colors[g], lw=8) for g in opex_groups]

first_legend = ax.legend(capex_handles, capex_groups, title="CAPEX", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.add_artist(first_legend)
ax.legend(opex_handles, opex_groups, title="OPEX", bbox_to_anchor=(1.05, 0.45), loc='upper left')

plt.tight_layout()
plt.show()
