#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
from pathlib import Path
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties

# ---------- SUPPRESS WARNINGS ----------
warnings.filterwarnings("ignore", message="Glyph .* missing from font")
# ---------------------------------------

# ---------- GLOBAL FONT SETTINGS ----------
plt.rcParams.update({
    'font.family': 'TeX Gyre Termes',  # main font
    'font.size': 18,
    'axes.titlesize': 20,
    'axes.labelsize': 20,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 18,
    'legend.title_fontsize': 19,
    # Make math look Times-like and default to upright (we'll force italics where needed)
    'mathtext.fontset': 'stix',
    'mathtext.default': 'it',
})
# Default font for μ★ axis label (non-bold)
default_font = FontProperties(family=rcParams.get('font.sans-serif', ['DejaVu Sans']))

# ------------------ Configuration ------------------
BASE_DIR = Path(__file__).resolve().parent           # folder containing morris2.py
# If the Excel files are in a sibling folder called "Excel":
DATA_DIR = str((BASE_DIR.parent / "Result_data").resolve())
# If they are next to the script instead, use:
# DATA_DIR = str(BASE_DIR.resolve())

FILES = [
    '25bacteria.xlsx', '25fungi.xlsx', '25maom.xlsx', '25pom.xlsx',
    '27bacteria.xlsx', '27fungi.xlsx', '27maom.xlsx', '27pom.xlsx',
]

# Save PDFs next to the script (in a subfolder)
OUT_DIR = str((BASE_DIR / "plots").resolve())
os.makedirs(OUT_DIR, exist_ok=True)

PH_COLOURS = {
    '3.5': '#d73027',
    '4.5': '#fc8d59',
    '5.5': '#127c4a',
    '6.5': '#91bfdb',
    '8':   '#4575b4',
}

# --- Your desired parameter order (legend order & marker assignment) ---
PARAM_ORDER = [
    "reference_cue_logit",
    "logit_cue_with_temperature",
    "min_pH_microbes",
    "lowest_optimal_pH_microbes",
    "highest_optimal_pH_microbes",
    "max_pH_microbes",
]

# --- Pretty labels (italics/upright per item) ---
#   \mathit{...} = italic, \mathrm{...} = upright
PARAM_LABEL_MAP = {
    "reference_cue_logit":           r"$\mathit{RCL}$",               # italic
    "logit_cue_with_temperature":    r"$\beta_T$",          # beta with italic T subscript
    "min_pH_microbes":               r"$\mathit{pH}_{\min}$",          # upright pH
    "lowest_optimal_pH_microbes":    r"$\mathit{pH}_{\mathrm{low}}$",
    "highest_optimal_pH_microbes":   r"$\mathit{pH}_{\mathrm{high}}$",
    "max_pH_microbes":               r"$\mathit{pH}_{\max}$",
}

PARAM_MARKERS = ['o', 's', '^', 'v', 'D', 'P']  # used in PARAM_ORDER sequence
AXIS_MARGIN = 0.12
FIGSIZE = (10, 8)
# ---------------------------------------------------

def get_params_in_workbook(xls):
    """Collect all unique parameter names across sheets, preserving PARAM_ORDER first."""
    names = []
    for sn in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sn)
        for p in df['parameter'].astype(str).unique():
            if p not in names:
                names.append(p)
    # ORDER: first those in PARAM_ORDER (if present), then any extras (as-is)
    ordered = [p for p in PARAM_ORDER if p in names]
    extras = [p for p in names if p not in ordered]
    return ordered + extras

def build_param_marker_map(ordered_params):
    """Assign markers in the order of ordered_params."""
    if len(ordered_params) < 6:
        raise ValueError('Fewer than six unique parameters found.')
    mapping = {}
    for i, p in enumerate(ordered_params):
        mapping[p] = PARAM_MARKERS[i % len(PARAM_MARKERS)]
    return mapping

