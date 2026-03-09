from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from src.analysis.geometry import convex_hull_area_km2, haversine_km, ratio_within_bbox
from src.simulation.config_loader import ScenarioConfig


def nearest_metric_row(metrics_df: pd.DataFrame, target_hour: int) -> pd.Series:
    index = (metrics_df["hours_since_release"] - float(target_hour)).abs().idxmin()
    return metrics_df.loc[index]


def calculate_metrics(dataset: xr.Dataset, scenario: ScenarioConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    times = pd.to_datetime(dataset["time"].values)
    lon = dataset["lon"].values
    lat = dataset["lat"].values
    z = dataset["z"].values if "z" in dataset else np.zeros_like(lon)
    rows: list[dict[str, Any]] = []

    for time_index, timestamp in enumerate(times):
        lon_slice = np.asarray(lon[:, time_index], dtype=float)
        lat_slice = np.asarray(lat[:, time_index], dtype=float)
        z_slice = np.asarray(z[:, time_index], dtype=float)
        valid = np.isfinite(lon_slice) & np.isfinite(lat_slice)
        lon_valid = lon_slice[valid]
        lat_valid = lat_slice[valid]
        z_valid = z_slice[valid]

        if lon_valid.size == 0:
            rows.append(
                {
                    "scenario_name": scenario.scenario_name,
                    "timestamp": timestamp,
                    "hours_since_release": float((timestamp - times[0]).total_seconds() / 3600.0),
                    "particle_count": 0,
                    "max_distance_km": np.nan,
                    "mean_distance_km": np.nan,
                    "centroid_lon": np.nan,
                    "centroid_lat": np.nan,
                    "centroid_distance_km": np.nan,
                    "convex_hull_area_km2": np.nan,
                    "dispersion_radius_km": np.nan,
                    "p95_radius_km": np.nan,
                    "reached_target_radius_ratio": np.nan,
                    "interest_area_ratio": np.nan,
                    "surface_retention_ratio": np.nan,
                }
            )
            continue

        distances = haversine_km(scenario.release_lat, scenario.release_lon, lat_valid, lon_valid)
        centroid_lon = float(np.mean(lon_valid))
        centroid_lat = float(np.mean(lat_valid))
        centroid_distance = float(haversine_km(scenario.release_lat, scenario.release_lon, centroid_lat, centroid_lon))
        hull_area = convex_hull_area_km2(lon_valid, lat_valid, scenario.release_lon, scenario.release_lat)

        rows.append(
            {
                "scenario_name": scenario.scenario_name,
                "timestamp": timestamp,
                "hours_since_release": float((timestamp - times[0]).total_seconds() / 3600.0),
                "particle_count": int(lon_valid.size),
                "max_distance_km": float(np.max(distances)),
                "mean_distance_km": float(np.mean(distances)),
                "centroid_lon": centroid_lon,
                "centroid_lat": centroid_lat,
                "centroid_distance_km": centroid_distance,
                "convex_hull_area_km2": float(hull_area),
                "dispersion_radius_km": float(np.mean(distances)),
                "p95_radius_km": float(np.percentile(distances, 95)),
                "reached_target_radius_ratio": float(np.mean(distances >= scenario.target_radius_km)),
                "interest_area_ratio": ratio_within_bbox(lon_valid, lat_valid, scenario.interest_area_bbox),
                "surface_retention_ratio": float(np.mean(np.abs(z_valid) <= 0.1)),
            }
        )

    metrics_df = pd.DataFrame(rows)
    centroid_df = metrics_df[
        ["scenario_name", "timestamp", "hours_since_release", "centroid_lon", "centroid_lat", "centroid_distance_km"]
    ].copy()

    summary_row: dict[str, Any] = {
        "scenario_name": scenario.scenario_name,
        "output_name": scenario.output_name,
        "polymer_type": scenario.polymer_type,
        "salinity_psu": scenario.salinity_psu,
        "oil_type": scenario.oil_type,
        "parameter_source": scenario.parameter_source,
        "temperature_c": scenario.temperature_c,
        "use_demo_data": scenario.use_demo_data,
        "release_time": scenario.release_time,
        "duration_hours": scenario.duration_hours,
        "particles": scenario.particles,
        "release_lat": scenario.release_lat,
        "release_lon": scenario.release_lon,
        "release_radius_m": scenario.release_radius_m,
        "terminal_velocity": scenario.terminal_velocity,
        "wind_drift_factor": scenario.wind_drift_factor,
        "current_drift_factor": scenario.current_drift_factor,
        "target_radius_km": scenario.target_radius_km,
        "interest_area_bbox": str(scenario.interest_area_bbox),
        "final_max_distance_km": float(metrics_df["max_distance_km"].iloc[-1]),
        "final_mean_distance_km": float(metrics_df["mean_distance_km"].iloc[-1]),
        "final_centroid_distance_km": float(metrics_df["centroid_distance_km"].iloc[-1]),
        "final_convex_hull_area_km2": float(metrics_df["convex_hull_area_km2"].iloc[-1]),
        "final_surface_retention_ratio": float(metrics_df["surface_retention_ratio"].iloc[-1]),
        "final_reached_target_radius_ratio": float(metrics_df["reached_target_radius_ratio"].iloc[-1]),
    }

    for hour in scenario.snapshots_hours:
        row = nearest_metric_row(metrics_df, hour)
        prefix = f"h{hour}"
        summary_row[f"{prefix}_actual_hour"] = float(row["hours_since_release"])
        summary_row[f"{prefix}_max_distance_km"] = float(row["max_distance_km"])
        summary_row[f"{prefix}_mean_distance_km"] = float(row["mean_distance_km"])
        summary_row[f"{prefix}_centroid_distance_km"] = float(row["centroid_distance_km"])
        summary_row[f"{prefix}_convex_hull_area_km2"] = float(row["convex_hull_area_km2"])
        summary_row[f"{prefix}_reached_target_radius_ratio"] = float(row["reached_target_radius_ratio"])

    summary_df = pd.DataFrame([summary_row])
    return metrics_df, summary_df, centroid_df
