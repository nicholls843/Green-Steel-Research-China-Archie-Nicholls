import pandas as pd
import matplotlib.pyplot as plt

# Load the data
df = pd.read_excel("BOF vs EAF.xlsx", sheet_name="Sheet1")

# Clean column names (remove any leading/trailing spaces)
df.columns = df.columns.str.strip()

# Calculate absolute production volumes
df['BOF_vol'] = df['Million Tonnes'] * df['BOF'] / 100
df['EAF_vol'] = df['Million Tonnes'] * df['EAF'] / 100
df['Other_vol'] = df['Million Tonnes'] * df['Other'].fillna(0) / 100

# Prepare for plotting
df_plot = df[['Area', 'BOF_vol', 'EAF_vol', 'Other_vol']]
df_plot.set_index('Area', inplace=True)
df_plot_reset = df_plot.reset_index()

# Create horizontal stacked bar chart
fig, ax = plt.subplots(figsize=(10, 4))

# Plot bars
bar1 = ax.barh(df_plot_reset['Area'], df_plot_reset['BOF_vol'], color='#4A90E2', label='BOF')
bar2 = ax.barh(df_plot_reset['Area'], df_plot_reset['EAF_vol'], left=df_plot_reset['BOF_vol'], color='#7B8B8E', label='EAF')
bar3 = ax.barh(
    df_plot_reset['Area'],
    df_plot_reset['Other_vol'],
    left=df_plot_reset['BOF_vol'] + df_plot_reset['EAF_vol'],
    color='#B0B0B0',
    label='Other'
)

# Add percentage annotations
for i, (bo_pct, ea_pct, ot_pct) in enumerate(zip(df['BOF'], df['EAF'], df['Other'].fillna(0))):
    ax.text(df_plot_reset['BOF_vol'][i] / 2, i, f'{bo_pct:.1f}%', va='center', ha='center', color='white', fontsize=16)
    ax.text(df_plot_reset['BOF_vol'][i] + df_plot_reset['EAF_vol'][i] / 2, i, f'{ea_pct:.1f}%', va='center', ha='center', color='white', fontsize=16)
    if ot_pct > 0:
        ax.text(df_plot_reset['BOF_vol'][i] + df_plot_reset['EAF_vol'][i] + df_plot_reset['Other_vol'][i] / 2, i, f'{ot_pct:.1f}%', va='center', ha='center', color='black', fontsize=15)

# Styling
ax.set_xlabel('Crude Steel Production (Mt)')
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=False)
ax.set_facecolor('#f5f5f5')
fig.patch.set_facecolor('#f5f5f5')
ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.spines[['top', 'right', 'left']].set_visible(False)
ax.tick_params(axis='y', labelsize=10)

plt.tight_layout()
plt.savefig("steel_production_2024.png", dpi=300, bbox_inches='tight')
plt.show()
