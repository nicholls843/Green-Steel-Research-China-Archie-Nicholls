import pandas as pd
import matplotlib.pyplot as plt

# Load your data
df_exports = pd.read_csv(r"C:\Users\archi\Data Visualisations\Introduction\China_Export_Destinations.csv")

# Ensure the export values are numeric
df_exports['Exports from China (Mt)'] = pd.to_numeric(df_exports['Exports from China (Mt)'], errors='coerce')

# Sort the data for better visual effect
df_exports_sorted = df_exports.sort_values(by='Exports from China (Mt)', ascending=True)

# Plot setup
plt.figure(figsize=(10, 6))
bars = plt.barh(
    df_exports_sorted['Destination'],
    df_exports_sorted['Exports from China (Mt)'],
    color='#4A90E2',       # Match blue color from reference
    edgecolor='black'      # Add black edges for clarity
)

# Add export volume labels to the end of each bar
for bar in bars:
    width = bar.get_width()
    if pd.notna(width):
        plt.text(
            width + 0.3,                         # Slightly offset right
            bar.get_y() + bar.get_height() / 2,  # Vertically centered
            f'{width:.1f}',                      # One decimal place
            va='center',
            fontsize=10,
            fontweight='bold'
        )

# Axis labels and title formatting
plt.xlabel("Exports from China (Million Tonnes)", fontsize=12, fontweight='bold')
# plt.title("Destination of Chinese Steel Exports", fontsize=14, fontweight='bold')

# Axis tick styling
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

# Grid and layout
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()

# Display the chart
plt.show()
