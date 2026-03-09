from __future__ import annotations

from typing import Iterable
import math

import numpy as np
from shapely.geometry import MultiPoint


EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: Iterable[float] | float, lon2: Iterable[float] | float) -> np.ndarray:
    lat1_rad = np.radians(float(lat1))
    lon1_rad = np.radians(float(lon1))
    lat2_rad = np.radians(np.asarray(lat2, dtype=float))
    lon2_rad = np.radians(np.asarray(lon2, dtype=float))
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def lonlat_to_local_km(lon: Iterable[float], lat: Iterable[float], origin_lon: float, origin_lat: float) -> tuple[np.ndarray, np.ndarray]:
    lon_arr = np.asarray(lon, dtype=float)
    lat_arr = np.asarray(lat, dtype=float)
    x = np.radians(lon_arr - origin_lon) * EARTH_RADIUS_KM * math.cos(math.radians(origin_lat))
    y = np.radians(lat_arr - origin_lat) * EARTH_RADIUS_KM
    return x, y


def convex_hull_area_km2(lon: Iterable[float], lat: Iterable[float], origin_lon: float, origin_lat: float) -> float:
    x, y = lonlat_to_local_km(lon, lat, origin_lon, origin_lat)
    points = [(float(px), float(py)) for px, py in zip(x, y, strict=False)]
    if len(points) < 3:
        return 0.0
    hull = MultiPoint(points).convex_hull
    return float(hull.area)


def convex_hull_lonlat(lon: Iterable[float], lat: Iterable[float]) -> list[tuple[float, float]]:
    points = [(float(px), float(py)) for px, py in zip(lon, lat, strict=False)]
    if len(points) < 3:
        return points
    hull = MultiPoint(points).convex_hull
    if hull.geom_type == "Polygon":
        return [(float(x), float(y)) for x, y in hull.exterior.coords]
    if hull.geom_type == "LineString":
        return [(float(x), float(y)) for x, y in hull.coords]
    if hull.geom_type == "Point":
        return [(float(hull.x), float(hull.y))]
    return points


def ratio_within_bbox(lon: Iterable[float], lat: Iterable[float], bbox: list[float] | None) -> float:
    if bbox is None:
        return float("nan")
    lon_arr = np.asarray(lon, dtype=float)
    lat_arr = np.asarray(lat, dtype=float)
    if lon_arr.size == 0:
        return float("nan")
    mask = (bbox[0] <= lon_arr) & (lon_arr <= bbox[1]) & (bbox[2] <= lat_arr) & (lat_arr <= bbox[3])
    return float(mask.mean())
