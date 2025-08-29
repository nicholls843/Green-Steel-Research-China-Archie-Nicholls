import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

# ==============================
# CONFIG
# ==============================
file_path = r"C:\Users\archi\Data Visualisations\LCOS CBAM\LCOS CBAM.csv"  # any file with your LCOS cols works
encoding = "cp1252"

# Policy toggles
selected_cbam_price = 75               # 60, 75, or 90 (USD/tCO2)
credit_domestic_ets_in_cbam = True     # True: CBAM credits CN ETS (realistic). False: add ETS + CBAM (simplified).

# Bands (uncertainty) in USD per tCO2
ets_margin_per_tco2  = 3.0
cbam_margin_per_tco2 = 3.0

# Visuals
range_facecolor = "lightgray"
range_alpha = 0.30

# ==============================
# LOAD & CLEAN
# ==============================
df = pd.read_csv(file_path, encoding=encoding)

for col in ["City", "Province"]:
    if col in df.columns:
        df[col] = (
            df[col].astype(str)
                  .str.replace("\u0092", "'", regex=False)  # stray cp1252 control
                  .str.replace("\u2019", "'", regex=False)  # curly apostrophe
                  .str.replace("\u00a0", " ", regex=False)  # NBSP
                  .str.strip()
        )

# Identify value columns
cost_cols  = [c for c in df.columns if "_S" in c and "_Solar" not in c]
solar_cols = [c for c in df.columns if "_Solar" in c]

# Coerce numeric BEFORE melting
for col in cost_cols + solar_cols:
    df[col] = (df[col].astype(str)
                      .str.replace(",", "", regex=False)
                      .str.replace("\u00a0", "", regex=False)
                      .str.strip())
    df[col] = pd.to_numeric(df[col], errors="coerce")

def normalize_year_label(yraw: str) -> str:
    y = yraw[1:] if isinstance(yraw, str) and yraw.lower().startswith("y") else yraw
    return "Current" if isinstance(y, str) and y.lower() == "current" else y

# Melt wide -> long
long_df = pd.DataFrame()
for cost_col in cost_cols:
    parts = cost_col.split("_")
    if len(parts) < 2:
        continue
    year_raw, scen_raw = parts[0], parts[1]           # e.g., "Y2030", "S2"
    scenario = scen_raw.replace("S", "")
    solar_col = f"{year_raw}_S{scenario}_Solar"
    if solar_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, solar_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Solar_share"]
    temp["Year"] = normalize_year_label(year_raw)
    temp["Scenario"] = scenario
    long_df = pd.concat([long_df, temp], ignore_index=True)

# Ensure numeric types after melt
long_df["Cost"] = pd.to_numeric(long_df["Cost"], errors="coerce")
long_df["Solar_share"] = pd.to_numeric(long_df["Solar_share"], errors="coerce")

# Orderings
year_order = ["Current", "2030", "2040", "2050"]
long_df["City"] = pd.Categorical(long_df["City"],
                                 categories=sorted(df["City"].dropna().unique()),
                                 ordered=True)
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

# Markers / linestyles by year
marker_map = {"Current": "P", "2030": "o", "2040": "s", "2050": "D"}
line_style_map = {"Current": "-", "2030": "--", "2040": "-.", "2050": ":"}

# ==============================
# THRESHOLDS
# ==============================
bf_bof_base   = 539.00
co2_intensity = 2.1  # tCO2 per t steel (BF-BOF)

# China's ETS price schedule (USD per tCO2)
ets_price_per_tco2 = {
    "Current": 8.59,
    "2030":   19.36,
    "2040":   35.06,
    "2050":   50.61,
}

# CBAM choices (USD per tCO2)
cbam_levels = [60, 75, 90]
assert selected_cbam_price in cbam_levels, "selected_cbam_price must be one of 60, 75, 90"

