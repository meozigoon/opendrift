from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.lines import Line2D
from matplotlib import font_manager

from src.analysis.geometry import convex_hull_lonlat
from src.simulation.config_loader import ScenarioConfig

try:  # pragma: no cover
    import cartopy.crs as ccrs
except Exception:  # pragma: no cover
    ccrs = None


def _configure_korean_font() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in ("Malgun Gothic", "NanumGothic", "AppleGothic", "HYGothic-Medium", "Gulim"):
        if font_name in available:
            matplotlib.rcParams["font.family"] = font_name
            break


_configure_korean_font()


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
    ax.set_xlabel("경도")
    ax.set_ylabel("위도")
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
    _plot_scatter(ax, final_lon[valid_final], final_lat[valid_final], transform, s=25, c="#F58518", alpha=0.8, label="최종 입자 위치")
    _plot_scatter(ax, np.array([scenario.release_lon]), np.array([scenario.release_lat]), transform, s=90, marker="*", c="#E45756", label="방출점")

    centroid_lon = metrics_df["centroid_lon"].to_numpy(dtype=float)
    centroid_lat = metrics_df["centroid_lat"].to_numpy(dtype=float)
    valid_centroid = np.isfinite(centroid_lon) & np.isfinite(centroid_lat)
    if valid_centroid.any():
        _plot_line(ax, centroid_lon[valid_centroid], centroid_lat[valid_centroid], transform, color="#54A24B", linewidth=2.0, label="중심점 경로")

    hull = convex_hull_lonlat(final_lon[valid_final], final_lat[valid_final])
    if len(hull) >= 3:
        hull_lon = np.array([point[0] for point in hull], dtype=float)
        hull_lat = np.array([point[1] for point in hull], dtype=float)
        _plot_line(ax, hull_lon, hull_lat, transform, color="#B279A2", linewidth=1.8, label="최종 볼록 껍질")

    ax.set_title(f"입자 궤적 지도: {scenario.scenario_name}")
    ax.legend(loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "설명: 파란 얇은 선은 개별 입자 궤적, 주황 점은 최종 입자 위치, 빨간 별은 방출점, "
        "초록 선은 중심점 이동 경로, 보라 선은 최종 볼록 껍질입니다.",
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
        _plot_line(ax, hull_lon, hull_lat, transform, color="#E45756", linewidth=2.0, label="최종 볼록 껍질")
    _plot_scatter(
        ax,
        np.array([scenario.release_lon]),
        np.array([scenario.release_lat]),
        transform,
        s=90,
        marker="*",
        c="#54A24B",
        label="방출점",
    )
    ax.set_title(f"최종 볼록 껍질 지도: {scenario.scenario_name}")
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", label="최종 입자 위치", markerfacecolor="#4C78A8", markersize=8),
        Line2D([0], [0], color="#E45756", lw=2, label="최종 볼록 껍질"),
        Line2D([0], [0], marker="*", color="w", label="방출점", markerfacecolor="#54A24B", markersize=12),
    ]
    ax.legend(handles=legend_handles, loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "설명: 파란 점은 최종 시점 입자 위치, 빨간 선은 볼록 껍질 기반 외곽 경계, 초록 별은 원래 방출점입니다.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_centroid_distance(metrics_df: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(metrics_df["hours_since_release"], metrics_df["centroid_distance_km"], label="중심점 이동거리", linewidth=2.0)
    ax.plot(metrics_df["hours_since_release"], metrics_df["max_distance_km"], label="최대 이동거리", linewidth=1.6)
    ax.plot(metrics_df["hours_since_release"], metrics_df["mean_distance_km"], label="평균 이동거리", linewidth=1.6)
    ax.set_xlabel("방출 후 경과 시간 (시간)")
    ax.set_ylabel("거리 (km)")
    ax.set_title("시간에 따른 거리 지표")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    _add_footer(
        fig,
        "설명: 중심점 이동거리는 방출점에서 입자군 중심까지의 거리, 최대 이동거리는 가장 멀리 이동한 입자 거리, "
        "평균 이동거리는 전체 입자의 평균 거리입니다.",
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
    ax.bar([str(hour) for hour, _ in bars], [value for _, value in bars], color="#4C78A8", label="볼록 껍질 면적")
    ax.set_xlabel("스냅샷 시각 (시간)")
    ax.set_ylabel("볼록 껍질 면적 (km²)")
    ax.set_title("주요 시점의 확산 면적")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    _add_footer(
        fig,
        "설명: 각 막대는 요청한 스냅샷 시각에 가장 가까운 저장 시점에서 계산한 입자군의 외곽 확산 면적입니다.",
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
    axes[0].set_ylabel("최대 이동거리 (km)")
    axes[0].set_title("시나리오 비교")
    axes[0].grid(True, alpha=0.3)
    axes[1].set_ylabel("볼록 껍질 면적 (km²)")
    axes[1].set_xlabel("방출 후 경과 시간 (시간)")
    axes[1].grid(True, alpha=0.3)
    axes[0].legend(loc="best")
    axes[1].legend(loc="best")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _add_footer(
        fig,
        "설명: 위 패널의 선은 시나리오별 최대 이동거리, 아래 패널의 선은 시나리오별 볼록 껍질 면적의 시간 변화를 나타냅니다.",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
