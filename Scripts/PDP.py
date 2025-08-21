#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDP 绘图：25°C 下，不同 pH（文件名 25-xx.npz）
Fungi = 实线 (SEF), Bacteria = 虚线 (SEB)
reference_cue_logit (RCL) = X[:, 1]
"""

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

# ====== 用户配置 ======
NPZ_DIR = Path("/home/yibin-li/ve/virtual_ecosystem")   # 存放 25-xx.npz 的目录
OUT_PDF = "PDP_25C_allpH.pdf"

BINS = 100  # reference_cue_logit 分多少箱
# =====================

# 颜色列表（可自行增加）
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# 扫描所有 25-xx.npz
npz_files = sorted(NPZ_DIR.glob("25-*.npz"))
if not npz_files:
    raise FileNotFoundError(f"{NPZ_DIR} 中未找到 25-*.npz 文件")

def pH_from_name(fname: str):
    """25-35.npz → 3.5"""
    m = re.search(r"25-(\d+)", fname)
    if not m:
        raise ValueError(f"文件名格式错误: {fname}")
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
    bacteria = Y[:, 2]
    fungi = Y[:, 4]

    # 分箱取平均
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

    # 绘图（Fungi = 实线, Bacteria = 虚线）
    plt.plot(bin_centers, f_means, color=color, lw=2)           # SEF
    plt.plot(bin_centers, b_means, color=color, ls="--", lw=2)  # SEB

# 双图例
ph_handles = [mpatches.Patch(color=ph_color_map[ph], label=f"pH {ph}")
              for ph in sorted(ph_color_map)]
style_handles = [
    mlines.Line2D([], [], color="black", lw=2, label="SEF"),       # fungi = solid
    mlines.Line2D([], [], color="black", lw=2, ls="--", label="SEB")  # bacteria = dashed
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

# ---- X/Y 轴标题：将 x 轴改名为 RCL ----
plt.xlabel("RCL", fontstyle="italic")

plt.ylabel("Mean content")
plt.xlim(bins.min(), bins.max())
plt.xticks(np.linspace(bins.min(), bins.max(), 5))

plt.tight_layout()
plt.savefig(OUT_PDF, format="pdf")
plt.show()

print(f"✅ 图已保存：{OUT_PDF}")