# Compute combined central thresholds per year (USD/t steel)
# central = BF-BOF + intensity * (ETS + CBAM_effective)
# If credit_domestic_ets_in_cbam: CBAM_effective = max(0, CBAM - ETS)  (credit domestic ETS in CBAM)
# Else: CBAM_effective = CBAM (simple additive)
combined_central = {}
combined_band_halfwidth = co2_intensity * (ets_margin_per_tco2 + (cbam_margin_per_tco2 if True else 0.0))

for year in year_order:
    ets_p = ets_price_per_tco2.get(year, np.nan)
    if np.isnan(ets_p):
        continue
    if credit_domestic_ets_in_cbam:
        cbam_effective = max(0.0, selected_cbam_price - ets_p)
    else:
        cbam_effective = float(selected_cbam_price)

    central = bf_bof_base + co2_intensity * (ets_p + cbam_effective)
    combined_central[year] = central

# ==============================
# 1) SCATTER: combined bands + lines, competitive rings vs combined
# ==============================
for scenario in ["1", "2", "3"]:
    fig, ax = plt.subplots(figsize=(16, 8))

    # thin connectors city-wise
    for city in long_df["City"].cat.categories:
        subset_city = long_df[(long_df["Scenario"] == scenario) & (long_df["City"] == city)]
        if subset_city.empty:
            continue
        subset_city = subset_city.sort_values(by="Year")
        ax.plot(subset_city["City"], subset_city["Cost"],
                color="gray", linewidth=1, alpha=0.3, zorder=1)

    sc = None
    for year, marker in marker_map.items():
        subset = long_df[(long_df["Scenario"] == scenario) & (long_df["Year"] == year)]
        if subset.empty:
            continue

        # competitive vs combined threshold for that year
        thr = combined_central.get(year, np.nan)
        comp_mask = subset["Cost"] <= thr

        sc = ax.scatter(subset["City"], subset["Cost"],
                        c=subset["Solar_share"] / 100.0,
                        cmap="RdBu_r", vmin=0.3, vmax=1.0,
                        marker=marker, s=120,
                        edgecolors="k", linewidths=0.6,
                        label=year, zorder=2)

        # overlay rings
        if comp_mask.any():
            ax.scatter(subset.loc[comp_mask, "City"],
                       subset.loc[comp_mask, "Cost"],
                       facecolors='none', edgecolors='black',
                       linewidths=2.0, marker=marker, s=220, zorder=3)

    # draw combined bands + lines per year
    line_handles = []
    for year in year_order:
        if year not in combined_central:
            continue
        central = float(combined_central[year])
        low, high = central - combined_band_halfwidth, central + combined_band_halfwidth

        # band
        ax.axhspan(low, high, facecolor=range_facecolor, alpha=range_alpha, zorder=0)
        # year-style line
        ls = line_style_map.get(year, "--")
        ax.axhline(y=central, color="dimgray", linestyle=ls, linewidth=1.8, zorder=1)

        # legend entry: show $ and indicate CBAM/ETS assumption
        addendum = "net of ETS" if credit_domestic_ets_in_cbam else "added to ETS"
        line_handles.append(
            mlines.Line2D([], [], color="dimgray", linestyle=ls, linewidth=1.8,
                          label=f"Combined {year} (CBAM ${selected_cbam_price}/tCO₂, {addendum})  ($ {central:,.1f})")
        )

    # Formatting
    ax.set_title(f"Levelised Cost of Green Steel by City — Combined ETS + CBAM (Scenario {scenario})", fontsize=14)
    ax.set_ylabel("USD per tonne of steel", fontsize=12)
    ax.set_xticks(range(len(long_df["City"].cat.categories)))
    ax.set_xticklabels(list(long_df["City"].cat.categories), rotation=45, ha="right")
    ax.grid(True, linestyle='--', alpha=0.3)

    # Legends (split)
    leg1 = ax.legend(title="Installation Year", loc="upper left", bbox_to_anchor=(1.23, 1))
    ax.add_artist(leg1)
    band_label = f"Combined band (±{ets_margin_per_tco2 + cbam_margin_per_tco2:.1f}/tCO₂)"
    band_handle = mpatches.Patch(facecolor=range_facecolor, alpha=range_alpha, label=band_label)
    ax.legend(handles=[band_handle, *line_handles],
              title="Benchmark (ETS + CBAM)", loc="upper left", bbox_to_anchor=(1.23, 0.66))

    # Colorbar
    if sc is not None:
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label("Share of solar in total VRE capacity (Solar + Wind)")
        cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    fig.subplots_adjust(right=0.85)
    suffix = f"CBAM{selected_cbam_price}_{'net' if credit_domestic_ets_in_cbam else 'add'}"
    plt.savefig(f"LCOS_Scenario_{scenario}_Combined_{suffix}_scatter.png", dpi=300, bbox_inches='tight')
    plt.show()

