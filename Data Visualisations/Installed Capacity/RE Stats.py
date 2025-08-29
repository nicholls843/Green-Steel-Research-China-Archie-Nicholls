import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load your CSV
csv_path = Path(r"C:\Users\archi\Data Visualisations\Installed Capacity\RE statistics.csv")
df = pd.read_csv(csv_path)

# Keep column names exactly as in CSV
columns = df.columns.tolist()

# Create figure
fig, ax = plt.subplots(figsize=(14, 5))
ax.axis("off")

# Colour scheme
header_blue = "#4F81BD"  # Darker blue for header
band_blue   = "#DCE6F1"  # Softer blue for zebra rows

# Create table
table = ax.table(
    cellText=df.values.tolist(),
    colLabels=columns,
    cellLoc="left",
    colColours=[header_blue] * len(columns),
    loc="center"
)

# Style cells
for (row, col), cell in table.get_celld().items():
    cell.set_fontsize(14)
    cell.set_height(0.09)

    if row == 0:  # header row
        cell.set_text_props(weight="bold", color="white")
    elif row % 2 == 0:  # zebra banding
        cell.set_facecolor(band_blue)

    # Bold first column (Parameter)
    if col == 0 and row != 0:
        cell.set_text_props(weight="bold")

# Adjust scaling
table.scale(1.05, 1.2)

plt.tight_layout()
plt.savefig("re_statistics_table_coloured.png", dpi=300, bbox_inches="tight")
plt.show()
