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

### 1. Clone the repository
```bash
git clone https://github.com/Yibin-Li02/Final-Thesis.git
cd Final-Thesis
```

### 2. Create a Python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
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
cd Scripts
python example_plot.py
```

### Sensitivity Analysis (`sensitivity.py`)
The core sensitivity analysis is implemented in:
```
virtual_ecosystem/sensitivity.py
```

Run it with:
```bash
python -m virtual_ecosystem.sensitivity
```

Optionally, specify output directories for data and plots:
```bash
python -m virtual_ecosystem.sensitivity --output_dir ../Result_data --plot_dir ../Result_plots
```

*(Adjust flags depending on script implementation.)*

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
