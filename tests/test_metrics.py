from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr

from src.analysis.metrics import calculate_metrics
from src.simulation.config_loader import ScenarioConfig


def _build_dataset() -> xr.Dataset:
    times = pd.date_range("2024-01-01", periods=4, freq="1h")
    lon = np.array(
        [
            [129.0, 129.01, 129.02, 129.03],
            [129.0, 129.015, 129.03, 129.045],
        ],
        dtype="float32",
    )
    lat = np.array(
        [
            [35.0, 35.005, 35.010, 35.015],
            [35.0, 35.004, 35.008, 35.012],
        ],
        dtype="float32",
    )
    z = np.zeros_like(lon, dtype="float32")
    return xr.Dataset(
        {
            "lon": (("trajectory", "time"), lon),
            "lat": (("trajectory", "time"), lat),
            "z": (("trajectory", "time"), z),
        },
        coords={"trajectory": [0, 1], "time": times},
    )


def test_calculate_metrics_returns_expected_columns() -> None:
    dataset = _build_dataset()
    scenario = ScenarioConfig(
        scenario_name="test",
        polymer_type="PE",
        salinity_psu=33,
        oil_type="diesel",
        release_lat=35.0,
        release_lon=129.0,
        release_time=datetime(2024, 1, 1).isoformat(),
        duration_hours=3,
        particles=2,
        release_radius_m=100.0,
        terminal_velocity=0.0,
        wind_drift_factor=0.03,
        current_drift_factor=1.0,
        snapshots_hours=[1, 2, 3],
    )
    metrics_df, summary_df, centroid_df = calculate_metrics(dataset, scenario)
    assert {"max_distance_km", "centroid_distance_km", "convex_hull_area_km2"} <= set(metrics_df.columns)
    assert summary_df.iloc[0]["final_max_distance_km"] > 0
    assert len(centroid_df) == 4
