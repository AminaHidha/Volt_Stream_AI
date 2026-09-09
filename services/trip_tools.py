import os
import requests
from langchain_core.tools import tool
from . import django_client, external_apis

DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://localhost:8000/api")


def _headers(token: str):
    return {"Authorization": token, "Content-Type": "application/json"} if token else {}


def _unwrap(data):
    if isinstance(data, dict):
        return data.get("results", data)
    return data


def _get(url, token, params=None):
    try:
        resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
        if resp.status_code >= 400:
            return {"error": f"Request failed ({resp.status_code}): {resp.text[:200]}"}
        return _unwrap(resp.json())
    except requests.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}


def _post(url, token, json_body):
    try:
        resp = requests.post(url, headers=_headers(token), json=json_body, timeout=15)
        if resp.status_code >= 400:
            try:
                return {"error": resp.json()}
            except ValueError:
                return {"error": resp.text[:200]}
        return resp.json()
    except requests.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}


def search_stations(token: str, city: str = "", search: str = ""):
    params = {}
    if city:
        params["city"] = city
    if search:
        params["search"] = search
    return _get(f"{DJANGO_BASE_URL}/stations/public/", token, params)


def get_all_stations(token: str = ""):
    return _get(f"{DJANGO_BASE_URL}/stations/list/", token, {"page": 1, "page_size": 1000})


def get_chargers_for_station(token: str, station_id: int):
    return _get(f"{DJANGO_BASE_URL}/chargers/station/{station_id}/", token)


def get_slot_availability(token: str, charger_id: int, booking_date: str):
    return _get(
        f"{DJANGO_BASE_URL}/slots/charger/{charger_id}/availability/",
        token,
        {"date": booking_date},
    )


def create_booking(token: str, slot_id: int, booking_date: str, total_amount: float):
    return _post(
        f"{DJANGO_BASE_URL}/bookings/create/",
        token,
        {"slot": slot_id, "booking_date": booking_date, "total_amount": total_amount},
    )


def create_payment_order(token: str, booking_id: int, amount: float):
    return _post(
        f"{DJANGO_BASE_URL}/payments/create/",
        token,
        {"booking": booking_id, "amount": amount},
    )


def make_trip_tools(token: str):
    """Creates the tool list for trip planning, closured around user's token."""

    @tool
    def plan_route(origin: str, destination: str) -> dict:
        """Plan a route between origin and destination, finding distance, duration, and nearby charging stations."""
        from_coord = external_apis.geocode(origin)
        to_coord = external_apis.geocode(destination)
        if not from_coord or not to_coord:
            return {"error": f"Could not geocode origin or destination ({origin} -> {destination})"}

        route_info = external_apis.get_route(from_coord, to_coord)
        if not route_info:
            return {"error": "Could not calculate route"}

        all_stations = django_client.get_all_stations(token)
        if isinstance(all_stations, dict) and "error" in all_stations:
            all_stations = []

        near_stations = []
        for station in (all_stations if isinstance(all_stations, list) else []):
            try:
                lat = float(station.get("latitude", 0))
                lng = float(station.get("longitude", 0))
                if external_apis.is_near_route(lat, lng, route_info["coords"], threshold_km=15):
                    near_stations.append(station)
            except (ValueError, TypeError):
                pass

        return {
            "origin": origin,
            "destination": destination,
            "distance_km": route_info["distance_km"],
            "duration_min": route_info["duration_min"],
            "stations_near_route": near_stations,
        }

    @tool
    def tool_get_chargers_for_station(station_id: int) -> list:
        """Get all chargers at a station, including price_per_kwh and power_output."""
        return django_client.get_chargers_for_station(token, station_id)

    @tool
    def tool_check_slot_availability(charger_id: int, date: str) -> list:
        """Get time slots for a charger on a specific date (YYYY-MM-DD), with is_booked status."""
        return django_client.get_slot_availability(token, charger_id, date)

    @tool
    def tool_create_booking(slot_id: int, date: str, price_per_kwh: float, power_output: float) -> dict:
        """
        Book a specific available slot and create its payment order.
        Only call this once you already know slot_id, date, price_per_kwh and power_output from earlier tool results.
        """
        total_amount = round(price_per_kwh * power_output * 0.5, 2)
        booking = django_client.create_booking(token, slot_id, date, total_amount)
        if "error" in booking:
            return booking

        booking_id = booking.get("booking_id") or booking.get("id")
        payment = django_client.create_payment_order(token, booking_id, total_amount)
        return {"booking": booking, "payment": payment, "total_amount": total_amount}

    return [plan_route, tool_get_chargers_for_station, tool_check_slot_availability, tool_create_booking]