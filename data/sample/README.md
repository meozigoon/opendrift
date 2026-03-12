This directory intentionally does not bundle external oceanographic datasets.

Use one of the following approaches:

1. Real-data mode

- Provide your own current and wind NetCDF files through the Streamlit UI or CLI config.
- Current NetCDF must expose eastward/northward current components.
- Wind NetCDF must expose x_wind and y_wind components.

2. Demo mode

- Run `python scripts/generate_demo_inputs.py --output-dir data/sample/generated`.
- Or use the included demo scenario JSON files, which auto-generate synthetic NetCDF inputs at runtime.

The demo mode is synthetic and only exists to verify code paths, UI wiring, and smoke tests.
