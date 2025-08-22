#!/usr/bin/env python
# -*- coding: utf-8 -*-



import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from itertools import cycle
import warnings

# ---------- SUPPRESS WARNINGS ----------
warnings.filterwarnings("ignore", message="Glyph .* missing from font")
# ---------------------------------------

# ---------- GLOBAL FONT SETTINGS ----------
plt.rcParams.update({
    'font.family': 'TeX Gyre Termes',
    'font.size': 25,
    'axes.titlesize': 25,
    'axes.labelsize': 25,
    'xtick.labelsize': 25,
    'ytick.labelsize': 25,
    'legend.fontsize': 25,
    'legend.title_fontsize': 25
})

LEGEND_MARKERSCALE = 0.9
LEGEND_BORDERPAD = 0.3
LEGEND_LABELSPACING = 0.3
LEGEND_HANDLELEN = 1.2
LEGEND_HANDLETEXTPAD = 0.5
# ------------------------------------------
BASE_DIR = Path(__file__).resolve().parent  # relative path
NPZ_DIR = BASE_DIR.parent / "virtual_ecosystem"
OUT_PDF = BASE_DIR / "PDP_25C_allpH.pdf"# For 27 temperature, change the "25C" to "27C"
OUT_PDF.parent.mkdir(parents=True, exist_ok=True)


BINS = 100  # box number
# =====================

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


npz_files = sorted(NPZ_DIR.glob("25-*.npz")) # For 27 temperature, change the "25-" to "27-"
if not npz_files:
    raise FileNotFoundError(f"{NPZ_DIR} can't find 25-*.npz")

def pH_from_name(fname: str):
    """25-35.npz → 3.5"""
    m = re.search(r"25-(\d+)", fname) # For 27 temperature, change the "25C" to "27C"

    if not m:
        raise ValueError(f"File format error: {fname}")
    return float(m.group(1)) / 10.0

plt.figure(figsize=(15, 6))
color_cycle = cycle(COLORS)
ph_color_map = {}

for npz_path in npz_files:
    ph_val = pH_from_name(npz_path.stem)
    color = next(color_cycle)
    ph_color_map[ph_val] = color

    data = np.load(npz_path)
    X, Y = data["X"], data["Y"]

    ref_cue = X[:, 1]  # reference_cue_logit (RCL)
    bacteria = Y[:, 2] # for MAOM pool, change the number to 0
    fungi = Y[:, 4] # for POM pool, change the number to 1

    # average
    bins = np.linspace(ref_cue.min(), ref_cue.max(), BINS + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    b_means, f_means = [], []

    for i in range(len(bins) - 1):
        mask = (ref_cue >= bins[i]) & (ref_cue < bins[i + 1])
        if mask.any():
            b_means.append(bacteria[mask].mean())
            f_means.append(fungi[mask].mean())
        else:
            b_means.append(np.nan)
            f_means.append(np.nan)

    
    plt.plot(bin_centers, f_means, color=color, lw=2)           # SEF
    plt.plot(bin_centers, b_means, color=color, ls="--", lw=2)  # SEB


ph_handles = [mpatches.Patch(color=ph_color_map[ph], label=f"pH {ph}")
              for ph in sorted(ph_color_map)]
style_handles = [
    mlines.Line2D([], [], color="black", lw=2, label="SEF"),       # For POM pool, change "SEF" to "POM pool"
    mlines.Line2D([], [], color="black", lw=2, ls="--", label="SEB")  # For MAOM pool, change "SEB" to "MAOM pool"
]

first = plt.legend(
    handles=ph_handles, loc="upper left",
    bbox_to_anchor=(1.02, 1.00),
    markerscale=LEGEND_MARKERSCALE, borderpad=LEGEND_BORDERPAD,
    labelspacing=LEGEND_LABELSPACING, handlelength=LEGEND_HANDLELEN,
    handletextpad=LEGEND_HANDLETEXTPAD
)
second = plt.legend(
    handles=style_handles, loc="lower left",
    bbox_to_anchor=(1.02, 0.08),
    markerscale=LEGEND_MARKERSCALE, borderpad=LEGEND_BORDERPAD,
    labelspacing=LEGEND_LABELSPACING, handlelength=LEGEND_HANDLELEN,
    handletextpad=LEGEND_HANDLETEXTPAD
)
plt.gca().add_artist(first)


plt.xlabel("RCL", fontstyle="italic")

plt.ylabel("Mean content")
plt.xlim(bins.min(), bins.max())
plt.xticks(np.linspace(bins.min(), bins.max(), 5))

plt.tight_layout()
plt.savefig(OUT_PDF, format="pdf")
plt.show()

print(f"✅ plot save as：{OUT_PDF}")
