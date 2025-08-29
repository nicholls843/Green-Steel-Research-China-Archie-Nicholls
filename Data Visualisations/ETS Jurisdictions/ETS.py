# Carbon trading prices by ETS jurisdiction (April 2025)
import os
import pandas as pd
import matplotlib.pyplot as plt
import re

# --- Paths ---
path_candidates = [
    r"C:\Users\archi\Data Visualisations\ETS Jurisdictions\ETS.csv",  
    "/mnt/data/ETS.csv",                                              
]

csv_path = next((p for p in path_candidates if os.path.exists(p)), None)
if csv_path is None:
    raise FileNotFoundError("ETS.csv not found. Update 'path_candidates' with the correct location.")

# --- Load data ---
df = pd.read_csv(csv_path)

# Helper to find likely columns
def find_col(cols, patterns):
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rx.search(c):
                return c
    return None

# Try to detect the jurisdiction and price columns
juris_col = find_col(df.columns, [r"jurisdiction", r"region", r"country", r"market", r"scheme", r"ets.*name"])
price_col = find_col(df.columns, [r"price", r"usd.*t", r"\btco2", r"us\$"])

# Sensible fallbacks
if juris_col is None:
    juris_col = df.columns[0]
if price_col is None:
    num_cols = [c for c in df.columns if c != juris_col and pd.api.types.is_numeric_dtype(df[c])]
    price_col = num_cols[0] if num_cols else df.columns[1]

# Clean & prep
df_plot = df[[juris_col, price_col]].copy()
df_plot.columns = ["Jurisdiction", "Price_USD_tCO2e"]
df_plot["Price_USD_tCO2e"] = pd.to_numeric(df_plot["Price_USD_tCO2e"], errors="coerce")
df_plot = df_plot.dropna(subset=["Price_USD_tCO2e"])

# Sort (ascending for horizontal bars so highest ends up on top visually after plotting)
df_plot = df_plot.sort_values("Price_USD_tCO2e", ascending=True)

# --- Plot ---
plt.figure(figsize=(10, max(4, 0.35 * len(df_plot))))

# Assign colors: red for China, blue for others
colors = ["red" if "china" in j.lower() else "steelblue" for j in df_plot["Jurisdiction"]]

bars = plt.barh(df_plot["Jurisdiction"], df_plot["Price_USD_tCO2e"], color=colors)

# Annotate bars with values
for i, (j, v) in enumerate(zip(df_plot["Jurisdiction"], df_plot["Price_USD_tCO2e"])):
    plt.text(v, i, f"{v:,.2f}", va="center", ha="left", fontsize=9)

plt.xlabel("Price (USD per tCO₂e)")
# plt.title("Carbon Trading Prices in Prominent ETS Jurisdictions - April 2025")
plt.tight_layout()

# Save figure
out_path = "ETS_prices_apr2025.png"   # change to your preferred folder
plt.savefig(out_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"Saved chart to: {os.path.abspath(out_path)}")
