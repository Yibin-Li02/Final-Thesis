# Final Thesis: Global Sensitivity Analysis with Virtual Ecosystem

## Author
**Yibin Li**  
📧 Email: yl2524@ic.ac.uk

---

## Overview
This repository contains all scripts, data, and results for my MSc thesis project, which applies **global sensitivity analysis** (GSA) to the [Virtual Ecosystem (VE)](https://virtual-ecosystem.readthedocs.io/en/latest/) model.  

The project focuses on assessing the impact of **soil temperature** and **soil pH** on model outcomes using variance-based methods (e.g., Morris and Sobol). The main analysis is performed through the `sensitivity.py` script included in the `virtual_ecosystem` package.  

---

## Repository Structure
```
Final-Thesis/
├── Scripts/                   # Utility scripts for analysis & plotting
├── Result_data/               # Output datasets from simulations
├── Result_plots/              # Figures and visualisations
├── virtual_ecosystem/         # Local copy of VE code including sensitivity.py
│   └── virtual_ecosystem/
│       └── data/              # Input NetCDF files (soil_temperature.nc, example_soil_data.nc)
└── README.md                  # Project documentation
```

---

## Setup Instructions

Install the Virtual Ecosystem model and its requirements:
```bash
pip install virtual-ecosystem
```

For more details, see the [official VE documentation](https://virtual-ecosystem.readthedocs.io/en/latest/).

---

## Running Scripts

### Scripts in `Scripts/`
The `Scripts/` folder contains helper scripts for analysis and plotting results.  
Example:
```bash
python morris.py
python morris1.py
python sobol.py
python PDP.py
python Script/combine.py --dir ../Result_data --out ./plots
```

### Sensitivity Analysis (`sensitivity.py`)
The core sensitivity analysis is implemented in:
```
virtual_ecosystem/virtual_ecosystem/sensitivity.py
```

Run it with:
```bash
OMP_NUM_THREADS=1 poetry run python sensitivity.py     --config_dir /home/yibin-li/ve/virtual_ecosystem/virtual_ecosystem/config2     --out_base   SA_OUTPUT     --morris_trajectories 30     --sobol_base 512     --cpu 12
```

*(Adjust script depending on actual conditions.)*

---

## Adjusting Soil Temperature and pH

The sensitivity analysis uses input data stored in NetCDF files inside `virtual_ecosystem/virtual_ecosystem/data/`.

- **Soil Temperature:**  
  Modify values in `soil_temperature.nc`.

- **Soil pH:**  
  Modify values in `example_soil_data.nc`.

You can edit these files with Python (`netCDF4`, `xarray`) or command-line tools (`ncdump`, `ncks`). After editing, rerun `sensitivity.py` to propagate changes through the analysis.

---

## Results
- Processed data will be saved in: `Result_data/`  
- Figures and visualisations will be saved in: `Result_plots/`

---

## License & Contributions
This repository is for academic research purposes only.  
If you wish to contribute, please fork the repo and submit a pull request.

---
