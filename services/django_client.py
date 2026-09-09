import os
import requests

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