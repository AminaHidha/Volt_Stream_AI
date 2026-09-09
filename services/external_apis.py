import requests
import math

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def geocode(place: str):
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": place, "format": "json", "limit": 1},
        headers={"User-Agent": "VoltStreamAI/1.0"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None
    return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}


def get_route(from_coord: dict, to_coord: dict):
    url = f"{OSRM_URL}/{from_coord['lng']},{from_coord['lat']};{to_coord['lng']},{to_coord['lat']}"
    resp = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok":
        return None

    route = data["routes"][0]
    coords = [[lat, lng] for lng, lat in route["geometry"]["coordinates"]]

    return {
        "distance_km": round(route["distance"] / 1000, 1),
        "duration_min": round(route["duration"] / 60),
        "coords": coords,
    }


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_near_route(lat, lng, route_coords, threshold_km=15):
    for r_lat, r_lng in route_coords:
        if haversine_km(lat, lng, r_lat, r_lng) <= threshold_km:
            return True
    return False