import json
import os
from datetime import datetime, timezone
from pathlib import Path

import polyline
import requests
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
USER_AGENT = "TrafficAdvisorMawa/1.0"


def geocode_address(address: str) -> tuple[float, float]:
    """Convert a place name into latitude and longitude."""
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    results = response.json()
    if not results:
        raise ValueError(f"Could not find location: {address}")
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    return lat, lon


def get_route(from_address: str, to_address: str) -> dict:
    """
    Return route info: coordinates for map, distance (km), duration (min).
    Uses OpenRouteService when ORS_API_KEY is set; otherwise straight-line estimate.
    """
    start = geocode_address(from_address)
    end = geocode_address(to_address)

    ors_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjhjYjQ2MmY0ZjQ1YzQyMDVhYTVkY2Y4ZTZhNzJmYmEwIiwiaCI6Im11cm11cjY0In0="
    if ors_key:
        try:
            return _route_with_ors(start, end, ors_key)
        except Exception:
            result = _route_straight_line(start, end, from_address, to_address)
            result["note"] = (
                "Could not fetch driving route from OpenRouteService. "
                "Showing straight-line estimate instead. Check your ORS_API_KEY."
            )
            return result

    return _route_straight_line(start, end, from_address, to_address)


def _route_with_ors(start: tuple[float, float], end: tuple[float, float], api_key: str) -> dict:
    body = {"coordinates": [[start[1], start[0]], [end[1], end[0]]]}
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    response = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        message = data["error"].get("message", data["error"])
        raise ValueError(message)

    routes = data.get("routes")
    if not routes:
        raise ValueError("No route returned from OpenRouteService.")

    route = routes[0]
    summary = route["summary"]
    distance_km = round(summary["distance"] / 1000, 2)
    duration_min = round(summary["duration"] / 60, 1)

    encoded = route.get("geometry")
    if not encoded:
        coords = [list(start), list(end)]
    else:
        # ORS returns an encoded polyline; decode to [lat, lon] for Folium
        coords = [[lat, lon] for lat, lon in polyline.decode(encoded)]

    return {
        "start": start,
        "end": end,
        "coords": coords,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "source": "openrouteservice",
    }


def _route_straight_line(
    start: tuple[float, float],
    end: tuple[float, float],
    from_address: str,
    to_address: str,
) -> dict:
    from math import asin, cos, radians, sin, sqrt

    lat1, lon1 = radians(start[0]), radians(start[1])
    lat2, lon2 = radians(end[0]), radians(end[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    distance_km = round(6371 * 2 * asin(sqrt(a)), 2)
    duration_min = round(distance_km / 40 * 60, 1)

    return {
        "start": start,
        "end": end,
        "coords": [list(start), list(end)],
        "distance_km": distance_km,
        "duration_min": duration_min,
        "source": "estimate",
        "note": (
            "Straight-line estimate. Add ORS_API_KEY to .env for real driving routes "
            "(free key at openrouteservice.org)."
        ),
    }


def save_trip(from_address: str, to_address: str, distance_km: float, duration_min: float) -> None:
    path = DATA_DIR / "trip_history.json"
    with open(path, encoding="utf-8") as f:
        trips = json.load(f)

    trips.append(
        {
            "from": from_address,
            "to": to_address,
            "distance_km": distance_km,
            "duration_min": duration_min,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(trips, f, indent=2, ensure_ascii=False)
