#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import pearsonr
import warnings
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties

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
    'legend.title_fontsize': 25,
    # Make math match serif & default to italics
    'mathtext.fontset': 'stix',
    'mathtext.default': 'it',
})

# Default font for μ★ (kept non-italic / non-math)
default_font = FontProperties(family=rcParams['font.sans-serif'])
# ------------------------------------------

# ---------- Appearance ----------
PH_COLOURS = {
    '3.5': 'red',
    '4.5': 'blue',
    '5.5': 'orange',
    '6.5': 'green',
    '8':   'purple',
}
MARKERS = ['o', 's', 'D', '^', 'v', '*']

# Legend styling
LEGEND_FONTSIZE = 15
LEGEND_TITLE_FONTSIZE = 16
LEGEND_MARKERSCALE = 0.9
LEGEND_BORDERPAD = 0.3
LEGEND_LABELSPACING = 0.3
LEGEND_HANDLELEN = 1.2
LEGEND_HANDLETEXTPAD = 0.5
# --------------------------------

DATASETS = [
    ('25bacteria.xlsx', '25', 'Bacteria'),
    ('25fungi.xlsx',    '25', 'Fungi'),
    ('25maom.xlsx',     '25', 'MAOM'),
    ('25pom.xlsx',      '25', 'POM'),
    ('27bacteria.xlsx', '27', 'Bacteria'),
    ('27fungi.xlsx',    '27', 'Fungi'),
    ('27maom.xlsx',     '27', 'MAOM'),
    ('27pom.xlsx',      '27', 'POM'),
]

# ---------- Pretty parameter labels (ITALIC) ----------
# Map raw parameter keys (as stored in the Excel files) to display labels.
PARAM_LABEL_MAP = {
    "reference_cue_logit":            r"$\mathit{RCL}$",
    "logit_cue_with_temperature":     r"$\beta_{\mathit{T}}$",
    "min_pH_microbes":                r"$\mathit{pH}_{\mathit{min}}$",
    "lowest_optimal_pH_microbes":     r"$\mathit{pH}_{\mathit{low}}$",
    "highest_optimal_pH_microbes":    r"$\mathit{pH}_{\mathit{high}}$",
    "max_pH_microbes":                r"$\mathit{pH}_{\mathit{max}}$",
}
# -----------------------------------------------------

def colour_for_ph(ph: str) -> str:
    return PH_COLOURS.get(str(ph), 'grey')

def ensure_files(directory: Path, filenames: List[str]) -> None:
    missing = [f for f in filenames if not (directory / f).exists()]
    if missing:
        raise FileNotFoundError('Missing files: ' + ', '.join(missing))

def create_plots(data_dir: Path,
                 out_dir: Path,
                 figsize: Tuple[float, float],
                 stat_pos: Tuple[float, float],
                 dpi: int) -> None:

    out_dir.mkdir(parents=True, exist_ok=True)
    ensure_files(data_dir, [f for f, _, _ in DATASETS])

    for fname, temp, material in DATASETS:
        sheets = pd.read_excel(data_dir / fname, sheet_name=None)

        records = [
            {
                'mu_star':   row['mu_star'],
                'ST':        row['ST'],
                'ph':        str(ph),
                'parameter': row['parameter']
            }
            for ph, df in sheets.items()
            for _, row in df.iterrows()
        ]
        if not records:
            continue

        mu = np.array([r['mu_star'] for r in records], float)
        st = np.array([r['ST'] for r in records], float)

        r_val, p_val = pearsonr(mu, st)
        slope, intercept = np.polyfit(mu, st, 1)
        x_line = np.array([mu.min(), mu.max()])
        y_line = slope * x_line + intercept

        parameters = sorted({r['parameter'] for r in records})
        marker_map = {p: m for p, m in zip(parameters, MARKERS)}

        fig, ax = plt.subplots(figsize=figsize)
        fig.tight_layout(rect=[0.0, 0.0, 0.76, 1.0])

        for rec in records:
            ax.scatter(
                rec['mu_star'], rec['ST'],
                marker=marker_map[rec['parameter']],
                color=colour_for_ph(rec['ph']),
                s=55, linewidths=0.6, edgecolors='black'
            )

        ax.plot(x_line, y_line, color='grey', linewidth=1)
        ax.text(
            stat_pos[0], stat_pos[1],
            f'r = {r_val:.2f}\np = {p_val:.3g}',
            transform=ax.transAxes, ha='left', va='top', fontsize=15
        )

        # μ★ axis label in default font
        ax.set_xlabel('μ★', fontproperties=default_font, fontweight='normal')
        # y-axis label as S_T (math)
        ax.set_ylabel(r'$S_T$')
        ax.grid(True, lw=0.3, alpha=0.4)

        # Legends
        ph_levels = sorted({r['ph'] for r in records}, key=lambda x: float(x))
        ph_handles = [
            Line2D([0], [0], marker='o', color=colour_for_ph(ph),
                   linestyle='None', label=f'pH {ph}')
            for ph in ph_levels
        ]
        leg_ph = ax.legend(
            handles=ph_handles,
            bbox_to_anchor=(1.02, 0.85), loc='upper left',
            fontsize=LEGEND_FONTSIZE, title_fontsize=LEGEND_TITLE_FONTSIZE,
            markerscale=LEGEND_MARKERSCALE, borderpad=LEGEND_BORDERPAD,
            labelspacing=LEGEND_LABELSPACING, handlelength=LEGEND_HANDLELEN,
            handletextpad=LEGEND_HANDLETEXTPAD, frameon=True
        )
        ax.add_artist(leg_ph)

        # Parameter legend with pretty italic labels
        param_handles = []
        param_labels = []
        for p in parameters:
            param_handles.append(
                Line2D([0], [0], marker=marker_map[p], color='k', linestyle='None', label=p)
            )
            param_labels.append(PARAM_LABEL_MAP.get(p, p))
        ax.legend(
            handles=param_handles, labels=param_labels, title='Parameter',
            bbox_to_anchor=(1.02, 0.45), loc='upper left',
            fontsize=LEGEND_FONTSIZE, title_fontsize=LEGEND_TITLE_FONTSIZE,
            markerscale=LEGEND_MARKERSCALE, borderpad=LEGEND_BORDERPAD,
            labelspacing=LEGEND_LABELSPACING, handlelength=LEGEND_HANDLELEN,
            handletextpad=LEGEND_HANDLETEXTPAD, frameon=True
        )

        out_path = out_dir / f'{temp}_{material.lower()}_mu_star_vs_ST.pdf'
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0.2)
        plt.close(fig)
        print(f'Saved {out_path}')

def main() -> None:
    p = argparse.ArgumentParser(description='Generate μ★–ST Sobol plots')
    p.add_argument('--dir', '-d', default='.')
    p.add_argument('--out', '-o', default='.')
    p.add_argument('--figsize', nargs=2, type=float, default=(15, 12))
    p.add_argument('--stat_pos', nargs=2, type=float, default=(0.02, 0.98))
    p.add_argument('--dpi', type=int, default=500)
    args = p.parse_args()

    create_plots(Path(args.dir).expanduser().resolve(),
                 Path(args.out).expanduser().resolve(),
                 tuple(args.figsize),
                 tuple(args.stat_pos),
                 args.dpi)

if __name__ == '__main__':
    main()
