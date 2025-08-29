import matplotlib.pyplot as plt
import pandas as pd

# Table data with wrapped long cell text
data = {
    "Route": ["BF–BOF", "DRI–EAF", "Scrap–EAF"],
    "Input": ["Iron ore, limestone, coke", "Iron ore + NG/H₂", "Recycled scrap steel"],
    "Process Steps": ["BF → BOF", "Direct reduction → EAF", "EAF only"],
    "Energy Source": [
        "Coke\n(coal-based fossil fuel)",  # <-- wrapped here
        "NG / H₂ + electricity",
        "Electricity"
    ],
    "Main Output": ["Crude Steel", "Crude Steel", "Crude Steel"],
    "Global Average CO₂ Intensity (2023)": ["2.32 tCO₂ / tonne", "1.43 tCO₂ / tonne", "0.70 tCO₂ / tonne"]
}

# Create DataFrame
df = pd.DataFrame(data)

# Manually wrap long column name
col_labels = [
    "Route",
    "Input",
    "Process Steps",
    "Energy Source",
    "Main Output",
    "Global Average\nCO₂ Intensity (2023)"
]

# Create figure and axis
fig, ax = plt.subplots(figsize=(13, 3))  # wider layout to avoid squeezing
ax.axis('off')

# Create the table
table = ax.table(
    cellText=df.values,
    colLabels=col_labels,
    cellLoc='center',
    loc='upper center',
    colColours=['#cdeafa'] * len(col_labels)
)

# Style settings
table.auto_set_font_size(False)
table.set_fontsize(13)       # larger font
table.scale(1, 2.2)          # taller rows

# Bold header row
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight='bold')

plt.tight_layout()
plt.show()