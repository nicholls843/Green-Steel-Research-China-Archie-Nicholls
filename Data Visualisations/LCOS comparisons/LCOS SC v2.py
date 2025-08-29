import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

# ----------------------------
# Config / thresholds
# ----------------------------
file_path = r"C:\Users\archi\Data Visualisations\LCOS Comparisons\LCOS Comparisons.csv"

# BF–BOF reference band and "beats average" threshold
BFBOF_LOW  = 500.0
BFBOF_HIGH = 600.0
BFBOF_AVG  = 539.0

# ----------------------------
# Load & tidy
# ----------------------------
df = pd.read_csv(file_path, encoding="ISO-8859-1")

for col in ["City", "Province"]:
    if col in df.columns:
        df[col] = (
            df[col].astype(str)
                  .str.replace("\u0092", "'", regex=False)
                  .str.replace("\u2019", "'", regex=False)
                  .str.replace("\u00a0", " ", regex=False)
                  .str.strip()
        )

# Identify value columns
cost_cols  = [c for c in df.columns if "_S" in c and "_Solar" not in c]
solar_cols = [c for c in df.columns if "_Solar" in c]

# Coerce numerics
for col in cost_cols + solar_cols:
    df[col] = (
        df[col].astype(str)
               .str.replace(",", "", regex=False)
               .str.replace("\u00a0", "", regex=False)
               .str.strip()
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

def normalize_year_label(yraw: str) -> str:
    if not isinstance(yraw, str):
        return yraw
    y = yraw[1:] if yraw.lower().startswith("y") else yraw
    return "Current" if y.lower() == "current" else y

# Wide -> long
long_df = pd.DataFrame()
for cost_col in cost_cols:
    parts = cost_col.split("_")
    if len(parts) < 2:
        continue
    year_raw, scen_raw = parts[0], parts[1]  # e.g. "Y2030", "S2"
    scenario = scen_raw.replace("S", "")
    solar_col = f"{year_raw}_S{scenario}_Solar"
    if solar_col not in df.columns:
        continue

    temp = df[["City", "Province", cost_col, solar_col]].copy()
    temp.columns = ["City", "Province", "Cost", "Solar_share"]
    temp["Year"] = normalize_year_label(year_raw)
    temp["Scenario"] = scenario
    long_df = pd.concat([long_df, temp], ignore_index=True)

# Types & ordering
long_df["Cost"] = pd.to_numeric(long_df["Cost"], errors="coerce")
long_df["Solar_share"] = pd.to_numeric(long_df["Solar_share"], errors="coerce")

year_order = ["Current", "2030", "2040", "2050"]
long_df["City"] = pd.Categorical(
    long_df["City"],
    categories=sorted(long_df["City"].dropna().unique()),
    ordered=True
)
long_df["Year"] = pd.Categorical(long_df["Year"], categories=year_order, ordered=True)

marker_map = {"Current": "P", "2030": "o", "2040": "s", "2050": "D"}

# ----------------------------
# 1) Scatter with two-tier rings
# ----------------------------
for scenario in ["1", "2", "3"]:
    fig, ax = plt.subplots(figsize=(16, 8))

    # Background BF-BOF band & average line
    ax.axhspan(BFBOF_LOW, BFBOF_HIGH, facecolor='lightgray', alpha=0.28, zorder=0)
    ax.axhline(y=BFBOF_AVG, color='dimgray', linestyle='--', linewidth=1.8, zorder=1)
    ax.annotate(f"Avg = ${BFBOF_AVG:,.0f}",
                xy=(0.995, BFBOF_AVG),
                xycoords=("axes fraction", "data"),
                xytext=(-6, 4),
                textcoords="offset points",
                ha="right", va="bottom", fontsize=9)

    # Thin grey connectors per city across years
    for city in long_df["City"].cat.categories:
        subset_city = long_df[(long_df["Scenario"] == scenario) & (long_df["City"] == city)]
        if subset_city.empty:
            continue
        subset_city = subset_city.sort_values(by="Year")
        ax.plot(subset_city["City"], subset_city["Cost"],
                color="gray", linewidth=1, alpha=0.3, zorder=1)

    # Scatter by year, color = solar share
    sc = None
    for year, marker in marker_map.items():
        subset = long_df[(long_df["Scenario"] == scenario) & (long_df["Year"] == year)]
        if subset.empty:
            continue

        sc = ax.scatter(
            x=subset["City"],
            y=subset["Cost"],
            c=subset["Solar_share"] / 100.0,
            cmap="RdBu_r", vmin=0.3, vmax=1.0,
            marker=marker, s=120,
            edgecolors="k", linewidths=0.6,
            label=year, zorder=2
        )

        # Two-tier competitiveness overlays
        in_range_mask  = (subset["Cost"] >= BFBOF_LOW) & (subset["Cost"] <= BFBOF_HIGH)
        beats_avg_mask = subset["Cost"] <= BFBOF_AVG
        in_range_only  = in_range_mask & (~beats_avg_mask)

        # Thin ring = within band but above avg
        if in_range_only.any():
            ax.scatter(subset.loc[in_range_only, "City"],
                       subset.loc[in_range_only, "Cost"],
                       facecolors='none', edgecolors='black',
                       linewidths=1.4, marker=marker, s=200, zorder=3)

        # Thick ring = beats avg
        if beats_avg_mask.any():
            ax.scatter(subset.loc[beats_avg_mask, "City"],
                       subset.loc[beats_avg_mask, "Cost"],
                       facecolors='none', edgecolors='black',
                       linewidths=2.6, marker=marker, s=240, zorder=4)

    # Formatting
    # ax.set_title(f"Levelised Cost of Green Steel by City (Scenario {scenario})", fontsize=14)
    ax.set_ylabel("USD per tonne of steel", fontsize=12)
    ax.set_xticks(range(len(long_df["City"].cat.categories)))
    ax.set_xticklabels(long_df["City"].cat.categories, rotation=45, ha="right")
    ax.grid(True, linestyle='--', alpha=0.3)

    # Legends
    leg1 = ax.legend(title="Installation Year", loc="upper left", bbox_to_anchor=(1.23, 1))
    ax.add_artist(leg1)

    range_patch = mpatches.Patch(facecolor='lightgray', alpha=0.28,
                                 label=f'BF–BOF range ({int(BFBOF_LOW)}–{int(BFBOF_HIGH)})')
    avg_line_h = mlines.Line2D([], [], color='dimgray', linestyle='--', linewidth=1.8,
                               label=f'BF–BOF avg (${BFBOF_AVG:,.0f})')
    ax.legend(handles=[range_patch, avg_line_h], title="BF–BOF reference",
              loc="upper left", bbox_to_anchor=(1.23, 0.68))

    tier_handles = [
        mlines.Line2D([], [], marker='o', linestyle='None',
                      markerfacecolor='none', markeredgecolor='black',
                      markeredgewidth=1.4, markersize=10,
                      label='Within band, above avg'),
        mlines.Line2D([], [], marker='o', linestyle='None',
                      markerfacecolor='none', markeredgecolor='black',
                      markeredgewidth=2.6, markersize=12,
                      label='Beats avg (≤ 539)'),
    ]
    ax.legend(handles=tier_handles, title="Competitiveness tiers",
              loc="upper left", bbox_to_anchor=(1.23, 0.36))

    if sc is not None:
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label("Share of solar in total VRE capacity (Solar + Wind)")
        cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    fig.subplots_adjust(right=0.85)
    plt.savefig(f"LCOS_Scenario_{scenario}_BFBOF_tiers_scatter.png", dpi=300, bbox_inches='tight')
    plt.show()

# ----------------------------
# 2) Δ Heat map with per-cell tier markers (no legend)
# ----------------------------
for scenario in ["1", "2", "3"]:
    df_s = long_df[long_df["Scenario"] == scenario].copy()
    if df_s.empty:
        continue

    # Δ vs BF–BOF average (keeps colormap tied to one baseline)
    df_s["BFBOF_threshold"] = BFBOF_AVG
    df_s["Delta_vs_BFBOF"] = df_s["Cost"] - df_s["BFBOF_threshold"]

    # City x Year matrix
    pivot = df_s.pivot_table(index="City", columns="Year",
                             values="Delta_vs_BFBOF", aggfunc="mean")
    pivot = pivot.reindex(columns=year_order)

    # Sort cities: earliest beating year first, then by 2050 delta
    earliest_idx = []
    for city, row in pivot.iterrows():
        idx = next((i for i, y in enumerate(year_order)
                    if pd.notna(row.get(y)) and row[y] <= 0), 999)
        earliest_idx.append((city, idx, row.get("2050", np.nan)))
    order = [c for c, _, _ in sorted(earliest_idx,
                                     key=lambda t: (t[1], t[2] if pd.notna(t[2]) else 1e9))]
    pivot = pivot.reindex(index=order)

    # Colormap centered at zero
    vmax = np.nanpercentile(np.abs(pivot.values), 95)
    if not np.isfinite(vmax) or vmax == 0:
        vmax = 50.0
    vmin = -vmax
    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad(color="#dddddd", alpha=0.6)

    # Figure size scales with number of cities
    n_cities = pivot.shape[0]
    fig_h = max(6, min(18, 0.35 * n_cities + 2))
    fig, ax = plt.subplots(figsize=(10, fig_h))

    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)

    # Ticks/labels
    ax.set_xticks(np.arange(len(year_order)))
    ax.set_xticklabels(year_order)
    ax.set_yticks(np.arange(n_cities))
    ax.set_yticklabels(pivot.index)

    ax.set_title(f"Competitiveness vs BF–BOF (Δ = LCOS − BF–BOF avg) — Scenario {scenario}")
    ax.set_xlabel("Year")
    ax.set_ylabel("City")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Δ cost vs BF–BOF (USD/t)\n(negative = competitive)")

    # Overlay per-cell markers, using mean cost per (City, Year)
    mean_cost = (df_s.groupby(["City", "Year"])["Cost"]
                    .mean()
                    .reindex(pd.MultiIndex.from_product([pivot.index, pivot.columns]),
                             fill_value=np.nan))

    for i, city in enumerate(pivot.index):
        for j, year in enumerate(year_order):
            if year not in pivot.columns:
                continue
            val = mean_cost.get((city, year), np.nan)
            if pd.isna(val):
                continue

            in_band_above_avg = (val >= BFBOF_LOW) and (val <= BFBOF_HIGH) and (val > BFBOF_AVG)
            beats_avg         = (val <= BFBOF_AVG)

            if in_band_above_avg:
                ax.scatter(j, i, marker="o", s=40, facecolors="none",
                           edgecolors="k", linewidths=0.8, zorder=3)
            if beats_avg:
                ax.scatter(j, i, marker="*", s=90, edgecolors="k",
                           facecolors="yellow", linewidths=0.6, zorder=4)

    # OPTIONAL: highlight the *first* beats-avg year per city with a larger hollow star
    for i, city in enumerate(pivot.index):
        row = pivot.loc[city]
        j = next((j for j, y in enumerate(year_order)
                  if y in row.index and pd.notna(row[y]) and row[y] <= 0), None)
        if j is not None:
            ax.scatter(j, i, marker="*", s=140, edgecolors="k",
                       facecolors="none", linewidths=1.2, zorder=5)

    # Gridlines
    ax.set_xticks(np.arange(-0.5, len(year_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_cities, 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.6)
    ax.tick_params(axis="both", which="both", length=0)

    fig.tight_layout()
    plt.savefig(f"LCOS_S{scenario}_BFBOF_tiers_heatmap.png", dpi=300, bbox_inches='tight')
    plt.show()

    # Export summary of first beats-avg year per city
    summary = []
    for city in pivot.index:
        row = pivot.loc[city]
        first_year = next((y for y in year_order
                           if y in row.index and pd.notna(row[y]) and row[y] <= 0), None)
        summary.append({"City": city, "FirstBeatsAvgYear": first_year})
    pd.DataFrame(summary).to_csv(f"Competitiveness_S{scenario}_tiers_summary.csv", index=False)
