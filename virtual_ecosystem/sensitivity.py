#!/usr/bin/env python


from __future__ import annotations

import argparse
import multiprocessing as mp
import pathlib
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import xarray as xr
from SALib.sample import morris as morris_sample
from SALib.sample import saltelli
from SALib.analyze import morris as morris_analyse
from SALib.analyze import sobol as sobol_analyse
from tqdm import tqdm

# ─────────────────────────── virtual_ecosystem entry point ──────────────────
from virtual_ecosystem.main import ve_run

# ─────────────────────── 1 ▸ parameter bounds (EDIT) ────────────────────────
# Exact attribute names from SoilConsts
PARAM_BOUNDS: Dict[str, Tuple[float, float]] = {
    "logit_cue_with_temperature": (-0.058, -0.021),
    "reference_cue_logit":        (-0.169,  0.359),
    "lowest_optimal_pH_microbes": (4.0,     5.0),
    "min_pH_microbes":            (2.0,     3.0),
    "highest_optimal_pH_microbes":(7.0,     8.0),
    "max_pH_microbes":            (10.5,    11.5),
}

PARAM_NAMES  = list(PARAM_BOUNDS.keys())

OUTPUT_NAMES = [
    "soil_c_pool_maom",
    "soil_c_pool_pom",
    "soil_enzyme_pom_bacteria",
    "soil_enzyme_pom_fungi",
]
NETCDF_FILE = "final_state.nc"

# ───────── helper: scalar value from DataArray ────────────

def _to_scalar(arr: xr.DataArray) -> float:
    """Return domain‑mean final‑time value as a scalar float."""
    if "time" in arr.dims:
        arr = arr.isel(time=-1)
    return float(arr.mean(skipna=True).values)

# ───────── worker executed in its own process ─────────────

def _one_run(i: int, cfg_dir: pathlib.Path,
             pvals: Dict[str, float], out_dir: pathlib.Path):
    """Run one VE realisation and return the outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)

    overrides = {
        "soil": {"constants": {"SoilConsts": pvals}},
        "core": {"data_output_options": {
            "out_path": str(out_dir),
            "save_initial_state": False,
            "save_continuous_data": False,
        }},
    }

    ve_run(cfg_paths=[cfg_dir], override_params=overrides,
           logfile=out_dir / "ve.log")

    with xr.open_dataset(out_dir / NETCDF_FILE) as ds:
        y = np.asarray([_to_scalar(ds[v]) for v in OUTPUT_NAMES], dtype=float)
    return i, y


def _one_run_wrap(t):  # helper for multiprocessing.Pool
    return _one_run(*t)

# ───────── main driver ────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config_dir", type=pathlib.Path, required=True)
    ap.add_argument("--out_base",   type=pathlib.Path, default=pathlib.Path("SA_OUTPUT"))
    ap.add_argument("--morris_trajectories", type=int, default=100)
    ap.add_argument("--sobol_base",          type=int, default=1024)
    ap.add_argument("--cpu", type=int, default=max(mp.cpu_count() - 1, 1))
    args = ap.parse_args()

    runs_dir, res_dir = args.out_base / "SA_RUNS", args.out_base / "SA_RESULTS"
    runs_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    problem = {
        "num_vars": len(PARAM_NAMES),
        "names": PARAM_NAMES,
        "bounds": [list(PARAM_BOUNDS[p]) for p in PARAM_NAMES],
    }

    # ────────── 2 ▸ design matrices ──────────
    X_mor = morris_sample.sample(problem, N=args.morris_trajectories, num_levels=8)
    X_sob = saltelli.sample(problem, N=args.sobol_base, calc_second_order=True)
    X = np.vstack((X_mor, X_sob))

    # ────────── 3 ▸ model evaluations ─────────
    Y = np.empty((len(X), len(OUTPUT_NAMES)))

    jobs = [
        (i, args.config_dir, dict(zip(PARAM_NAMES, row)), runs_dir / f"run_{i:06d}")
        for i, row in enumerate(X)
    ]

    ctx = mp.get_context("fork")
    with ctx.Pool(processes=args.cpu, maxtasksperchild=1) as pool:
        for idx, y in tqdm(
            pool.imap_unordered(_one_run_wrap, jobs, chunksize=1),
            total=len(X), desc="Running ensemble",
        ):
            Y[idx] = y

    np.savez(res_dir / "raw_XY.npz", X=X, Y=Y)
    Y_m, Y_s = Y[: len(X_mor)], Y[len(X_mor) :]

    # ────────── 4 ▸ sensitivity analyses ──────
    for j, var in enumerate(OUTPUT_NAMES):
        m = morris_analyse.analyze(
            problem,
            X_mor,
            Y_m[:, j],
            print_to_console=False,
        )

        # Sobol with 95 % bootstrap CIs (1000 resamples)
        s = sobol_analyse.analyze(
            problem,
            Y_s[:, j],
            print_to_console=False,
            calc_second_order=True,
            conf_level=0.95,
        )

        pd.DataFrame(
            {
                "parameter": PARAM_NAMES,
                # Morris
                "mu_star": m["mu_star"],
                "sigma": m["sigma"],
                # Sobol first‑ and total‑order
                "S1": s["S1"],
                "S1_conf": s["S1_conf"],
                "ST": s["ST"],
                "ST_conf": s["ST_conf"],
            }
        ).to_csv(res_dir / f"combined_{var}.csv", index=False)

    print(f"✓ Finished — runs in {runs_dir} | results in {res_dir}")


if __name__ == "__main__":
    main()
