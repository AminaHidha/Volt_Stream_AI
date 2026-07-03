def estimate_range_km(battery_percent: float, capacity_kwh: float, efficiency: float):
    """
    Calculate how many km EV can still travel
    """

    available_kwh = (battery_percent / 100) * capacity_kwh
    estimated_km = available_kwh * efficiency

    return round(estimated_km, 2)