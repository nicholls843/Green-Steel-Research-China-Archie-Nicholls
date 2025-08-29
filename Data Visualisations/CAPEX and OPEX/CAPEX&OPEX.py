import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# === Choose which plot to generate ===
selected_year = "Y2050"   # e.g. "YCurrent", "Y2030", "Y2040", "Y2050"
selected_scenario = "S1"  # e.g. "S1", "S2", "S3"

file_path = r"C:\Users\archi\Data Visualisations\CAPEX and OPEX\CAPEX OPEX.csv"

# === Load and clean data ===
df = pd.read_csv(file_path, encoding="utf-8-sig")
df.columns = df.columns.str.strip()

for col in ["City", "Province"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
if "City" not in df.columns:
    raise KeyError("CSV must contain a 'City' column.")
if "Province" not in df.columns:
    raise KeyError("CSV must contain a 'Province' column to show labels as 'City (Province)'.")

# === Detect available Year–Scenario pairs ===
pattern = re.compile(r"^(Y(?:Current|20\d{2}))_(S\d)_(CAPEX|OPEX)$")
pairs = {}
for col in df.columns:
    m = pattern.match(col)
    if m:
        year, scase, kind = m.groups()
        pairs.setdefault((year, scase), {})[kind] = col

# Check that selected pair exists
if (selected_year, selected_scenario) not in pairs or \
   {"CAPEX", "OPEX"} - set(pairs[(selected_year, selected_scenario)].keys()):
    raise ValueError(f"No valid CAPEX/OPEX columns found for {selected_year}_{selected_scenario}.")

# === Extract relevant columns ===
capex_col = pairs[(selected_year, selected_scenario)]["CAPEX"]
opex_col  = pairs[(selected_year, selected_scenario)]["OPEX"]

sub = df.copy()
sub["CAPEX"] = pd.to_numeric(sub[capex_col], errors="coerce").fillna(0.0)
sub["OPEX"]  = pd.to_numeric(sub[opex_col],  errors="coerce").fillna(0.0)
sub["Total"] = sub["CAPEX"] + sub["OPEX"]

# Label: City (Province)
sub["CityLabel"] = sub["City"] + " (" + sub["Province"] + ")"

# Sort by Total ascending
sub = sub.sort_values("Total", ascending=True).reset_index(drop=True)

# === Plot ===
fig, ax = plt.subplots(figsize=(14, 7))
x = range(len(sub))
ax.bar(x, sub["CAPEX"], label="CAPEX", color="#003f5c")          # dark blue
ax.bar(x, sub["OPEX"],  bottom=sub["CAPEX"], label="OPEX", color="#7aafff")  # light blue

# Add % labels inside bars
max_total = sub["Total"].max() if len(sub) else 0
capex_thresh = 0.05 * max_total
opex_thresh  = 0.05 * max_total

for i in range(len(sub)):
    total = sub.loc[i, "Total"]
    if total <= 0:
        continue
    capex_val = sub.loc[i, "CAPEX"]
    opex_val  = sub.loc[i, "OPEX"]
    capex_pct = 100 * capex_val / total

    if capex_val > capex_thresh:
        ax.text(i, capex_val / 2, f"{capex_pct:.0f}%", ha='center', va='center',
                fontsize=8, color="white")
    if opex_val > opex_thresh:
        ax.text(i, capex_val + (opex_val / 2), f"{100 - capex_pct:.0f}%",
                ha='center', va='center', fontsize=8, color="black")

# Titles & axes
year_title = selected_year.replace("YCurrent", "Current")
scenario_title = selected_scenario.replace("S", "")
ax.set_title(f"CAPEX and OPEX per City – Year {year_title}, Scenario {scenario_title}", fontsize=14)
ax.set_ylabel("USD (Million per year)", fontsize=12)

ax.set_xticks(list(x))
ax.set_xticklabels(sub["CityLabel"], rotation=45, ha='right')

ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax.legend()
ax.grid(True, axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.show()
