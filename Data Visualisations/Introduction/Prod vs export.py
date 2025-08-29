import pandas as pd
import matplotlib.pyplot as plt

# Load the data
df = pd.read_csv("C:/Users/archi/Data Visualisations/Introduction/Production vs Export.csv")

# Calculate export percentage
df['Export %'] = df['Exports'] / df['Production'] * 100

# Create the plot
fig, ax = plt.subplots(figsize=(10, 5))

# Plot total production bars
bars_prod = ax.bar(df['Year'], df['Production'], color='#4A90E2', label='Production')

# Overlay export volumes
bars_exp = ax.bar(df['Year'], df['Exports'], color='#7B8B8E', label='Exports')

# Annotate production total on top
for i, (year, prod) in enumerate(zip(df['Year'], df['Production'])):
    ax.text(year, prod + 5, f'{prod:.0f}', ha='center', va='bottom', fontsize=13, fontweight='bold', color='black')

# Annotate export percentage above the grey bar
for i, (year, exp, pct) in enumerate(zip(df['Year'], df['Exports'], df['Export %'])):
    ax.text(year, exp + 5, f'{pct:.1f}%', ha='center', va='bottom', fontsize=13, fontweight='bold', color='black')

# Styling
ax.set_ylabel('Million Tonnes')
# ax.set_title('China Steel Production and Export Share by Year', fontsize=16, weight='bold')
ax.legend()
ax.set_facecolor('#f5f5f5')
fig.patch.set_facecolor('#f5f5f5')
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.set_xticks(df['Year'])

plt.tight_layout()
plt.savefig("production_export_chart.png", dpi=300, bbox_inches='tight')  # Optional: save the figure
plt.show()
