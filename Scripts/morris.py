#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate μ★ heat-maps with:
  • Custom parameter row order (top→bottom)
  • Italic/upright control per-parameter label
  • Blue starts at 0; no bold text
  • TeX Gyre Termes for main text (math rendered via STIX for better match)
"""

import re, sys, warnings
from pathlib import Path
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties

# ---------- SUPPRESS WARNINGS ----------
warnings.filterwarnings("ignore", message="Glyph .* missing from font")
# --------------------------------------

# ---------- GLOBAL FONT SETTINGS ----------
plt.rcParams.update({
    'font.family': 'TeX Gyre Termes',  # main text font (Times-like)
    'font.size': 18,
    'axes.titlesize': 20,
    'axes.labelsize': 20,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 18,
    'legend.title_fontsize': 19,
    # Make math look Times-like so it matches the text better
    'mathtext.fontset': 'stix',
    'mathtext.default': 'it',
})
# Keep μ★ label in default (non-Termes) font if desired
default_font = FontProperties(family=rcParams.get('font.sans-serif', ['DejaVu Sans']))

# ---------- CONFIG ----------
BASE_DIR   = Path(__file__).resolve().parent          # folder containing morris.py
DATA_DIR   = BASE_DIR.parent / "Result_data"                # sibling folder: ../Excel
OUT_DIR    = BASE_DIR / "Result_plots"                       # save PDFs here
OUT_DIR.mkdir(parents=True, exist_ok=True)

# allow CLI overrides if you want
ap = argparse.ArgumentParser(add_help=False)
ap.add_argument("--data-dir", default=str(DATA_DIR))
ap.add_argument("--out-dir",  default=str(OUT_DIR))
args, _ = ap.parse_known_args()
DATA_DIR = Path(args.data_dir).expanduser().resolve()
OUT_DIR  = Path(args.out_dir).expanduser().resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)


TEMPS      = [25, 27]                      # temperatures to include
PH_KEEP    = ["3.5", "4.5", "5.5", "6.5", "8"]
HEAT_CMAP  = cm.get_cmap("coolwarm")       # blue→red
# --------------------------------------

# ---------- PARAMETER ORDER & LABELS ----------
# Row order (top→bottom). Only those present in the data will be kept.
PARAM_ORDER = [
    "reference_cue_logit",
    "logit_cue_with_temperature",
    "min_pH_microbes",
    "lowest_optimal_pH_microbes",
    "highest_optimal_pH_microbes",
    "max_pH_microbes",
]

# Pretty labels. Use \mathit{...} for italics, \mathrm{...} for upright.
# Tip: To make pH italic instead, switch \mathrm{pH} → \mathit{pH}.
PARAM_TICK_MAP = {
    "reference_cue_logit":           r"$\mathit{RCL}$",             # italic
    "logit_cue_with_temperature":    r"$\beta_T$",                  # Greek is italic by default
    "min_pH_microbes":               r"$\mathit{pH}_{\min}$",       # upright pH
    "lowest_optimal_pH_microbes":    r"$\mathit{pH}_{\mathrm{low}}$",
    "highest_optimal_pH_microbes":   r"$\mathit{pH}_{\mathrm{high}}$",
    "max_pH_microbes":               r"$\mathit{pH}_{\max}$",
}
# ----------------------------------------------

# ---------- LOAD XLSX ----------
rows = []
if not DATA_DIR.exists():
    sys.exit(f"❌ DATA_DIR not found: {DATA_DIR}")

for f in DATA_DIR.glob("*.xls*"):
    m = re.match(r"(\d+)(.*)", f.stem)
    if not m:
        continue
    try:
        temp = int(m.group(1))
    except ValueError:
        continue
    if temp not in TEMPS:
        continue

    out_tag = (m.group(2).strip() or "unknown").lower()
    xls = pd.ExcelFile(f)
    for sh in xls.sheet_names:
        ph = sh.strip()
        if ph not in PH_KEEP:
            continue
        df = pd.read_excel(xls, sh).rename(str.lower, axis=1)
        # Expect columns: parameter, mu_star, sigma
        if {"parameter", "mu_star", "sigma"}.issubset(df.columns):
            for _, r in df.iterrows():
                rows.append(dict(
                    T=temp, pH=ph, output=out_tag,
                    param=str(r["parameter"]),
                    mu=r["mu_star"],
                    sig=r["sigma"]
                ))

data = pd.DataFrame(rows)
if data.empty:
    sys.exit("❌  No data rows found. Check DATA_DIR and Excel sheet/column names.")

# ---------- PLOT HEATMAPS ----------
params_present = list(data.param.unique())

for out, sub in data.groupby("output"):
    if sub.empty:
        print(f"⚠  skip heat-map: '{out}' has no rows")
        continue

    # Pivot to heatmap table
    heat = sub.pivot_table(index="param", columns=["T", "pH"], values="mu")

    # Enforce custom row order (keep only those present)
    order_idx = [p for p in PARAM_ORDER if p in heat.index]
    # If there are extra params not listed, append them after the ordered list
    extras = [p for p in heat.index if p not in order_idx]
    heat = heat.reindex(index=order_idx + extras)

    # Enforce column order
    desired_cols = [(t, ph) for t in TEMPS for ph in PH_KEEP]
    # Keep only columns that exist
    desired_cols = [c for c in desired_cols if c in heat.columns]
    heat = heat[desired_cols]

    # Color scale: blue at 0 → red at global max
    vmin = 0.0
    vmax = float(heat.max().max()) if heat.size else 1.0

    pdf_name = f"morris_heatmap_{out}.pdf"
    with PdfPages(pdf_name) as pdf:
        # Size scales with number of columns; height fixed for readability
        fig_w = max(6.0, 1.2 * max(1, heat.shape[1]))
        plt.figure(figsize=(fig_w, 3.8))

        # Pretty y-axis labels (with italics where requested)
        ytick_labels = [PARAM_TICK_MAP.get(p, p) for p in heat.index]

        ax = sns.heatmap(
            heat,
            cmap=HEAT_CMAP,
            annot=False,
            cbar_kws={'label': ''},
            vmin=vmin,
            vmax=vmax,
            yticklabels=ytick_labels
        )
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.ylabel("Parameter")
        plt.xlabel("Temperature-pH")

        # Colorbar label: keep in default font (non-bold)
        cbar = ax.collections[0].colorbar
        cbar.set_label('μ★', fontproperties=default_font, fontweight='normal')
        for t in cbar.ax.get_yticklabels():
            t.set_fontweight('normal')

        plt.tight_layout()
        pdf.savefig()
        plt.close()

    print(f"✓  wrote {pdf_name}")

print("\n✅  Heat-maps complete.")
