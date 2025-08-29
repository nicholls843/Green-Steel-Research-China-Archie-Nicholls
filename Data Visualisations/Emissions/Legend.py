import matplotlib.pyplot as plt

# Define the scrap scenario colors & labels
colors = {"S1": "#4C78A8", "S2": "#F58518", "S3": "#54A24B"}
scrap_labels = {"S1": "0% scrap", "S2": "25% scrap", "S3": "50% scrap"}

# Create a standalone legend figure
fig_legend = plt.figure(figsize=(4, 1))
handles = [plt.Line2D([0], [0], color=colors[s], lw=10) for s in colors]
labels = [scrap_labels[s] for s in colors]

fig_legend.legend(handles, labels, ncols=3, frameon=False, loc="center")
fig_legend.tight_layout()

# Save separately (PNG, but you can change to PDF/SVG if needed for publications)
LEGEND_PNG = r"C:\Users\archi\Data Visualisations\Emissions\figures\Legend_ScrapScenarios.png"
fig_legend.savefig(LEGEND_PNG, dpi=220, bbox_inches="tight")
print(f"Legend saved separately: {LEGEND_PNG}")

plt.show()
