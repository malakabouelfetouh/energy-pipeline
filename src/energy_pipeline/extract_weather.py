from datetime import UTC, datetime

import requests

API_URL = "https://archive-api.open-meteo.com/v1/archive"
BERLIN_LAT = 52.52
BERLIN_LON = 13.41


def reshape_hourly(
    hourly: dict, latitude: float, longitude: float
) -> list[dict]:  # turn parallel list to one dict per hour

    rows = []
    for time_str, temp, wind in zip(
        hourly["time"], hourly["temperature_2m"], hourly["wind_speed_10m"]
    ):
        rows.append(
            {
                "ts": datetime.fromisoformat(time_str).replace(tzinfo=UTC),
                "latitude": latitude,
                "longitude": longitude,
                "temperature_2m": temp,
                "wind_speed_10m": wind,
            }
        )
    return rows


def fetch_weather(
    latitude: float, longitude: float, start_date: str, end_date: str
) -> list[dict]:  # return hourly weather rows between 2 dates (yyyy-mm-dd)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,wind_speed_10m",
        "timezone": "UTC",
    }
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    return reshape_hourly(response.json()["hourly"], latitude, longitude)


if __name__ == "__main__":
    rows = fetch_weather(BERLIN_LAT, BERLIN_LON, "2026-11-01", "2026-11-07")
    print(len(rows))
    print(rows[0])
    print(rows[-1])
