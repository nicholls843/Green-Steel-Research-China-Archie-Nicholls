import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import re
from pathlib import Path

# ================== USER PATH ==================
file_path = r"C:\Users\archi\Data Visualisations\Installed Capacity\Solar Installed Capacity (MW).xlsx"
# ===============================================

# --- Load Excel (first sheet by default) ---
xls = pd.ExcelFile(file_path)
sheet_name = xls.sheet_names[0]
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Standardize column names for easier matching
df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]

# --- Identify City/Province columns robustly ---
if "City" in df.columns:
    city_col = "City"
elif "city" in df.columns:
    city_col = "city"
else:
    city_col = df.select_dtypes(include=["object"]).columns[0]

prov_col = None
for cand in ["Province", "province", "Region", "region"]:
    if cand in df.columns:
        prov_col = cand
        break

# --- Patterns for year & scenario labels in column names ---
year_pattern = r"Y(?:Current|\d{4})"
scen_pattern = r"S\d+"

def extract_year_scen(colname: str):
    """Return (YearTag, ScenarioNumber) from a column name."""
    y = re.search(year_pattern, colname)
    s = re.search(scen_pattern, colname)
    year_tag = y.group(0) if y else None         # e.g., 'Y2040' or 'YCurrent'
    scen_num = s.group(0).replace("S", "") if s else None  # e.g., '2'
    return year_tag, scen_num