def add_reference_lines(ax, x_max, y_max):
    x_vals = np.linspace(0, x_max, 500)
    slopes = [1.0, 0.5, 0.1]
    styles = ['-', '--', '-.']
    labels = ['σ/μ★ = 1.0', 'σ/μ★ = 0.5', 'σ/μ★ = 0.1']
    for slope, style in zip(slopes, styles):
        ax.plot(x_vals, slope * x_vals, style, lw=1, color='k')
    for slope, label in zip(slopes, labels):
        x_end = x_max * 0.97
        y_end = slope * x_end
        if y_end > y_max * 0.97:
            y_end = y_max * 0.97
            x_end = y_end / slope
        ax.text(x_end, y_end, label,
                ha='right', va='bottom', fontsize=12, color='k',
                rotation=np.degrees(np.arctan(slope)),
                rotation_mode='anchor')

def scan_axis_limits(xls, sheet_names):
    max_mu = max_sigma = 0.0
    for sn in sheet_names:
        df = pd.read_excel(xls, sheet_name=sn)
        max_mu = max(max_mu, df['mu_star'].max())
        max_sigma = max(max_sigma, df['sigma'].max())
    return max_mu, max_sigma

def create_plot(workbook_path):
    basename = os.path.splitext(os.path.basename(workbook_path))[0]
    xls = pd.ExcelFile(workbook_path)
    sheet_names = xls.sheet_names
    if not sheet_names:
        print(f'[Warning] No sheets found in {workbook_path}')
        return

    # Parameter order & markers
    ordered_params = get_params_in_workbook(xls)
    marker_map = build_param_marker_map(ordered_params)

    # Axis limits
    max_mu, max_sigma = scan_axis_limits(xls, sheet_names)
    x_lim_max = max_mu * (1 + AXIS_MARGIN)
    y_lim_max = max_sigma * (1 + AXIS_MARGIN)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.subplots_adjust(right=0.73)

    # Scatter points for each sheet (pH)
    for sn in sheet_names:
        colour = PH_COLOURS.get(sn, plt.cm.tab20(len(PH_COLOURS) % 20))
        df = pd.read_excel(xls, sheet_name=sn)
        for _, row in df.iterrows():
            ax.scatter(row['mu_star'], row['sigma'],
                       color=colour,
                       marker=marker_map.get(row['parameter'], 'o'),
                       edgecolor='k', s=60,
                       label=f'pH {sn}')

    # Dedup pH legend
    handles, labels = ax.get_legend_handles_labels()
    pH_handles, pH_labels, seen = [], [], set()
    for h, l in zip(handles, labels):
        if l not in seen and l.startswith('pH'):
            pH_handles.append(h); pH_labels.append(l); seen.add(l)

    pH_legend = ax.legend(pH_handles, pH_labels,
                          loc='upper left', bbox_to_anchor=(1.02, 0.95))
    ax.add_artist(pH_legend)

    # Parameter legend (ordered, with pretty/math labels)
    param_handles, param_labels = [], []
    for p in ordered_params:
        # skip if not in our label map and not one of the main 6
        pretty = PARAM_LABEL_MAP.get(p, p)
        mk = marker_map[p]
        param_handles.append(plt.Line2D([], [], marker=mk, linestyle='',
                                        color='grey', markeredgecolor='k', markersize=8))
        param_labels.append(pretty)

    ax.legend(param_handles, param_labels, title='Parameter',
              loc='lower left', bbox_to_anchor=(1.02, 0.1), handletextpad=0.8)

    # Axes, grid, refs
    ax.set_xlim(0, x_lim_max)
    ax.set_ylim(0, y_lim_max)
    add_reference_lines(ax, x_lim_max, y_lim_max)

    # μ★ axis label in default font (non-bold)
    ax.set_xlabel('μ★', fontproperties=default_font, fontweight='normal')
    ax.set_ylabel('σ (Interaction)')
    ax.grid(True, lw=0.25, alpha=0.5)
    fig.tight_layout()

    pdf_path = os.path.join(OUT_DIR, f'{basename}_morris_scatter.pdf')
    fig.savefig(pdf_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    print(f'Saved → {pdf_path}')

def main():
    for fname in FILES:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            print(f'[Warning] File not found: {fpath}')
            continue
        create_plot(fpath)

if __name__ == '__main__':
    main()
