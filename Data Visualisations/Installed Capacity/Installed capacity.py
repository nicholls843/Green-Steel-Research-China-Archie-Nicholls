import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import os
import re

# =========================
# User choices (edit these)
# =========================
file_path = r"C:\Users\archi\Data Visualisations\Installed Capacity\Installed Capacity .csv"  # tries alt name if not found

SCENARIO = "S1"         # "S1", "S2", "S3"
SORT_BY = "total"       # "total", "alpha", or "year:Y2030" / "year:YCurrent" / "year:Y2040" / "year:Y2050"
TOP_N = None            # e.g., 15 for top 15 cities, or None for all
SAVE_FIG = True
output_folder = r"C:\Users\archi\Data Visualisations\Installed Capacity\charts"

# =========================
# Styling
# =========================
YEARS = ["YCurrent", "Y2030", "Y2040", "Y2050"]
TECHS_SW = ["Solar", "Wind"]
ELEC_TECH = "Electrolyser"

COLORS = {
    "Solar": "#4F81BD",        # Blue
    "Wind": "#7F7F7F",         # Dark grey
    "Electrolyser": "#BFBFBF"  # Light grey
}

# =========================
# Load data (handles both file name variants)
# =========================
if not os.path.exists(file_path):
    alt_path = file_path.replace("Installed Capacity .csv", "Installed Capacity.csv")
    if os.path.exists(alt_path):
        file_path = alt_path
    else:
        raise FileNotFoundError(f"Could not find:\n- {file_path}\n- {alt_path}")

df = pd.read_csv(file_path, encoding="utf-8-sig")
df.columns = df.columns.str.strip()
df["City"] = df["City"].astype(str).str.strip()
df["Province"] = df["Province"].astype(str).str.strip()

# Validate scenario & columns
if SCENARIO not in {"S1", "S2", "S3"}:
    raise ValueError("SCENARIO must be 'S1', 'S2', or 'S3'.")

missing_sw = []
missing_elec = []
for yr in YEARS:
    # Solar/Wind
    for t in TECHS_SW:
        col = f"{yr}_{SCENARIO}_{t}"
        if col not in df.columns:
            missing_sw.append(col)
    # Electrolyser
    elec_col = f"{yr}_{SCENARIO}_{ELEC_TECH}"
    if elec_col not in df.columns:
        missing_elec.append(elec_col)

if missing_sw:
    raise KeyError(f"Missing Solar/Wind columns for {SCENARIO}: {missing_sw}")
if missing_elec:
    raise KeyError(f"Missing Electrolyser columns for {SCENARIO}: {missing_elec}")

# =========================
# Build a unified table for the selected scenario
# =========================
cols = (
    ["City", "Province"]
    + [f"{yr}_{SCENARIO}_{t}" for yr in YEARS for t in TECHS_SW]
    + [f"{yr}_{SCENARIO}_{ELEC_TECH}" for yr in YEARS]
)
sub = df[cols].copy()

# City label with province in brackets
sub["City"] = sub["City"] + " (" + sub["Province"] + ")"

# Totals used for sorting (include Electrolyser too to keep global ordering consistent)
sub["Total_all_years"] = (
    sum(sub[f"{yr}_{SCENARIO}_{t}"] for yr in YEARS for t in TECHS_SW)
    + sum(sub[f"{yr}_{SCENARIO}_{ELEC_TECH}"] for yr in YEARS)
)

def year_total(y):
    return (
        sub[[f"{y}_{SCENARIO}_{t}" for t in TECHS_SW]].sum(axis=1)
        + sub[f"{y}_{SCENARIO}_{ELEC_TECH}"]
    )

# Decide order of cities
s = SORT_BY.lower()
if s == "alpha":
    sub = sub.sort_values("City", ascending=True)
elif s == "total":
    sub["Total_ref"] = sub["Total_all_years"]
    sub = sub.sort_values("Total_ref", ascending=False)
elif s.startswith("year:"):
    m = re.match(r"year:(YCurrent|Y2030|Y2040|Y2050|Current|2030|2040|2050)", SORT_BY, re.IGNORECASE)
    if not m:
        raise ValueError("SORT_BY 'year:XXXX' must be one of YCurrent/Y2030/Y2040/Y2050 (or aliases Current/2030/2040/2050).")
    ref = m.group(1)
    alias = {"Current": "YCurrent", "2030": "Y2030", "2040": "Y2040", "2050": "Y2050"}
    ref_year = alias.get(ref, ref)
    sub["Total_ref"] = year_total(ref_year)
    sub = sub.sort_values("Total_ref", ascending=False)
else:
    raise ValueError("SORT_BY must be 'total', 'alpha', or 'year:YYYY' (e.g., 'year:Y2030').")

# Apply TOP_N if requested
if TOP_N is not None:
    sub = sub.head(int(TOP_N))

cities = sub["City"].tolist()
ypos = np.arange(len(cities))

