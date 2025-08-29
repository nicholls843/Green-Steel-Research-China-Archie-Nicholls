# Schematic of the thesis system using matplotlib (no external dependencies)
# Encodes included components and flows from your table.

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---------- helpers ----------
def add_box(ax, xy, w, h, text, fontsize=10):
    """Add a rounded rectangle with centered text."""
    x, y = xy
    patch = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.04",
                           linewidth=1.4, fill=False)
    ax.add_patch(patch)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fontsize, wrap=True)
    return patch

def add_arrow(ax, p1, p2, text=None, style="->", lw=1.4, ls="-"):
    """Add an arrow from p1 to p2 with optional label."""
    arr = FancyArrowPatch(p1, p2, arrowstyle=style,
                          linewidth=lw, linestyle=ls, mutation_scale=12)
    ax.add_patch(arr)
    if text:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx, my + 0.15, text, ha="center", va="bottom", fontsize=9)
    return arr

# ---------- layout ----------
W, H = 2.2, 1.0  # default box size
fig, ax = plt.subplots(figsize=(12, 7))

# Top row: VRE -> Battery ↔ Bus, Grid backup, Fuel cells
vre       = add_box(ax, (0.2, 6.6), W, H, "Solar PV &\nOnshore Wind\n(Renewable electricity generation)")
bat       = add_box(ax, (2.9, 6.6), W, H, "Battery storage\n(short-term balancing)")
bus       = add_box(ax, (5.6, 6.6), W, H, "Electricity bus")
grid      = add_box(ax, (8.3, 7.4), W, H, "Grid imports\n(backup / penalised)")
fuelcell  = add_box(ax, (8.3, 6.6), W, H, "Fuel cells\n(H₂ → power\nin deficits)")

# Mid row: Electrolyzers -> Compressors -> H₂ storage
ely       = add_box(ax, (5.6, 4.6), W, H, "Electrolyzers\n(electricity + water → H₂)")
comp      = add_box(ax, (8.3, 4.6), W, H, "Compressors\n(H₂ for storage)")
h2store   = add_box(ax, (10.8, 4.6), W, H, "Compressed H₂ storage\n(CGH₂)")

# Lower row: Ore chain → DRI → EAF & caster → Crude steel
benef     = add_box(ax, (0.2, 2.4), W, H, "Ore beneficiation\n& pelletisation")
dri       = add_box(ax, (3.1, 2.4), W, H, "Hydrogen-based\nDRI reactor")
eaf       = add_box(ax, (6.1, 2.4), W, H, "EAF & caster\n(melts DRI + scrap)")
steel     = add_box(ax, (9.2, 2.4), W, H, "Crude steel\n(output)")

# Supporting systems
transport = add_box(ax, (-1.8, 2.4), W, H, "Material input\ntransport")
scrap     = add_box(ax, (4.5, 1.0), W, H, "Scrap feed")
labour    = add_box(ax, (8.3, 1.0), W, H, "Labour &\nmaintenance costs")

# Excluded components
excluded  = add_box(ax, (0.2, 0.2), 6.1, 0.9,
                    "Excluded: Downstream steel processing • Upstream mining beyond beneficiation • "
                    "VRE-related embodied construction emissions")

# ---------- flows ----------
# Electricity generation, storage, and backup
add_arrow(ax, (0.2+W, 7.1),   (2.9, 7.1),        "electricity")             # VRE → Battery
add_arrow(ax, (2.9+W, 7.1),   (5.6, 7.1),        "electricity (discharge)") # Battery → Bus
add_arrow(ax, (5.6, 7.1),     (2.9+W, 7.1),      "electricity (charge)")    # Bus → Battery
add_arrow(ax, (8.3, 7.9),     (5.6+W, 7.9),      "backup supply", ls="--")  # Grid → Bus (penalised)
add_arrow(ax, (5.6+W, 7.1),   (8.3, 7.1),        "electricity")             # Bus → Fuel cells
add_arrow(ax, (8.3+W, 7.1),   (5.6+0.05, 7.1),   "electricity")             # Fuel cells → Bus

# Electricity to processes
add_arrow(ax, (5.6+W/2, 6.6), (5.6+W/2, 5.6),    "electricity")             # Bus → Electrolyzers
add_arrow(ax, (5.6+W, 6.1),   (8.3, 5.2),        "electricity")             # Bus → Compressors
add_arrow(ax, (5.6+W/2, 6.6), (6.1+W/2, 3.4),    "electricity")             # Bus → EAF

# Hydrogen path
add_arrow(ax, (5.6+W, 5.1),   (8.3, 5.1),        "H₂")                      # Electrolyzers → Compressors
add_arrow(ax, (8.3+W, 5.1),   (10.8, 5.1),       "H₂")                      # Compressors → H₂ storage
add_arrow(ax, (10.8+W/2, 4.6),(8.3+W/2, 6.6),    "H₂")                      # H₂ storage → Fuel cells

# Ore → DRI → EAF → Steel
add_arrow(ax, (0.2+W, 2.9),   (3.1, 2.9),        "ore")                     # Beneficiation → DRI
add_arrow(ax, (3.1+W, 2.9),   (6.1, 2.9),        "DRI")                     # DRI → EAF
add_arrow(ax, (6.1+W, 2.9),   (9.2, 2.9),        "cast steel")              # EAF → Crude steel

# Scrap and transport
add_arrow(ax, (4.5+W/2, 2.0), (6.1+W/2, 2.4),    "scrap")                   # Scrap feed → EAF
add_arrow(ax, (-1.8+W, 2.9),  (0.2, 2.9),        "materials")               # Transport → Beneficiation
add_arrow(ax, (-1.8+W, 2.9),  (4.5, 1.5),        "scrap/materials")         # Transport → Scrap feed

# Final styling
ax.set_xlim(-2.2, 13.2)
ax.set_ylim(-0.2, 9.0)
ax.set_aspect("equal", adjustable="box")
ax.axis("off")
ax.set_title("System schematic: Renewable-powered H₂–DRI–EAF steelmaking model", fontsize=13)

# Save (optional)
plt.savefig("system_schematic.png", bbox_inches="tight", dpi=300)
plt.savefig("system_schematic.svg", bbox_inches="tight")
plt.show()
