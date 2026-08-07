import duckdb
import os

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "./analytics.duckdb")


def query_analytics(question: str) -> str:
    question_lower = question.lower()

    try:
        # Check if file exists first
        if not os.path.exists(DUCKDB_PATH):
            print(f"DuckDB file not found at: {DUCKDB_PATH}")
            return None

        conn = duckdb.connect(DUCKDB_PATH, read_only=True)

        # Check tables exist
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"DuckDB tables: {tables}")

        # Total revenue
        if any(word in question_lower for word in ["revenue", "money", "earned", "income"]):
            result = conn.execute(
                "SELECT SUM(revenue) as total FROM booking_summary"
            ).fetchone()
            conn.close()
            total = result[0] or 0
            return f"Total revenue on VoltStream is ₹{float(total):.2f}."

        # Total bookings
        if any(word in question_lower for word in ["total booking", "how many booking", "number of booking"]):
            result = conn.execute(
                "SELECT SUM(count) as total FROM booking_summary"
            ).fetchone()
            conn.close()
            total = result[0] or 0
            return f"There are {int(total)} total bookings on VoltStream."

        # Top station
        if any(word in question_lower for word in ["top station", "most popular", "best station", "most booking"]):
            result = conn.execute(
                "SELECT station_name, city, total_bookings FROM station_performance ORDER BY total_bookings DESC LIMIT 1"
            ).fetchone()
            conn.close()
            if result:
                return f"{result[0]} in {result[1]} is the most popular station with {result[2]} bookings."
            return "No station data available yet."

        # Busiest hour
        if any(word in question_lower for word in ["busiest", "peak hour", "busy time", "most active"]):
            result = conn.execute(
                "SELECT hour, count FROM hourly_bookings ORDER BY count DESC LIMIT 1"
            ).fetchone()
            conn.close()
            if result:
                hour = int(result[0])
                label = f"{hour}AM" if hour < 12 else f"{hour - 12}PM" if hour > 12 else "12PM"
                return f"The busiest charging hour is {label} with {result[1]} bookings."
            return "No hourly data available yet."

        # Rating
        if any(word in question_lower for word in ["rating", "review", "rated", "score"]):
            result = conn.execute(
                "SELECT station_name, avg_rating FROM ratings_summary ORDER BY avg_rating DESC LIMIT 1"
            ).fetchone()
            conn.close()
            if result:
                return f"{result[0]} has the highest rating of {float(result[1]):.1f} out of 5."
            return "No rating data available yet."

        conn.close()
        return None

    except Exception as e:
        print(f"DuckDB query error: {e}")
        return None