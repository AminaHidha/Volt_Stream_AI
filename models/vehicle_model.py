from sqlalchemy import Column, Integer, String, Float
from database.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)

    battery_percent = Column(Float, default=100)
    battery_capacity_kwh = Column(Float, default=50)  # example EV size
    efficiency_km_per_kwh = Column(Float, default=6)   # how far EV travels per kWh