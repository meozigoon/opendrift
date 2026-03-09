from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.lines import Line2D

from src.analysis.geometry import convex_hull_lonlat
from src.simulation.config_loader import ScenarioConfig

try:  # pragma: no cover
    import cartopy.crs as ccrs
except Exception:  # pragma: no cover
    ccrs = None


def _extent_from_points(lon: np.ndarray, lat: np.ndarray) -> tuple[float, float, float, float]:
    lon_min, lon_max = float(np.nanmin(lon)), float(np.nanmax(lon))
    lat_min, lat_max = float(np.nanmin(lat)), float(np.nanmax(lat))
    lon_pad = max(0.05, (lon_max - lon_min) * 0.15)
    lat_pad = max(0.05, (lat_max - lat_min) * 0.15)
    return lon_min - lon_pad, lon_max + lon_pad, lat_min - lat_pad, lat_max + lat_pad


def _make_map_figure(extent: tuple[float, float, float, float]):
    if ccrs is not None:  # pragma: no cover
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        try:
            ax.coastlines(resolution="10m", linewidth=0.6)
        except Exception:
            pass
        try:
            gridlines = ax.gridlines(draw_labels=True, linestyle=":", linewidth=0.4, alpha=0.5)
            gridlines.top_labels = False
            gridlines.right_labels = False
        except Exception:
            pass
        return fig, ax, ccrs.PlateCarree()

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.3, linestyle=":")
    return fig, ax, None


def _plot_line(ax, lon: np.ndarray, lat: np.ndarray, transform, **kwargs) -> None:
    if transform is not None:
        ax.plot(lon, lat, transform=transform, **kwargs)
    else:
        ax.plot(lon, lat, **kwargs)


def _plot_scatter(ax, lon: np.ndarray, lat: np.ndarray, transform, **kwargs) -> None:
    if transform is not None:
        ax.scatter(lon, lat, transform=transform, **kwargs)
    else:
        ax.scatter(lon, lat, **kwargs)


def _add_footer(fig, text: str) -> None:
    fig.subplots_adjust(bottom=0.16)
    fig.text(0.01, 0.02, text, ha="left", va="bottom", fontsize=8, color="#444444")


