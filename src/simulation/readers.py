from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from opendrift.readers import reader_netCDF_CF_generic

from src.simulation.config_loader import ScenarioConfig


def create_demo_inputs(output_dir: Path, scenario: ScenarioConfig) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    current_path = output_dir / "demo_current.nc"
    wind_path = output_dir / "demo_wind.nc"

    time = pd.date_range(scenario.release_datetime, periods=scenario.duration_hours + 2, freq="1h")
    span = max(1.5, min(4.0, 1.0 + scenario.duration_hours / 72.0))
    lat = np.linspace(scenario.release_lat - span, scenario.release_lat + span, 31)
    lon = np.linspace(scenario.release_lon - span, scenario.release_lon + span, 31)
    lon_grid, lat_grid = np.meshgrid(lon, lat, indexing="xy")
    phase = np.arange(len(time), dtype=float)[:, None, None]

    current_u = (
        0.05
        + 0.01 * np.sin(np.radians(lon_grid - scenario.release_lon) * 8.0)[None, :, :]
        + 0.004 * np.sin(phase / 4.0)
    ).astype("float32")
    current_v = (
        0.02
        + 0.008 * np.cos(np.radians(lat_grid - scenario.release_lat) * 8.0)[None, :, :]
        + 0.003 * np.cos(phase / 5.0)
    ).astype("float32")
    wind_u = (
        1.4
        + 0.25 * np.sin(phase / 3.0)
        + 0.15 * np.cos(np.radians(lon_grid - scenario.release_lon) * 4.0)[None, :, :]
    ).astype("float32")
    wind_v = (
        0.7
        + 0.20 * np.cos(phase / 3.5)
        + 0.12 * np.sin(np.radians(lat_grid - scenario.release_lat) * 4.0)[None, :, :]
    ).astype("float32")

    coords = {
        "time": ("time", time),
        "lat": ("lat", lat, {"standard_name": "latitude", "units": "degrees_north"}),
        "lon": ("lon", lon, {"standard_name": "longitude", "units": "degrees_east"}),
    }

    current_ds = xr.Dataset(
        {
            "uo": (
                ("time", "lat", "lon"),
                current_u,
                {"standard_name": "eastward_sea_water_velocity", "units": "m s-1"},
            ),
            "vo": (
                ("time", "lat", "lon"),
                current_v,
                {"standard_name": "northward_sea_water_velocity", "units": "m s-1"},
            ),
        },
        coords=coords,
        attrs={"synthetic_demo": "true", "description": "Synthetic current field for PlastDrift demo mode."},
    )
    current_ds.to_netcdf(current_path)

    wind_ds = xr.Dataset(
        {
            "uwnd": (("time", "lat", "lon"), wind_u, {"standard_name": "x_wind", "units": "m s-1"}),
            "vwnd": (("time", "lat", "lon"), wind_v, {"standard_name": "y_wind", "units": "m s-1"}),
        },
        coords=coords,
        attrs={"synthetic_demo": "true", "description": "Synthetic wind field for PlastDrift demo mode."},
    )
    wind_ds.to_netcdf(wind_path)
    return current_path, wind_path


def prepare_input_paths(scenario: ScenarioConfig, output_dir: Path) -> tuple[Path, Path, list[str]]:
    notes: list[str] = []
    if scenario.use_demo_data:
        current_path, wind_path = create_demo_inputs(output_dir / "demo_inputs", scenario)
        notes.append("use_demo_data=true 이므로 합성 데모 입력장을 생성했습니다.")
        return current_path, wind_path, notes
    if scenario.current_path is None or scenario.wind_path is None:
        raise ValueError("실제 실행에는 해류 경로와 바람 경로가 모두 필요합니다.")
    return Path(scenario.current_path), Path(scenario.wind_path), notes


def build_readers(current_path: Path, wind_path: Path):
    current_reader = reader_netCDF_CF_generic.Reader(str(current_path))
    wind_reader = reader_netCDF_CF_generic.Reader(str(wind_path))
    return current_reader, wind_reader
