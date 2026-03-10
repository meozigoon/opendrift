from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import xarray as xr

from src.ui.texts import localize_dataframe, localize_manifest
from src.utils.validation import ValidationResult


def render_validation_result(validation: ValidationResult) -> None:
    for message in validation.errors:
        st.error(message)
    for message in validation.warnings:
        st.warning(message)
    for message in validation.info:
        st.info(message)


def render_summary_cards(summary_df: pd.DataFrame) -> None:
    if summary_df.empty:
        return
    row = summary_df.iloc[0]
    columns = st.columns(4)
    columns[0].metric("최종 최대 이동거리 (km)", f"{row['final_max_distance_km']:.2f}")
    columns[1].metric("최종 중심점 이동거리 (km)", f"{row['final_centroid_distance_km']:.2f}")
    columns[2].metric("최종 볼록 껍질 면적 (km²)", f"{row['final_convex_hull_area_km2']:.2f}")
    columns[3].metric("표층 잔류 비율", f"{row['final_surface_retention_ratio']:.2%}")


def render_image_if_exists(path: Path, caption: str) -> None:
    if path.exists():
        st.image(str(path), caption=caption, width="stretch")


def render_plot_footnote(text: str) -> None:
    st.caption(f"설명: {text}")


def render_screen_help(title: str, description: str) -> None:
    st.info(f"{title}: {description}")


def _build_paths(dataset: xr.Dataset, max_paths: int = 40) -> list[dict]:
    lon = np.asarray(dataset["lon"].values, dtype=float)
    lat = np.asarray(dataset["lat"].values, dtype=float)
    limit = min(max_paths, lon.shape[0])
    records = []
    for index in range(limit):
        valid = np.isfinite(lon[index, :]) & np.isfinite(lat[index, :])
        if valid.sum() < 2:
            continue
        path = [[float(lon_val), float(lat_val)] for lon_val, lat_val in zip(lon[index, valid], lat[index, valid], strict=False)]
        records.append({"path": path})
    return records


def render_pydeck_map(dataset: xr.Dataset, time_index: int) -> None:
    lon = np.asarray(dataset["lon"].values[:, time_index], dtype=float)
    lat = np.asarray(dataset["lat"].values[:, time_index], dtype=float)
    valid = np.isfinite(lon) & np.isfinite(lat)
    if not valid.any():
        st.info("선택한 시점에 유효한 입자 위치가 없습니다.")
        return

    point_data = [{"lon": float(lon_val), "lat": float(lat_val), "label": f"입자 {idx + 1}"} for idx, (lon_val, lat_val) in enumerate(zip(lon[valid], lat[valid], strict=False))]
    center_lon = float(np.nanmean(lon[valid]))
    center_lat = float(np.nanmean(lat[valid]))
    layers = [
        pdk.Layer(
            "PathLayer",
            data=_build_paths(dataset),
            get_path="path",
            get_width=25,
            get_color=[76, 120, 168, 120],
            width_min_pixels=1,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=point_data,
            get_position="[lon, lat]",
            get_radius=1500,
            get_fill_color=[245, 133, 24, 180],
        ),
    ]
    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0),
        tooltip={"text": "{label}"},
        layers=layers,
    )
    st.pydeck_chart(deck, width="stretch")
    render_plot_footnote(
        "파란 선은 방출 시점부터 저장된 마지막 시점까지의 대표 입자 궤적이고, 주황 점은 현재 선택한 시점의 입자 위치입니다."
    )


def render_animation_if_exists(path: Path, caption: str) -> None:
    if path.exists():
        st.image(str(path), caption=caption, width="stretch")


def render_download_buttons(result_dir: Path) -> None:
    file_order = [
        "result.nc",
        "summary.csv",
        "metrics.csv",
        "scenario_config_copy.json",
        "resolved_scenario.json",
        "trajectory_map.png",
        "convex_hull_map.png",
        "snapshot_24h.png",
        "snapshot_72h.png",
        "snapshot_168h.png",
        "animation.gif",
        "comparison_plot.png",
        "centroid_distance_plot.png",
        "dispersion_area_plot.png",
        "results_bundle.zip",
    ]
    mime_map = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".png": "image/png",
        ".gif": "image/gif",
        ".zip": "application/zip",
        ".nc": "application/x-netcdf",
    }
    for filename in file_order:
        path = result_dir / filename
        if not path.exists():
            continue
        st.download_button(
            label=f"{filename} 다운로드",
            data=path.read_bytes(),
            file_name=filename,
            mime=mime_map.get(path.suffix.lower(), "application/octet-stream"),
            key=f"download_{result_dir.name}_{filename}",
        )


def render_manifest(result_dir: Path) -> None:
    manifest_path = result_dir / "manifest.json"
    if manifest_path.exists():
        localized = localize_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
        st.json(localized)


def render_localized_dataframe(dataframe: pd.DataFrame, *, width: str = "stretch", height: int | None = None) -> None:
    localized = localize_dataframe(dataframe)
    kwargs = {"width": width}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(localized, **kwargs)