def plot_trajectory_map(dataset: xr.Dataset, scenario: ScenarioConfig, metrics_df: pd.DataFrame, output_path: Path) -> Path:
    lon = np.asarray(dataset["lon"].values, dtype=float)
    lat = np.asarray(dataset["lat"].values, dtype=float)
    extent = _extent_from_points(lon, lat)
    fig, ax, transform = _make_map_figure(extent)

    trajectory_count = min(lon.shape[0], 120)
    for index in range(trajectory_count):
        valid = np.isfinite(lon[index, :]) & np.isfinite(lat[index, :])
        if valid.any():
            _plot_line(ax, lon[index, valid], lat[index, valid], transform, color="#4C78A8", alpha=0.15, linewidth=0.8)

    final_lon = lon[:, -1]
    final_lat = lat[:, -1]
    valid_final = np.isfinite(final_lon) & np.isfinite(final_lat)
    _plot_scatter(ax, final_lon[valid_final], final_lat[valid_final], transform, s=25, c="#F58518", alpha=0.8, label="Final particles")
    _plot_scatter(ax, np.array([scenario.release_lon]), np.array([scenario.release_lat]), transform, s=90, marker="*", c="#E45756", label="Release point")

    centroid_lon = metrics_df["centroid_lon"].to_numpy(dtype=float)
    centroid_lat = metrics_df["centroid_lat"].to_numpy(dtype=float)
    valid_centroid = np.isfinite(centroid_lon) & np.isfinite(centroid_lat)
    if valid_centroid.any():
        _plot_line(ax, centroid_lon[valid_centroid], centroid_lat[valid_centroid], transform, color="#54A24B", linewidth=2.0, label="Centroid")

    hull = convex_hull_lonlat(final_lon[valid_final], final_lat[valid_final])
    if len(hull) >= 3:
        hull_lon = np.array([point[0] for point in hull], dtype=float)
        hull_lat = np.array([point[1] for point in hull], dtype=float)
        _plot_line(ax, hull_lon, hull_lat, transform, color="#B279A2", linewidth=1.8, label="Convex hull")

    ax.set_title(f"Trajectory map: {scenario.scenario_name}")
    ax.legend(loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "Footnote: blue thin lines = individual particle trajectories, orange dots = final particle positions, "
        "red star = release point, green line = centroid trajectory, purple line = final convex hull.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_convex_hull_map(dataset: xr.Dataset, scenario: ScenarioConfig, output_path: Path) -> Path:
    lon = np.asarray(dataset["lon"].values[:, -1], dtype=float)
    lat = np.asarray(dataset["lat"].values[:, -1], dtype=float)
    valid = np.isfinite(lon) & np.isfinite(lat)
    extent = _extent_from_points(lon[valid], lat[valid])
    fig, ax, transform = _make_map_figure(extent)
    _plot_scatter(ax, lon[valid], lat[valid], transform, s=25, c="#4C78A8", alpha=0.75)
    hull = convex_hull_lonlat(lon[valid], lat[valid])
    if len(hull) >= 3:
        hull_lon = np.array([point[0] for point in hull], dtype=float)
        hull_lat = np.array([point[1] for point in hull], dtype=float)
        _plot_line(ax, hull_lon, hull_lat, transform, color="#E45756", linewidth=2.0, label="Final convex hull")
    _plot_scatter(
        ax,
        np.array([scenario.release_lon]),
        np.array([scenario.release_lat]),
        transform,
        s=90,
        marker="*",
        c="#54A24B",
        label="Release point",
    )
    ax.set_title(f"Final convex hull: {scenario.scenario_name}")
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", label="Final particle positions", markerfacecolor="#4C78A8", markersize=8),
        Line2D([0], [0], color="#E45756", lw=2, label="Final convex hull"),
        Line2D([0], [0], marker="*", color="w", label="Release point", markerfacecolor="#54A24B", markersize=12),
    ]
    ax.legend(handles=legend_handles, loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "Footnote: blue dots = final timestep particle positions, red line = outer boundary from convex hull, "
        "green star = original release point.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_centroid_distance(metrics_df: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(metrics_df["hours_since_release"], metrics_df["centroid_distance_km"], label="Centroid distance", linewidth=2.0)
    ax.plot(metrics_df["hours_since_release"], metrics_df["max_distance_km"], label="Max distance", linewidth=1.6)
    ax.plot(metrics_df["hours_since_release"], metrics_df["mean_distance_km"], label="Mean distance", linewidth=1.6)
    ax.set_xlabel("Hours since release")
    ax.set_ylabel("Distance (km)")
    ax.set_title("Distance metrics over time")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    _add_footer(
        fig,
        "Footnote: centroid distance = release point to particle-cluster center, max distance = farthest particle from release point, "
        "mean distance = average particle distance from release point.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_dispersion_area(metrics_df: pd.DataFrame, snapshot_hours: list[int], output_path: Path) -> Path:
    bars = []
    for hour in snapshot_hours:
        index = (metrics_df["hours_since_release"] - float(hour)).abs().idxmin()
        bars.append((hour, float(metrics_df.loc[index, "convex_hull_area_km2"])))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([str(hour) for hour, _ in bars], [value for _, value in bars], color="#4C78A8", label="Convex hull area")
    ax.set_xlabel("Snapshot hour")
    ax.set_ylabel("Convex hull area (km²)")
    ax.set_title("Dispersion area at key times")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    _add_footer(
        fig,
        "Footnote: each bar represents the outer spread area of the particle cloud at the nearest saved timestep "
        "to the requested snapshot hour.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_comparison(metrics_map: dict[str, pd.DataFrame], output_path: Path) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for scenario_name, metrics_df in metrics_map.items():
        axes[0].plot(metrics_df["hours_since_release"], metrics_df["max_distance_km"], label=scenario_name)
        axes[1].plot(metrics_df["hours_since_release"], metrics_df["convex_hull_area_km2"], label=scenario_name)
    axes[0].set_ylabel("Max distance (km)")
    axes[0].set_title("Scenario comparison")
    axes[0].grid(True, alpha=0.3)
    axes[1].set_ylabel("Hull area (km²)")
    axes[1].set_xlabel("Hours since release")
    axes[1].grid(True, alpha=0.3)
    axes[0].legend(loc="best")
    axes[1].legend(loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "Footnote: top panel lines = scenario-wise maximum particle travel distance, "
        "bottom panel lines = scenario-wise convex hull area over time.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
