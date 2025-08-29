import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

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

# --- Marker style for different years ---
marker_map = {"Current": "P", "2030": "o", "2040": "s", "2050": "D"}

# --- CBAM thresholds setup ---
bf_bof_base = 539.00
co2_intensity = 2.1  # tCO2 per tonne steel (BF–BOF)
cbam_prices = {60: bf_bof_base + 60 * co2_intensity,
               75: bf_bof_base + 75 * co2_intensity,
               90: bf_bof_base + 90 * co2_intensity}

# Band width: ±(margin_per_tCO2 × intensity)
uniform_margin_per_tco2 = 3.0  # USD per tCO2
range_facecolor = "lightgray"
range_alpha = 0.30

# Distinct line patterns per CBAM level (keep color consistent for clarity)
cbam_linestyle = {60: "-", 75: "--", 90: "-."}

# Competitive highlight reference (rings & heatmap will use this CBAM level)
selected_cbam_price = 90  # change to 60 or 90 as needed
selected_threshold = float(cbam_prices[selected_cbam_price])

# === 1) SCATTER with shaded CBAM bands, patterned lines, and competitive rings ===
for scenario in ["1", "2", "3"]:
    fig, ax = plt.subplots(figsize=(16, 8))

    # Connectors per city across years
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

        # Competitive vs the SELECTED CBAM level (e.g., $75/tCO2)
        comp_mask = subset["Cost"] <= selected_threshold

        # main scatter (colored by Solar share)
        sc = ax.scatter(subset["City"], subset["Cost"],
                        c=subset["Solar_share"] / 100.0,
                        cmap="RdBu_r", vmin=0.3, vmax=1.0,
                        marker=marker, s=120,
                        edgecolors="k", linewidths=0.6,
                        label=year, zorder=2)

        # overlay RINGS to highlight competitive points (vs selected CBAM)
        if comp_mask.any():
            ax.scatter(subset.loc[comp_mask, "City"],
                       subset.loc[comp_mask, "Cost"],
                       facecolors='none', edgecolors='black',
                       linewidths=2.0, marker=marker, s=220, zorder=3)

    # CBAM bands + patterned central lines (+$ in legend labels)
    cbam_line_handles = []
    for price, central in cbam_prices.items():
        central = float(central)
        half_width = co2_intensity * uniform_margin_per_tco2
        low_cost, high_cost = central - half_width, central + half_width

        ax.axhspan(low_cost, high_cost, facecolor=range_facecolor, alpha=range_alpha, zorder=0)
        ls = cbam_linestyle.get(price, "--")
        ax.axhline(y=central, color="dimgray", linestyle=ls, linewidth=1.8, zorder=1)

        cbam_line_handles.append(
            mlines.Line2D([], [], color="dimgray", linestyle=ls, linewidth=1.8,
                          label=f"CBAM ${price}/tCO₂  ($ {central:,.1f})")
        )

    # Formatting
    # ax.set_title(f"Levelised Cost of Green Steel by City (Scenario {scenario})", fontsize=14)
    ax.set_ylabel("USD per tonne of steel", fontsize=12)
    ax.set_xticks(range(len(long_df["City"].cat.categories)))
    ax.set_xticklabels(long_df["City"].cat.categories, rotation=45, ha="right")
    ax.grid(True, linestyle='--', alpha=0.3)

    # Legends (split)
    leg1 = ax.legend(title="Installation Year", loc="upper left", bbox_to_anchor=(1.23, 1))
    ax.add_artist(leg1)
    band_handle = mpatches.Patch(facecolor=range_facecolor, alpha=range_alpha,
                                 label=f"CBAM range (±{uniform_margin_per_tco2:.1f}/tCO₂)")
    ax.legend(handles=[band_handle, *cbam_line_handles],
              title="CBAM reference", loc="upper left", bbox_to_anchor=(1.23, 0.66))

    # Colorbar
    if sc is not None:
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label("Share of solar in total VRE capacity (Solar + Wind)")
        cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    fig.subplots_adjust(right=0.85)
    plt.savefig(f"LCOS_Scenario_{scenario}_CBAM_scatter.png", dpi=300, bbox_inches='tight')
    plt.show()

# === 2) COMPETITIVENESS HEATMAP vs SELECTED CBAM (Δ = LCOS − threshold) ===
for scenario in ["1", "2", "3"]:
    df_s = long_df[long_df["Scenario"] == scenario].copy()
    if df_s.empty:
        continue

    df_s["CBAM_threshold"] = selected_threshold  # constant per row for selected CBAM
    df_s["Delta_vs_CBAM"] = df_s["Cost"].astype(float) - df_s["CBAM_threshold"]

    # pivot to City x Year matrix
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

    # colormap centered at zero
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

    ax.set_title(f"Competitiveness vs CBAM ${selected_cbam_price}/tCO₂ "
                 f"(Δ = LCOS − threshold) — Scenario {scenario}")
    ax.set_xlabel("Year")
    ax.set_ylabel("City")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Δ cost vs CBAM (USD/t)\n(negative = competitive)")

    # star the first competitive year per city
    for i, city in enumerate(pivot.index):
        row = pivot.loc[city]
        j = next((j for j, y in enumerate(year_order)
                  if y in row.index and pd.notna(row[y]) and row[y] <= 0), None)
        if j is not None:
            ax.scatter(j, i, marker="*", s=120, edgecolors="k",
                       facecolors="yellow", linewidths=0.6)

    ax.set_xticks(np.arange(-0.5, len(year_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_cities, 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.6)
    ax.tick_params(axis="both", which="both", length=0)

    fig.tight_layout()
    plt.savefig(f"LCOS_Scenario_{scenario}_CBAM_heatmap_{selected_cbam_price}.png", dpi=300, bbox_inches='tight')
    plt.show()