from __future__ import annotations

from io import BytesIO
from pathlib import Path
import math

from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.lines import Line2D

from src.analysis.geometry import convex_hull_lonlat
from src.analysis.plotting import _add_footer, _extent_from_points, _make_map_figure, _plot_line, _plot_scatter
from src.simulation.config_loader import ScenarioConfig


def nearest_time_index(dataset: xr.Dataset, target_hour: int) -> tuple[int, float]:
    times = dataset["time"].values
    hours = (times - times[0]) / np.timedelta64(1, "h")
    index = int(np.argmin(np.abs(hours.astype(float) - float(target_hour))))
    return index, float(hours[index])


def save_snapshot(dataset: xr.Dataset, scenario: ScenarioConfig, output_path: Path, target_hour: int) -> tuple[Path, float]:
    index, actual_hour = nearest_time_index(dataset, target_hour)
    lon = np.asarray(dataset["lon"].values[:, index], dtype=float)
    lat = np.asarray(dataset["lat"].values[:, index], dtype=float)
    valid = np.isfinite(lon) & np.isfinite(lat)
    extent = _extent_from_points(lon[valid], lat[valid])
    fig, ax, transform = _make_map_figure(extent)
    _plot_scatter(ax, lon[valid], lat[valid], transform, s=24, c="#4C78A8", alpha=0.8)
    _plot_scatter(ax, np.array([scenario.release_lon]), np.array([scenario.release_lat]), transform, s=85, marker="*", c="#E45756")
    hull = convex_hull_lonlat(lon[valid], lat[valid])
    if len(hull) >= 3:
        hull_lon = np.array([point[0] for point in hull], dtype=float)
        hull_lat = np.array([point[1] for point in hull], dtype=float)
        _plot_line(ax, hull_lon, hull_lat, transform, color="#B279A2", linewidth=1.8)
    ax.set_title(f"Snapshot {target_hour}h (nearest={actual_hour:.1f}h)")
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", label="Particle positions", markerfacecolor="#4C78A8", markersize=7),
        Line2D([0], [0], marker="*", color="w", label="Release point", markerfacecolor="#E45756", markersize=12),
        Line2D([0], [0], color="#B279A2", lw=2, label="Convex hull"),
    ]
    ax.legend(handles=legend_handles, loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "Footnote: blue dots = particle positions at this snapshot, red star = release point, "
        "purple line = outer boundary from convex hull.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path, actual_hour


def build_animation_gif(
    dataset: xr.Dataset,
    scenario: ScenarioConfig,
    output_path: Path,
    frame_stride: int = 1,
    max_frames: int = 48,
) -> Path:
    total_frames = int(dataset.sizes["time"])
    auto_stride = max(1, math.ceil(total_frames / max_frames))
    step = max(1, frame_stride, auto_stride)
    frame_indices = list(range(0, total_frames, step))
    if frame_indices[-1] != total_frames - 1:
        frame_indices.append(total_frames - 1)

    lon_all = np.asarray(dataset["lon"].values, dtype=float)
    lat_all = np.asarray(dataset["lat"].values, dtype=float)
    extent = _extent_from_points(lon_all, lat_all)
    times = dataset["time"].values
    frames: list[Image.Image] = []
    buffers: list[BytesIO] = []

    for index in frame_indices:
        lon = lon_all[:, index]
        lat = lat_all[:, index]
        valid = np.isfinite(lon) & np.isfinite(lat)
        fig, ax, transform = _make_map_figure(extent)
        _plot_scatter(ax, lon[valid], lat[valid], transform, s=22, c="#4C78A8", alpha=0.8)
        _plot_scatter(ax, np.array([scenario.release_lon]), np.array([scenario.release_lat]), transform, s=85, marker="*", c="#E45756")
        ax.set_title(f"{scenario.scenario_name} | {np.datetime_as_string(times[index], unit='h')}")
        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)
        image = Image.open(buffer).convert("P", palette=Image.ADAPTIVE)
        frames.append(image.copy())
        buffers.append(buffer)
        image.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=450, loop=0)
    for frame in frames:
        frame.close()
    for buffer in buffers:
        buffer.close()
    return output_path