# ==============================
# 2) HEATMAP: Δ vs combined threshold (star = first competitive year)
# ==============================
for scenario in ["1", "2", "3"]:
    df_s = long_df[long_df["Scenario"] == scenario].copy()
    if df_s.empty:
        continue

    # map combined thresholds by year
    df_s["Combined_threshold"] = df_s["Year"].astype(str).map(combined_central).astype(float)
    df_s["Delta_vs_Combined"] = df_s["Cost"].astype(float) - df_s["Combined_threshold"]

    # pivot to City x Year
    pivot = df_s.pivot_table(index="City", columns="Year",
                             values="Delta_vs_Combined", aggfunc="mean")
    pivot = pivot.reindex(columns=year_order)

    # sort by earliest competitive year (Δ <= 0), then by 2050 delta
    earliest = []
    for city, row in pivot.iterrows():
        idx = next((i for i, y in enumerate(year_order)
                    if pd.notna(row.get(y)) and row[y] <= 0), 999)
        earliest.append((city, idx, row.get("2050", np.nan)))
    order = [c for c, _, _ in sorted(earliest,
                                     key=lambda t: (t[1], t[2] if pd.notna(t[2]) else 1e9))]
    pivot = pivot.reindex(index=order)

    # color scaling centered at zero
    vmax = np.nanpercentile(np.abs(pivot.values), 95)
    if not np.isfinite(vmax) or vmax == 0:
        vmax = 50.0
    vmin = -vmax
    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad(color="#dddddd", alpha=0.6)

    # figure size scales with number of cities
    n_cities = pivot.shape[0]
    fig_h = max(6, min(18, 0.35 * n_cities + 2))
    fig, ax = plt.subplots(figsize=(10, fig_h))

    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)

    ax.set_xticks(np.arange(len(year_order)))
    ax.set_xticklabels(year_order)
    ax.set_yticks(np.arange(n_cities))
    ax.set_yticklabels(pivot.index)

    addendum = "net of ETS" if credit_domestic_ets_in_cbam else "added to ETS"
    ax.set_title(f"Δ vs Combined ETS + CBAM (CBAM ${selected_cbam_price}/tCO₂, {addendum}) — Scenario {scenario}")
    ax.set_xlabel("Year")
    ax.set_ylabel("City")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Δ cost vs Combined benchmark (USD/t)\n(negative = competitive)")

    # star first competitive year per city
    for i, city in enumerate(pivot.index):
        row = pivot.loc[city]
        j = next((j for j, y in enumerate(year_order)
                  if y in row.index and pd.notna(row[y]) and row[y] <= 0), None)
        if j is not None:
            ax.scatter(j, i, marker="*", s=120, edgecolors="k",
                       facecolors="yellow", linewidths=0.6)

    # gridlines
    ax.set_xticks(np.arange(-0.5, len(year_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_cities, 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.6)
    ax.tick_params(axis="both", which="both", length=0)

    fig.tight_layout()
    suffix = f"CBAM{selected_cbam_price}_{'net' if credit_domestic_ets_in_cbam else 'add'}"
    plt.savefig(f"LCOS_Scenario_{scenario}_Combined_{suffix}_heatmap.png", dpi=300, bbox_inches='tight')
    plt.show()
