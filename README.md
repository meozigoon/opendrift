# OpenDrift PlastDrift Surface Research Web Project

## Purpose
This project predicts and analyzes the surface transport range of oil-adsorbed microplastic particles with OpenDrift `PlastDrift`.

The research target is not free oil slick weathering. The project is intentionally centered on `PlastDrift` and a semi-empirical parameter mapping workflow:

- Polymer types: `PE`, `PP`, `PET`
- Salinity comparison: `33 psu`, `40 psu`
- Oil comparison: `diesel`, `kerosene`
- Fixed temperature metadata: `25 C`
- Surface-only baseline:
  - `vertical_mixing = False`
  - `vertical_advection = False`
  - `stokes_drift = False` by default
  - `z = 0` release

Polymer/oil/salinity differences are represented by scenario-specific transport parameters such as:

- `terminal_velocity`
- `wind_drift_factor`
- `current_drift_factor`

This allows future laboratory calibration results to be plugged into the model without pretending to compute direct oil-plastic chemistry.

## Project structure
```text
.
├── README.md
├── requirements.txt
├── environment.yml
├── app.py
├── main.py
├── configs
│   ├── defaults.yaml
│   └── scenarios
│       ├── pe_33psu_diesel.json
│       ├── pp_33psu_diesel.json
│       └── pet_40psu_kerosene.json
├── data
│   ├── input
│   │   └── uploads
│   ├── output
│   └── sample
│       └── README.md
├── reports
│   ├── figures
│   └── summaries
├── scripts
│   ├── build_report.py
│   ├── generate_demo_inputs.py
│   ├── make_animation.py
│   ├── run_batch.py
│   └── run_scenario.py
├── src
│   ├── __init__.py
│   ├── analysis
│   ├── simulation
│   ├── ui
│   └── utils
└── tests
    ├── test_config_loader.py
    ├── test_metrics.py
    ├── test_runner_smoke.py
    └── test_validation.py
```

## Installation

### pip
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### conda
```bash
conda env create -f environment.yml
conda activate plastdrift-surface-web
```

## Required input data format

### Real-data mode
You must provide:

- one current NetCDF
- one wind NetCDF

Expected CF-style content:

- Current file:
  - eastward current component
  - northward current component
  - `time`, `lat`, `lon` coordinates
- Wind file:
  - `x_wind`
  - `y_wind`
  - `time`, `lat`, `lon` coordinates

The app validates these before running.

### Demo mode
No external forcing file is bundled. Demo mode auto-generates synthetic NetCDF inputs and clearly labels them as synthetic.

Demo mode exists only for:

- code-path verification
- UI testing
- smoke tests
- local demonstration without external data

## Web app
```bash
streamlit run app.py
```

Web features:

- scenario input
- saved scenario load/save
- local file upload or file path input
- simulation launch
- stage-based run status
- result maps, plots, snapshots, GIF preview
- CSV/PNG/GIF/NetCDF/ZIP downloads
- multiple scenario comparison view
- log and manifest inspection

## CLI

### Single scenario
```bash
python main.py --config configs/scenarios/pe_33psu_diesel.json
```

### Validate only
```bash
python main.py --config configs/scenarios/pe_33psu_diesel.json --validate-only
```

### Batch run
```bash
python scripts/run_batch.py --dir configs/scenarios
```

### Rebuild animation
```bash
python scripts/make_animation.py --result-dir data/output/pe_33psu_diesel_surface
```

### Rebuild report
```bash
python scripts/build_report.py --result-dir data/output/pe_33psu_diesel_surface
```

### Generate demo NetCDF files
```bash
python scripts/generate_demo_inputs.py --output-dir data/sample/generated
```

## Output structure
Each run creates a result directory under `data/output/<scenario_name>/` or a timestamped variant.

Expected outputs:

- `result.nc`
- `summary.csv`
- `metrics.csv`
- `centroid_trajectory.csv`
- `scenario_config_copy.json`
- `resolved_scenario.json`
- `manifest.json`
- `trajectory_map.png`
- `convex_hull_map.png`
- `snapshot_24h.png`
- `snapshot_72h.png`
- `snapshot_168h.png`
- `animation.gif`
- `comparison_plot.png`
- `centroid_distance_plot.png`
- `dispersion_area_plot.png`
- `analysis_report.md`
- `run.log`
- `results_bundle.zip`

Cross-scenario comparison outputs are stored in:

- `reports/figures/comparison_plot.png`
- `reports/summaries/scenario_comparison_summary.csv`
- `reports/summaries/scenario_comparison_report.md`

## Automatic analysis
After each simulation the project automatically computes and exports:

- maximum travel distance at 24 h, 72 h, 168 h
- mean travel distance from the release point
- centroid displacement
- centroid trajectory
- convex hull area
- dispersion radius change
- target-radius arrival ratio
- optional bbox arrival ratio
- surface retention ratio
- scenario comparison summary

## Interpretation notes

- `summary.csv` is a one-row scenario summary for reporting and comparison.
- `metrics.csv` is a time-series table for graphing and detailed post-processing.
- `trajectory_map.png` shows the release point, trajectories, centroid path, and final hull.
- `snapshot_*h.png` shows particle distributions near requested time horizons.
- `comparison_plot.png` shows distance and area time series.
- `analysis_report.md` is an auto-generated textual summary.

## Testing
```bash
python -m pytest
```

The smoke test runs a short synthetic PlastDrift simulation end-to-end.

## Known limitations

- The baseline implementation is surface-only and does not model oil weathering.
- Demo mode is synthetic and must not be interpreted as an ocean forecast.
- Real-data runs depend on the quality, grid coverage, and time range of user-supplied NetCDF forcing.
- The UI previews a release point map, but click-to-select coordinates are not implemented.
- Animation output is provided as GIF. MP4 is not generated in the current implementation.

## Extension ideas

- click-to-map release coordinate selection
- polygon-based area of interest input
- ensemble or uncertainty sweeps
- calibration workflow from experimental adsorption data
- optional MP4 export when FFmpeg is available
- richer GIS export such as GeoJSON or shapefile
- scheduled background jobs for long simulations
