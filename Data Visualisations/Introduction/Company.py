import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
df = pd.read_csv(r"C:\Users\archi\Data Visualisations\Introduction\Company.csv")

# Sort and take top 20
df_top20 = df.sort_values(by='Production', ascending=False).head(20)

# Updated and visually distinct color palette
custom_country_colors = {
    "China": "#d62728",         # Red
    "India": "#ff7f0e",         # Orange
    "Japan": "#1f77b4",         # Blue
    "South Korea": "#2ca02c",   # Green
    "United States": "#9467bd", # Purple
    "Germany": "#8c564b",       # Brown
    "Brazil": "#17becf",        # Teal
    "Taiwan": "#bcbd22",        # Olive
    "Turkey": "#e377c2",        # Pink
    "Russia": "#7f7f7f",        # Grey
    "Luxembourg": "#008b8b",    # Dark Cyan — distinct from Japan's blue
    "Iran": "#aec7e8",          # Light Blue
    "Argentina/Italy": "#98df8a", # Pale Green
    "Vietnam": "#ffbb78"        # Light Orange
}

# Assign colors
colors = df_top20['Country'].map(lambda c: custom_country_colors.get(c, '#000000'))

# Create the plot
plt.figure(figsize=(14, 8))
bars = plt.barh(df_top20['Company'], df_top20['Production'], color=colors)

# Formatting
plt.xlabel("Crude Steel Production (Mt)", fontsize=12)
# plt.title("Top 20 Steel Companies by Crude Steel Production\n(Colour-Coded by Country)", fontsize=14)
plt.gca().invert_yaxis()
plt.grid(axis='x', linestyle='--', alpha=0.6)

# Legend
used_countries = df_top20['Country'].unique()
legend_handles = [plt.Line2D([0], [0], color=custom_country_colors[c], lw=8) for c in used_countries]
plt.legend(legend_handles, used_countries, title="Country", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()
