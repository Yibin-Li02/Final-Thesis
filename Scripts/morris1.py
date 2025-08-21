#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust μ★–σ scatter plot generator
• searches current folder (*.xlsx)
• keeps pH 3.5 / 4.5 / 6.5 / 8   (drops 5.5)
• one PDF per (temperature × output)  to OUTPUT_DIR
• colour = pH  •  marker = parameter  •  σ/μ★ lines (1, 0.5, 0.1)
"""

import re, sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

# ============ CONFIG ============ #
DATA_DIR   = Path("/home/yibin-li/ve")                # folder with the eight Excel files
OUTPUT_DIR = Path("/home/yibin-li/ve")          # <— all PDFs will be written here
TEMPS      = [25, 27]                 # which temperatures to plot
PH_KEEP    = ["3.5", "4.5", "6.5", "8"]   # pH 5.5 is excluded
# pH → colour (feel free to edit)
PH_COLOR   = {"3.5":"#1f77b4", "4.5":"#17becf",
              "6.5":"#2ca02c", "8":"#ff7f0e"}
# enough marker shapes for any #parameters
MARKERS    = ["o","s","^","D","v","P","X","<",">","h",
              "8","H","+","x","*","1","2","3","4"]
# all column aliases that should become "mu" or "sig"
ALIAS = {
    "mu_star":"mu", "mu*":"mu", "mu_star_mean":"mu",
    "mu":"mu", "muave":"mu",
    "sigma":"sig", "sigma_tot":"sig", "sigma*":"sig",
    "sig":"sig", "sd":"sig",
    "parameter":"param", "param":"param"
}
# ================================= #

OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ---------- 1) LOAD ALL XLSX ---------- #
rows = []
print(f"Scanning  .xlsx  in {DATA_DIR.resolve()}\n")
for xfile in DATA_DIR.glob("*.xls*"):
    m = re.match(r"(\d+)(.*)", xfile.stem)
    if not m:
        print(f"  skip  {xfile.name}  (file name must start with digits)")
        continue
    temp = int(m.group(1))
    if temp not in TEMPS:
        print(f"  skip  {xfile.name}  (T={temp} not in {TEMPS})")
        continue
    output = (m.group(2).strip() or "unknown").lower()
    print(f"→ {xfile.name}  →  output='{output}'")

    xls = pd.ExcelFile(xfile)
    for sh in xls.sheet_names:
        ph = sh.strip()
        if ph not in PH_KEEP:
            continue
        df = pd.read_excel(xls, sh).rename(str.lower, axis=1)
        df = df.rename(columns=lambda c: ALIAS.get(c, c))      # unify names
        df = df.apply(pd.to_numeric, errors="ignore")          # force numbers
        if not {"param","mu","sig"}.issubset(df.columns):
            print(f"   · skip sheet '{sh}' (missing mu/sig/param)")
            continue
        valid = df[["param","mu","sig"]].dropna()
        if valid.empty:
            print(f"   · sheet '{sh}' has zero valid rows")
            continue
        for _, r in valid.iterrows():
            rows.append(dict(T=temp, pH=ph, output=output,
                             param=str(r["param"]),
                             mu=float(r["mu"]),
                             sig=float(r["sig"])))
print()

data = pd.DataFrame(rows)
if data.empty:
    sys.exit("❌  No valid data rows found – check Excel column names/content.")

params = sorted(data.param.unique(), key=str)
marker_map = {p: MARKERS[i % len(MARKERS)] for i, p in enumerate(params)}

# ---------- 2) PLOT & SAVE PDFs ---------- #
written = []
for temp in TEMPS:
    temp_df = data[data.T == temp]
    for out, sub in temp_df.groupby("output"):
        if sub.empty:
            continue
        pdf_path = OUTPUT_DIR / f"morris_scatter_{temp}C_{out}.pdf"
        with PdfPages(pdf_path) as pdf:
            plt.figure(figsize=(6, 5))
            # scatter
            for ph, g1 in sub.groupby("pH"):
                for prm, g2 in g1.groupby("param"):
                    plt.scatter(g2.mu, g2.sig,
                                marker=marker_map[prm], s=70,
                                color=PH_COLOR[ph], edgecolor="black",
                                label=f"{prm}  pH {ph}")
            # σ/μ★ guide lines
            xmax = sub.mu.max()*1.05
            for k, style in zip([1, 0.5, 0.1],
                                ['solid','dashed',(0,(5,5))]):
                plt.plot([0, xmax], [0, k*xmax],
                         ls=style, lw=1.2, color="black")
                plt.text(xmax*0.98, k*xmax*1.02,
                         f"σ/μ★={k}", ha="right", va="bottom", fontsize=8)
            plt.xlabel("μ★")
            plt.ylabel("σ")
            plt.title(f"{out.capitalize()}  ({temp} °C)")
            # unique legend
            h, l = plt.gca().get_legend_handles_labels()
            uniq = dict(zip(l, h))
            plt.legend(uniq.values(), uniq.keys(), fontsize=7,
                       bbox_to_anchor=(1.02, 1), loc="upper left")
            plt.tight_layout()
            pdf.savefig(); plt.close()
        written.append(pdf_path)

print("✅  PDFs written to:", OUTPUT_DIR.resolve())
for p in written:
    print("   •", p.name)
