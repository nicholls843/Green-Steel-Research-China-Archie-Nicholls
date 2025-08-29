import pandas as pd
import matplotlib.pyplot as plt

# === USER INPUT: Choose province to analyse ===
selected_province = "Inner Mongolia"  # Change as needed
# ================================================

# === Load and clean data ===
df = pd.read_csv(r"C:\Users\archi\Data Visualisations\Cost Distrubution\Cost Distrubution.csv")
df.columns = df.columns.str.strip()
df['Province'] = df['Province'].str.strip()

# === Group definitions with added Transport (OPEX) ===
group_map = {
    'Renewables': ['aCAPEX_s', 'aCAPEX_w'],
    'Hydrogen Production': ['aCAPEX_ely', 'aCAPEX_cmp2b', 'aCAPEX_CGH2', 'aCAPEX_FC'],
    'Steelmaking': ['aCAPEX_DRP', 'aCAPEX_EAF'],
    'Casting': ['aCAPEX_cst'],
    'Transport': ['TotalTransportCost_mUSD'],  
    'Iron Feed': ['aOPEX_pel', 'aOPEX_lmp'],
    'Scrap': ['aOPEX_scr'],
    'Alloy & Additives': ['aOPEX_aly', 'aOPEX_lime', 'aOPEX_eld'],
    'Labour & Maint.': ['aOPEX_labour', 'aOPEX_maint']
}

# === Filter for selected province ===
province_df = df[df['Province'] == selected_province].copy()

# === Sum components into grouped columns ===
for group, cols in group_map.items():
    province_df[group] = province_df[cols].sum(axis=1)

# === Create label: Year + Scenario ===
province_df['Label'] = province_df['Ycase'] + "_" + province_df['Scase']

# === Sort labels chronologically ===
sort_order = ['YCurrent', 'Y2030', 'Y2050']
province_df['Label'] = pd.Categorical(
    province_df['Label'],
    categories=[f"{year}_{s}" for year in sort_order for s in ['S1', 'S2', 'S3']],
    ordered=True
)

# === Aggregate for plotting ===
final_groups = list(group_map.keys())
plot_data = province_df.groupby('Label')[final_groups].mean().dropna().T

# === Color palette update ===
group_colors = {
    'Renewables': '#6baed6',
    'Hydrogen Production': '#66c2a5',
    'Steelmaking': '#2171b5',
    'Casting': '#08306b',
    'Transport': '#9ecae1',            
    'Iron Feed': '#bdbdbd',
    'Scrap': '#969696',
    'Alloy & Additives': '#636363',
    'Labour & Maint.': '#238b45'
}

# === Plot ===
fig, ax = plt.subplots(figsize=(12, 6))
bottom = pd.Series([0] * len(plot_data.columns), index=plot_data.columns)

for component in plot_data.index:
    ax.bar(
        plot_data.columns,
        plot_data.loc[component],
        bottom=bottom,
        label=component,
        color=group_colors.get(component, '#999999')
    )
    bottom += plot_data.loc[component]

# === Styling ===
ax.set_ylabel("Cost (Million USD/year)")
ax.set_title(f"{selected_province}: CAPEX + OPEX Breakdown by Year and Scenario")
ax.set_xticks(range(len(plot_data.columns)))
ax.set_xticklabels(plot_data.columns, rotation=45)
ax.legend(title="Cost Category", bbox_to_anchor=(1.02, 1), loc='upper left')
ax.grid(axis='y', linestyle='--', linewidth=0.7)

plt.tight_layout()
plt.show()