# =========================
# Prepare data per year for plotting
# =========================
data_sw_by_year = {}
data_elec_by_year = {}
for yr in YEARS:
    data_sw_by_year[yr] = {t: sub[f"{yr}_{SCENARIO}_{t}"].to_numpy() for t in TECHS_SW}
    data_sw_by_year[yr]["Total"] = sum(data_sw_by_year[yr][t] for t in TECHS_SW)
    data_elec_by_year[yr] = sub[f"{yr}_{SCENARIO}_{ELEC_TECH}"].to_numpy()

# =========================
# Figure 1: Solar + Wind (stacked), 4 subplots (one per year)
# =========================
fig_h = max(6, 0.35 * len(cities) + 2)
fig1, axes1 = plt.subplots(nrows=1, ncols=4, sharey=True, figsize=(22, fig_h))

# Consistent x-limit across all years for SW
xmax_sw = max(np.max(data_sw_by_year[yr]["Total"]) for yr in YEARS)
xpad_sw = 0.05 * xmax_sw if xmax_sw > 0 else 1

for i, yr in enumerate(YEARS):
    ax = axes1[i]
    left = np.zeros(len(cities))
    for t in TECHS_SW:
        ax.barh(ypos, data_sw_by_year[yr][t], left=left, color=COLORS[t], label=t if i == 0 else None)
        left += data_sw_by_year[yr][t]

    # y-ticks on all subplots, labels on first AND last (right side)
    ax.set_yticks(ypos)
    if i == 0:
        ax.set_yticklabels(cities, fontsize=9)
    elif i == len(YEARS) - 1:
        ax.set_yticklabels([])
        ax_right = ax.twinx()
        ax_right.set_ylim(ax.get_ylim())
        ax_right.set_yticks(ypos)
        ax_right.set_yticklabels(cities, fontsize=9)
        ax_right.tick_params(axis="y", which="both", length=0)
    else:
        ax.set_yticklabels([])

    ax.set_title(yr)
    ax.set_xlim(0, xmax_sw + xpad_sw)
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f"{int(x):,}"))
    ax.set_xlabel("Installed Capacity (MW)")

fig1.suptitle(f"Installed Capacity by City — {SCENARIO} (Solar + Wind)", y=0.995, fontsize=14)
axes1[0].set_ylabel("City")
handles, labels = axes1[0].get_legend_handles_labels()
fig1.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig1.subplots_adjust(left=0.22, right=0.86, wspace=0.08, bottom=0.10, top=0.92)

if SAVE_FIG:
    os.makedirs(output_folder, exist_ok=True)
    fname1 = f"Installed_Capacity_{SCENARIO}_SW_by_city_facet_province.png"
    save_path1 = os.path.join(output_folder, fname1)
    fig1.savefig(save_path1, dpi=300, bbox_inches="tight")
    print(f"Saved figure: {save_path1}")

# =========================
# Figure 2: Electrolyser only, 4 subplots (one per year)
# =========================
fig2, axes2 = plt.subplots(nrows=1, ncols=4, sharey=True, figsize=(22, fig_h))

# Consistent x-limit across all years for Electrolyser
xmax_e = max(np.max(data_elec_by_year[yr]) for yr in YEARS)
xpad_e = 0.05 * xmax_e if xmax_e > 0 else 1

for i, yr in enumerate(YEARS):
    ax = axes2[i]
    ax.barh(ypos, data_elec_by_year[yr], color=COLORS["Electrolyser"], label="Electrolyser")

    ax.set_yticks(ypos)
    if i == 0:
        ax.set_yticklabels(cities, fontsize=9)
    elif i == len(YEARS) - 1:
        ax.set_yticklabels([])
        ax_right = ax.twinx()
        ax_right.set_ylim(ax.get_ylim())
        ax_right.set_yticks(ypos)
        ax_right.set_yticklabels(cities, fontsize=9)
        ax_right.tick_params(axis="y", which="both", length=0)
    else:
        ax.set_yticklabels([])

    ax.set_title(yr)
    ax.set_xlim(0, xmax_e + xpad_e)
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f"{int(x):,}"))
    ax.set_xlabel("Installed Capacity (MW)")

fig2.suptitle(f"Installed Capacity by City — {SCENARIO} (Electrolyser Only)", y=0.995, fontsize=14)
axes2[0].set_ylabel("City")
handles2, labels2 = axes2[0].get_legend_handles_labels()
fig2.legend(handles2, labels2, loc="lower center", ncol=1, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig2.subplots_adjust(left=0.22, right=0.86, wspace=0.08, bottom=0.10, top=0.92)

if SAVE_FIG:
    fname2 = f"Installed_Capacity_{SCENARIO}_Electrolyser_by_city_facet_province.png"
    save_path2 = os.path.join(output_folder, fname2)
    fig2.savefig(save_path2, dpi=300, bbox_inches="tight")
    print(f"Saved figure: {save_path2}")

plt.show()
