import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =============================
# === FONT SIZE SETTINGS
# =============================
TITLE_FONTSIZE = 18
LABEL_FONTSIZE = 16       # x/y axis label font size
TICK_FONTSIZE = 14        # x/y tick label font size
CBAR_TITLE_FONTSIZE = 16  # colorbar (legend) title
CBAR_TICK_FONTSIZE = 13   # colorbar tick labels

# --- Read the CSV (cp1252 avoids U+0092 glyph issues) ---
file_path = r"C:\Users\archi\Data Visualisations\LCOS CBAM\LCOS CBAM.csv"
df = pd.read_csv(file_path, encoding="cp1252")

# --- Clean text columns (quotes, NBSP, stray whitespace) ---
for col in ["City", "Province"]:
    if col in df.columns:
        df[col] = (
            df[col].astype(str)
                  .str.replace("\u0092", "'", regex=False)  # bad control char
                  .str.replace("\u2019", "'", regex=False)  # curly apostrophe
                  .str.replace("\u00a0", " ", regex=False)  # non-breaking space
                  .str.strip()
        )

# --- Identify cost and solar share columns ---
cost_cols  = [c for c in df.columns if "_S" in c and "_Solar" not in c]
solar_cols = [c for c in df.columns if "_Solar" in c]

# Coerce numeric for all value columns BEFORE melting
for col in cost_cols + solar_cols:
    df[col] = (
        df[col].astype(str)
               .str.replace(",", "", regex=False)
               .str.replace("\u00a0", "", regex=False)
               .str.strip()
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Helper: normalize year labels ("Ycurrent" -> "Current", "Y2030" -> "2030") ---
def normalize_year_label(yraw: str) -> str:
    y = yraw[1:] if isinstance(yraw, str) and yraw.lower().startswith("y") else yraw
    return "Current" if isinstance(y, str) and y.lower() == "current" else y

# --- Melt wide -> long ---
long_df = pd.DataFrame()
for cost_col in cost_cols:
    parts = cost_col.split("_")
    if len(parts) < 2:
        continue
    year_raw, scen_raw = parts[0], parts[1]  # e.g., "Y2030", "S2"
    scenario = scen_raw.replace("S", "")
    solar_col = f"{year_raw}_S{scenario}_Solar"
    if solar_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, solar_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Solar_share"]
    temp["Year"] = normalize_year_label(year_raw)  # => "Current" or "2030"
    temp["Scenario"] = scenario
    long_df = pd.concat([long_df, temp], ignore_index=True)

# Ensure numeric types after melt
long_df["Cost"] = pd.to_numeric(long_df["Cost"], errors="coerce")
long_df["Solar_share"] = pd.to_numeric(long_df["Solar_share"], errors="coerce")

# --- Order City alphabetically and Year logically ---
long_df["City"] = pd.Categorical(
    long_df["City"],
    categories=sorted(df["City"].dropna().unique()),
    ordered=True
)
year_order = ["Current", "2030", "2040", "2050"]
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

# =============================
# === CBAM thresholds setup
# =============================
bf_bof_base = 539.00
co2_intensity = 2.1  # tCO2 per tonne steel (BF–BOF)
cbam_prices = {
    60: bf_bof_base + 60 * co2_intensity,
    75: bf_bof_base + 75 * co2_intensity,
    90: bf_bof_base + 90 * co2_intensity,
}

# Pick a CBAM level for section 2A (by scenario)
selected_cbam_price = 90  # change to 60 or 75 or 90 as needed
selected_threshold = float(cbam_prices[selected_cbam_price])

# =============================
# === Helper to draw a heatmap panel with big fonts
# =============================
def draw_heatmap(ax, pivot, year_order, vmin, vmax, title, show_ylabel):
    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad(color="#dddddd", alpha=0.6)

    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)

    ax.set_xticks(np.arange(len(year_order)))
    ax.set_xticklabels(year_order, fontsize=TICK_FONTSIZE)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=TICK_FONTSIZE)

    ax.set_title(title, fontsize=TITLE_FONTSIZE)
    ax.set_xlabel("Year", fontsize=LABEL_FONTSIZE)
    ax.set_ylabel("City" if show_ylabel else "", fontsize=LABEL_FONTSIZE)

    # grid lines for readability
    ax.set_xticks(np.arange(-0.5, len(year_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(pivot.index), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.6)
    ax.tick_params(axis="both", which="both", length=0)

    # star the first competitive year per city (Δ <= 0)
    for i, city in enumerate(pivot.index):
        row = pivot.loc[city]
        j = next((j for j, y in enumerate(year_order)
                  if y in row.index and pd.notna(row[y]) and row[y] <= 0), None)
        if j is not None:
            ax.scatter(j, i, marker="*", s=140, edgecolors="k",
                       facecolors="yellow", linewidths=0.7)
    return im

# =============================
# === 2A) HEATMAPS SIDE-BY-SIDE BY SCENARIO (S1 → S3) at selected CBAM
# =============================
scenarios = ["1", "2", "3"]  # arrange any order you want here

fig, axes = plt.subplots(
    nrows=1, ncols=len(scenarios),
    figsize=(6 * len(scenarios), 0.35 * len(long_df["City"].cat.categories) + 8),
    constrained_layout=True
)
if len(scenarios) == 1:
    axes = [axes]

# Compute a consistent vmin/vmax across ALL scenarios for fair comparison
all_deltas = []
for scenario in scenarios:
    df_s = long_df[long_df["Scenario"] == scenario].copy()
    if df_s.empty:
        continue
    all_deltas.append(df_s["Cost"].astype(float) - selected_threshold)
if len(all_deltas) == 0:
    all_deltas = [pd.Series([0.0])]
all_deltas = pd.concat(all_deltas, ignore_index=True)
vmax = np.nanpercentile(np.abs(all_deltas.values), 95)
if not np.isfinite(vmax) or vmax == 0:
    vmax = 50.0
vmin = -vmax

last_im = None
for ax, scenario in zip(axes, scenarios):
    df_s = long_df[long_df["Scenario"] == scenario].copy()
    if df_s.empty:
        ax.set_axis_off()
        continue

    df_s["CBAM_threshold"] = selected_threshold
    df_s["Delta_vs_CBAM"] = df_s["Cost"].astype(float) - df_s["CBAM_threshold"]

    pivot = df_s.pivot_table(index="City", columns="Year",
                             values="Delta_vs_CBAM", aggfunc="mean")
    pivot = pivot.reindex(columns=year_order)

    # sort cities by earliest competitive year (Δ <= 0), then by 2050 delta
    earliest_idx = []
    for city, row in pivot.iterrows():
        idx = next((i for i, y in enumerate(year_order)
                    if pd.notna(row.get(y)) and row[y] <= 0), 999)
        earliest_idx.append((city, idx, row.get("2050", np.nan)))
    order = [c for c, _, _ in sorted(earliest_idx,
                                     key=lambda t: (t[1], t[2] if pd.notna(t[2]) else 1e9))]
    pivot = pivot.reindex(index=order)

    last_im = draw_heatmap(
        ax=ax,
        pivot=pivot,
        year_order=year_order,
        vmin=vmin, vmax=vmax,
        title=f"Scenario {scenario}",
        show_ylabel=(scenario == scenarios[0])
    )

# Shared colorbar (legend) with larger fonts
if last_im is not None:
    cbar = fig.colorbar(last_im, ax=axes, orientation="vertical", fraction=0.02, pad=0.02)
    cbar.set_label("Δ cost vs CBAM (USD/t)\n(negative = competitive)", fontsize=CBAR_TITLE_FONTSIZE)
    cbar.ax.tick_params(labelsize=CBAR_TICK_FONTSIZE)

plt.suptitle(
    f"Competitiveness vs CBAM ${selected_cbam_price}/tCO₂ (Δ = LCOS − threshold) — by Scenario",
    fontsize=TITLE_FONTSIZE + 2, y=1.02
)
plt.savefig(f"LCOS_CBAM_heatmaps_side_by_side_byScenario_{selected_cbam_price}.png",
            dpi=300, bbox_inches="tight")
plt.show()

# =============================
# === 2B) HEATMAPS SIDE-BY-SIDE BY CBAM TAX (60 → 75 → 90) for a chosen SCENARIO
# =============================
chosen_scenario = "2"                 # change to "2" or "3" as needed
cbam_levels_ordered = [60, 75, 90]    # lowest → highest (left to right)

fig, axes = plt.subplots(
    nrows=1, ncols=len(cbam_levels_ordered),
    figsize=(6 * len(cbam_levels_ordered), 0.35 * len(long_df["City"].cat.categories) + 8),
    constrained_layout=True
)
if len(cbam_levels_ordered) == 1:
    axes = [axes]

df_cs = long_df[long_df["Scenario"] == chosen_scenario].copy()
if df_cs.empty:
    for ax in axes:
        ax.set_axis_off()
else:
    # Consistent vmin/vmax across CBAM levels for this scenario
    all_deltas_cbam = []
    for cb in cbam_levels_ordered:
        threshold = float(cbam_prices[cb])
        all_deltas_cbam.append(df_cs["Cost"].astype(float) - threshold)
    all_deltas_cbam = pd.concat(all_deltas_cbam, ignore_index=True)
    vmax_cb = np.nanpercentile(np.abs(all_deltas_cbam.values), 95)
    if not np.isfinite(vmax_cb) or vmax_cb == 0:
        vmax_cb = 50.0
    vmin_cb = -vmax_cb

    last_im2 = None
    for ax, cb in zip(axes, cbam_levels_ordered):
        threshold = float(cbam_prices[cb])
        df_s = df_cs.copy()
        df_s["CBAM_threshold"] = threshold
        df_s["Delta_vs_CBAM"] = df_s["Cost"].astype(float) - df_s["CBAM_threshold"]

        pivot = df_s.pivot_table(index="City", columns="Year",
                                 values="Delta_vs_CBAM", aggfunc="mean")
        pivot = pivot.reindex(columns=year_order)

        # same sort rule as above
        earliest_idx = []
        for city, row in pivot.iterrows():
            idx = next((i for i, y in enumerate(year_order)
                        if pd.notna(row.get(y)) and row[y] <= 0), 999)
            earliest_idx.append((city, idx, row.get("2050", np.nan)))
        order = [c for c, _, _ in sorted(earliest_idx,
                                         key=lambda t: (t[1], t[2] if pd.notna(t[2]) else 1e9))]
        pivot = pivot.reindex(index=order)

        last_im2 = draw_heatmap(
            ax=ax,
            pivot=pivot,
            year_order=year_order,
            vmin=vmin_cb, vmax=vmax_cb,
            title=f"CBAM ${cb}/tCO₂",
            show_ylabel=(cb == cbam_levels_ordered[0])
        )

    # Shared colorbar (legend) with larger fonts
    if last_im2 is not None:
        cbar2 = fig.colorbar(last_im2, ax=axes, orientation="vertical", fraction=0.02, pad=0.02)
        cbar2.set_label("Δ cost vs CBAM (USD/t)\n(negative = competitive)", fontsize=CBAR_TITLE_FONTSIZE)
        cbar2.ax.tick_params(labelsize=CBAR_TICK_FONTSIZE)

plt.savefig(f"LCOS_CBAM_heatmaps_side_by_side_byCBAM_S{chosen_scenario}.png",
            dpi=300, bbox_inches="tight")
plt.show()
