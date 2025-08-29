import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# === Config ===
scenario = "YCurrent_S1"
capex_col = f"{scenario}_CAPEX"
opex_col = f"{scenario}_OPEX"
file_path = r"C:\Users\archi\Data Visualisations\CAPEX and OPEX\CAPEX OPEX.csv"

# === Load and clean data ===
df = pd.read_csv(file_path, encoding="utf-8-sig")
df.columns = df.columns.str.strip()
df["Province"] = df["Province"].str.strip()
df["City"] = df["City"].str.strip()
df["CAPEX"] = df[capex_col]
df["OPEX"] = df[opex_col]
df["Total"] = df["CAPEX"] + df["OPEX"]

# === Sort by province and city ===
df = df.sort_values(by=["Province", "City"]).reset_index(drop=True)

# === Calculate province centers and group ends ===
province_centers = []
province_edges = []
provinces = df["Province"].unique()

for province in provinces:
    province_indices = df[df["Province"] == province].index
    start = province_indices[0]
    end = province_indices[-1]
    center = (start + end) / 2
    province_centers.append((center, province))
    province_edges.append(end)

# === Create figure ===
fig, ax = plt.subplots(figsize=(16, 9))

# === Plot bars ===
ax.bar(df.index, df["CAPEX"], label="CAPEX", color="#003f5c")
ax.bar(df.index, df["OPEX"], bottom=df["CAPEX"], label="OPEX", color="#7aafff")

# === Add % labels ===
for i in range(len(df)):
    total = df.loc[i, "Total"]
    capex = df.loc[i, "CAPEX"]
    opex = df.loc[i, "OPEX"]
    pct = 100 * capex / total
    if capex > 15:
        ax.text(i, capex / 2, f"{pct:.0f}%", ha="center", va="center", fontsize=8, color="white")
    if opex > 15:
        ax.text(i, capex + opex / 2, f"{100 - pct:.0f}%", ha="center", va="center", fontsize=8, color="black")

# === Hide default xticks ===
ax.set_xticks(df.index)
ax.set_xticklabels([])

# === Draw province labels where xticks normally go ===
for center, province in province_centers:
    ax.text(center, -0.05, province, ha='center', va='center', fontsize=11, fontweight='bold', transform=ax.get_xaxis_transform())

# === Draw city labels below provinces ===
for i, city in enumerate(df["City"]):
    ax.text(i, -0.12, city, ha='center', va='center', fontsize=8, rotation=90, transform=ax.get_xaxis_transform())

# === Vertical lines between provinces ===
for end in province_edges[:-1]:
    ax.axvline(end + 0.5, color="gray", linestyle="--", alpha=0.4)

# === Aesthetics ===
ax.set_title(f"CAPEX and OPEX per City – Scenario {scenario}", fontsize=14)
ax.set_ylabel("USD (Million per year)", fontsize=12)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.legend()
ax.grid(True, axis='y', linestyle='--', alpha=0.4)

# === Increase bottom margin to fit city names
plt.subplots_adjust(bottom=0.25)

plt.show()