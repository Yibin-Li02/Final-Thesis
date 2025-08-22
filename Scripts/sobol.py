#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
import warnings
from pathlib import Path 

# ---------- SUPPRESS WARNINGS ----------
warnings.filterwarnings("ignore", message="Glyph .* missing from font")
# ---------------------------------------

# ---------- GLOBAL FONT SETTINGS ----------
plt.rcParams.update({
    'font.family': 'TeX Gyre Termes',
    'font.size': 20,
    'axes.titlesize': 20,
    'axes.labelsize': 20,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'legend.fontsize': 20,
    'legend.title_fontsize': 20,
    'mathtext.fontset': 'stix',
    'mathtext.default': 'it'
})
# ------------------------------------------
# ==== Defaults relative to this file ====
BASE_DIR = Path(__file__).resolve().parent         # .../Script
DEFAULT_DATA_DIR = BASE_DIR.parent / "Result_data"       # sibling: .../Excel
DEFAULT_OUT_DIR  = BASE_DIR / "Result_plots"              # save PDFs here
DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
# ========================================
# ========== Config (edit if needed) ========== #
TEMPERATURES = [25, 27]
PH_LIST = ["3.5", "4.5", "6.5", "5.5", "8"]

# Output display names (no italics) and order
#  25pom.xlsx -> "pom", 25maom.xlsx -> "maom", 25bacteria.xlsx -> "bacteria", 25fungi.xlsx -> "fungi"
OUTPUT_LABELS = {
    "pom": "POM pool",
    "maom": "MAOM pool",
    "bacteria": "SEB",
    "fungi": "SEF",
}
OUTPUT_ORDER_KEYS = ["pom", "maom", "bacteria", "fungi"]  # display order

COLOR_PALETTE = "rocket"

# Raw parameter order (drives x positions)
PARAM_ORDER = [
    "logit_cue_with_temperature",
    "reference_cue_logit",
    "lowest_optimal_pH_microbes",
    "min_pH_microbes",
    "highest_optimal_pH_microbes",
    "max_pH_microbes",
]

# Pretty x-axis tick labels (plain text, no italics)
# Use simple ASCII or Unicode where convenient (e.g., β and subscript t).
PARAM_LABELS = {
    "reference_cue_logit":           r"$\mathit{RCL}$",               # italic
    "logit_cue_with_temperature":    r"$\beta_T$",          # beta with italic T subscript
    "min_pH_microbes":               r"$\mathit{pH}_{\min}$",          # upright pH
    "lowest_optimal_pH_microbes":    r"$\mathit{pH}_{\mathrm{low}}$",
    "highest_optimal_pH_microbes":   r"$\mathit{pH}_{\mathrm{high}}$",
    "max_pH_microbes":               r"$\mathit{pH}_{\max}$",
}

SHAPE_CYCLE = ["o", "s", "^", "D", "v", "P", "X", "*", "h", "8", "<", ">", "H", "d"]
FIGSIZE = (14, 6)
DPI = 300
OFFSET_WIDTH = 0.15
# =========================================== #

def load_data(path: str = ".") -> pd.DataFrame:
    frames = []
    for temp in TEMPERATURES:
        for fname in os.listdir(path):
            if not fname.lower().endswith(".xlsx"):
                continue
            if not fname.startswith(str(temp)):
                continue
            # derive Microbe key from file name: e.g., "25pom.xlsx" -> "pom"
            microbe = fname[len(str(temp)):-5].lower()
            file_path = os.path.join(path, fname)
            for ph in PH_LIST:
                try:
                    df = pd.read_excel(file_path, sheet_name=ph)
                except ValueError:
                    continue
                df = df.assign(Temperature=temp, Microbe=microbe, pH=ph)
                frames.append(
                    df[
                        [
                            "parameter",
                            "S1", "S1_conf",
                            "ST", "ST_conf",
                            "Temperature", "Microbe", "pH"
                        ]
                    ]
                )
    if not frames:
        raise RuntimeError("No data loaded – check file names / sheets.")
    data = pd.concat(frames, ignore_index=True)
    data["parameter"] = pd.Categorical(
        data["parameter"], categories=PARAM_ORDER, ordered=True
    )
    return data

def prepare_mappings(data: pd.DataFrame):
    present = list(data["Microbe"].unique())
    # enforce desired output order first, then append any extras
    outputs = [k for k in OUTPUT_ORDER_KEYS if k in present] + \
              [k for k in present if k not in OUTPUT_ORDER_KEYS]

    shape_map = {out: SHAPE_CYCLE[i % len(SHAPE_CYCLE)] for i, out in enumerate(outputs)}
    colors = dict(zip(PH_LIST, sns.color_palette(COLOR_PALETTE, len(PH_LIST))))
    n_out = len(outputs)
    offsets = {out: (i - (n_out - 1) / 2) * OFFSET_WIDTH for i, out in enumerate(outputs)}
    return outputs, shape_map, colors, offsets

def make_legends(ax, colors, shape_map):
    # pH legend
    ph_handles = [
        Line2D([0], [0], marker="o", color=col, linestyle="",
               markersize=6, label=f"pH {ph}")
        for ph, col in colors.items()
    ]
    leg1 = ax.legend(handles=ph_handles,
                     loc="upper left", bbox_to_anchor=(1.02, 1.0),
                     fontsize=20, title_fontsize=20)
    ax.add_artist(leg1)

    # Output legend with custom labels (no italics)
    out_handles = []
    for out_key, marker in shape_map.items():
        label = OUTPUT_LABELS.get(out_key, out_key)
        out_handles.append(Line2D([0], [0], marker=marker, color="black",
                                  linestyle="", markersize=6, label=label))
    ax.legend(out_handles, [h.get_label() for h in out_handles], title="Output",
              loc="upper left", bbox_to_anchor=(1.02, 0.45),
              fontsize=20, title_fontsize=20)

def plot_temperature(df: pd.DataFrame, idx: str, temp: int,
                     outputs, shape_map, colors, offsets):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for _, row in df.iterrows():
        param_idx = PARAM_ORDER.index(row["parameter"])
        x = param_idx + offsets[row["Microbe"]]
        ax.errorbar(
            x,
            row[idx],
            yerr=row[f"{idx}_conf"],
            fmt=shape_map[row["Microbe"]],
            markersize=6,
            capsize=3,
            linestyle="none",
            color=colors[row["pH"]],
            markeredgecolor="black",
        )

    # X ticks: custom pretty labels (plain text)
    ax.set_xticks(range(len(PARAM_ORDER)))
    pretty_xticks = [PARAM_LABELS.get(p, p) for p in PARAM_ORDER]
    ax.set_xticklabels(pretty_xticks, rotation=0)

    ax.set_xlabel("Parameter")
    ax.set_ylabel(f"{idx} index (95% CI)")
    ax.axhline(0, color="grey", lw=0.8, ls="--")
    make_legends(ax, colors, shape_map)
    fig.tight_layout()
    out = f"sobol_{idx}_{temp}C.pdf"
    fig.savefig(out, format="pdf", dpi=DPI)
    print(f"✔ Saved {out}")

def main():
    data = load_data()
    outputs, shape_map, colors, offsets = prepare_mappings(data)
    for temp in TEMPERATURES:
        subset = data[data["Temperature"] == temp]
        for idx in ("S1", "ST"):
            plot_temperature(subset, idx, temp,
                             outputs, shape_map, colors, offsets)

if __name__ == "__main__":
    main()
