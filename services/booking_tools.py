from langchain_core.tools import tool
from . import django_client


def make_booking_tools(token: str):
    """Creates the tool list for one request, closured around that user's token."""

    @tool
    def search_stations(city: str = "") -> list:
        """Search EV charging stations, optionally filtered by city."""
        return django_client.search_stations(token, city=city)

    @tool
    def get_chargers_for_station(station_id: int) -> list:
        """Get all chargers at a station, including price_per_kwh and power_output."""
        return django_client.get_chargers_for_station(token, station_id)

    @tool
    def check_slot_availability(charger_id: int, date: str) -> list:
        """Get time slots for a charger on a specific date (YYYY-MM-DD), with is_booked status."""
        return django_client.get_slot_availability(token, charger_id, date)

    @tool
    def create_booking(slot_id: int, date: str, price_per_kwh: float, power_output: float) -> dict:
        """
        Book a specific available slot and create its payment order.
        Only call this once you already know slot_id, date, price_per_kwh and
        power_output from earlier tool results — never guess these values.
        date must be YYYY-MM-DD.
        """
        total_amount = round(price_per_kwh * power_output * 0.5, 2)

        booking = django_client.create_booking(token, slot_id, date, total_amount)
        if "error" in booking:
            return booking

        booking_id = booking.get("booking_id") or booking.get("id")
        payment = django_client.create_payment_order(token, booking_id, total_amount)

        return {"booking": booking, "payment": payment, "total_amount": total_amount}

    return [search_stations, get_chargers_for_station, check_slot_availability, create_booking]