def parse_ratio(val):
    """Parse over‑capacity ratio strings like '5.42:1', '1:5.42', '5.42x', or plain numbers."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float, np.number)):
        return float(val)
    s = str(val).strip().lower().replace(" ", "")
    # '5.4x'
    if s.endswith("x"):
        try:
            return float(s[:-1])
        except Exception:
            return np.nan
    # 'a:b'
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2:
            try:
                a = float(parts[0]); b = float(parts[1])
                if b == 0:
                    return np.nan
                return a / b
            except Exception:
                return np.nan
    # plain number string
    try:
        return float(s)
    except Exception:
        return np.nan

# --- Identify Installed Capacity (MW) columns and Over‑Capacity Factor columns ---
installed_cols = []
ocf_cols = []

for col in df.columns:
    y, s = extract_year_scen(col)
    if not (y and s):
        continue
    low = col.lower()

    # Likely installed capacity columns (MW)
    if any(k in low for k in ["installed", "capacity", "mw", "inst_cap", "installed_capacity"]):
        # Avoid matching factor columns by excluding typical keywords
        if not any(k in low for k in ["cf", "cap_factor", "capacityfactor", "capacity_factor", "over", "ocf", "overbuild", "over_capacity", "overcap"]):
            installed_cols.append(col)

    # Likely over‑capacity factor columns
    if any(k in low for k in ["over", "overbuild", "ocf", "over_capacity", "overcap", "cap_factor", "capacityfactor", "capacity_factor", "cf"]):
        ocf_cols.append(col)

# Fallback: treat numeric year+scenario columns as installed capacity if nothing matched
if not installed_cols:
    for col in df.columns:
        if re.search(year_pattern, col) and re.search(scen_pattern, col):
            if pd.api.types.is_numeric_dtype(df[col]):
                installed_cols.append(col)

# Build a lookup for OCF by (YearTag, ScenarioNumber)
ocf_lookup = {}
for col in ocf_cols:
    y, s = extract_year_scen(col)
    if y and s:
        ocf_lookup[(y, s)] = col

# --- Reshape to long format ---
records = []
for ic_col in installed_cols:
    y, s = extract_year_scen(ic_col)
    if not (y and s):
        continue

    ocf_col = ocf_lookup.get((y, s), None)

    use_cols = [city_col]
    if prov_col: use_cols.append(prov_col)
    use_cols.append(ic_col)

    temp = df[use_cols].copy()
    temp.rename(columns={city_col: "City"}, inplace=True)
    if prov_col: temp.rename(columns={prov_col: "Province"}, inplace=True)

    temp["Installed_MW"] = pd.to_numeric(temp[ic_col], errors="coerce")
    temp.drop(columns=[ic_col], inplace=True)

    # Attach over‑capacity factor (ratio, not %)
    if ocf_col and ocf_col in df.columns:
        temp["OverCapacity_Ratio"] = df[ocf_col].apply(parse_ratio)
    else:
        temp["OverCapacity_Ratio"] = np.nan

    # Year label formatting
    year_label = "Current" if y == "YCurrent" else y.replace("Y", "")
    temp["Year"] = year_label
    temp["Scenario"] = s

    records.append(temp)

long_df = pd.concat(records, ignore_index=True) if records else pd.DataFrame()

# --- Filter out 0 or missing MW so they never appear on the y=0 line ---
long_df = long_df[(long_df["Installed_MW"].notna()) & (long_df["Installed_MW"] > 0)]

# --- Order cities by size (max Installed_MW across years) for nicer flow ---
if not long_df.empty:
    city_order = (
        long_df.groupby("City")["Installed_MW"]
        .max()
        .sort_values(ascending=False)
        .index.tolist()
    )
    long_df["City"] = pd.Categorical(long_df["City"], categories=city_order, ordered=True)

# --- Plotting (scenario‑by‑scenario), neat & readable ---
marker_map = {"Current": "P", "2030": "o", "2040": "s", "2050": "D"}
year_order_key = {"Current": 0, "2030": 1, "2040": 2, "2050": 3}
offset_map = {"Current": -0.18, "2030": -0.06, "2040": 0.06, "2050": 0.18}
cmap_name = "plasma"

def ocf_bounds(series):
    """Robust color scale bounds for OCF."""
    vals = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if len(vals) == 0:
        return 1.0, 1.0
    vmin = max(1.0, np.nanpercentile(vals, 5))
    vmax = np.nanpercentile(vals, 95)
    if vmax <= vmin:
        vmax = float(np.nanmax(vals))
    return float(vmin), float(vmax)

out_dir = Path(file_path).parent

for scenario in sorted(long_df["Scenario"].dropna().unique(), key=lambda x: int(x)):
    sub = long_df[long_df["Scenario"] == scenario].copy()
    if sub.empty:
        continue

    vmin, vmax = ocf_bounds(sub["OverCapacity_Ratio"])

    # dynamic width: 0.35 in per city, min 12, max 20
    n_cities = sub["City"].nunique()
    fig_w = min(max(12, 0.35 * n_cities), 20)
    plt.figure(figsize=(fig_w, 8))

    # connectors (very faint, behind points)
    for city, df_c in sub.groupby("City"):
        df_c = df_c.sort_values(by="Year", key=lambda s: s.map(year_order_key))
        if len(df_c) > 1:
            # straight connectors at the base x (no dodge)
            x_base = np.full(len(df_c), list(sub["City"].cat.categories).index(city))
            plt.plot(
                x_base, df_c["Installed_MW"].values,
                color="0.85", linewidth=0.8, alpha=0.6, zorder=1
            )

    # scatter with dodged x positions for each year
    last_scatter = None
    for year, marker in marker_map.items():
        dyear = sub[sub["Year"] == year]
        if dyear.empty:
            continue

        base_x = dyear["City"].cat.codes.to_numpy(dtype=float)
        x = base_x + offset_map[year]

        colors = pd.to_numeric(dyear["OverCapacity_Ratio"], errors="coerce")
        if colors.isna().all():
            colors = np.full(len(dyear), (vmin + vmax) / 2.0)
        else:
            colors = colors.fillna(colors.median())

        last_scatter = plt.scatter(
            x=x,
            y=dyear["Installed_MW"],
            c=colors.astype(float),
            cmap=cmap_name,
            vmin=vmin, vmax=vmax,
            marker=marker,
            s=90,
            linewidths=0.6, edgecolors="k",
            zorder=2,
            label=year
        )

    # axes, labels, ticks
    plt.title(f"Installed Solar Capacity by City (Scenario {scenario})", fontsize=14)
    plt.ylabel("Installed Capacity (MW)", fontsize=12)

    # x tick labels for cities present in this scenario
    cities_present = [c for c in sub["City"].cat.categories if c in sub["City"].unique()]
    xticks_idx = np.arange(len(cities_present))
    plt.xticks(xticks_idx, cities_present, rotation=35, ha="right")

    # thin labels further when many cities
    if len(cities_present) > 30:
        for i, label in enumerate(plt.gca().get_xticklabels()):
            if i % 2 != 0:
                label.set_visible(False)

    # y grid & tidy spines
    ax = plt.gca()
    ax.yaxis.set_major_locator(mticker.MaxNLocator(6))
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    # legend
    leg = plt.legend(title="Installation Year", frameon=True)
    leg.get_frame().set_alpha(0.9)

    # colorbar for ratio (×)
    if last_scatter is not None:
        cbar = plt.colorbar(last_scatter)
        cbar.set_label("Over‑Capacity Ratio (×)")
        ticks = np.linspace(vmin, vmax, 5)
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f"{t:.1f}×" for t in ticks])

    plt.tight_layout()

    # Save alongside the Excel
    out_path = out_dir / f"Solar_Installed_OCF_Scenario_{scenario}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()

print("Done. Saved one PNG per scenario next to the Excel file.")
