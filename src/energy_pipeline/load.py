from datetime import UTC, datetime, timedelta

import psycopg

from energy_pipeline.config import get_db_settings
from energy_pipeline.extract import fetch_prices
from energy_pipeline.extract_weather import BERLIN_LAT, BERLIN_LON, fetch_weather

UPSERT_PRICES = """
INSERT INTO raw_prices (start_ts, end_ts, price_eur_mwh, unit)
VALUES (%(start_ts)s, %(end_ts)s, %(price_eur_mwh)s, %(unit)s)
ON CONFLICT (start_ts) DO UPDATE SET 
    end_ts = EXCLUDED.end_ts,
    price_eur_mwh = EXCLUDED.price_eur_mwh,
    unit = EXCLUDED.unit,
    ingested_at = now()
"""

UPSERT_WEATHER = """
INSERT INTO raw_weather (ts, latitude, longitude, temperature_2m, wind_speed_10m)
VALUES (%(ts)s, %(latitude)s, %(longitude)s, %(temperature_2m)s, %(wind_speed_10m)s)
ON CONFLICT (ts, latitude, longitude) DO UPDATE SET
    temperature_2m = EXCLUDED.temperature_2m,
    wind_speed_10m = EXCLUDED.wind_speed_10m,
    ingested_at = now()
"""


def ms_to_datetime(
    ms: int,
) -> datetime:  # convert each epoch millisecond to a UTC datetime

    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def price_record_to_row(
    record: dict,
) -> dict:  # map one API price record to the raw_prices column name

    return {
        "start_ts": ms_to_datetime(record["start_timestamp"]),
        "end_ts": ms_to_datetime(record["end_timestamp"]),
        "price_eur_mwh": record["marketprice"],
        "unit": record["unit"],
    }


def load_prices(
    records: list[dict],
) -> int:  # upsert prices records and return how many were sent

    rows = [price_record_to_row(r) for r in records]
    with psycopg.connect(**get_db_settings()) as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_PRICES, rows)
    return len(rows)


def load_weather(
    records: list[dict],
) -> int:  # upsert weather records and return how many were sent

    with psycopg.connect(**get_db_settings()) as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_WEATHER, records)
    return len(records)


if __name__ == "__main__":
    end = datetime.now(UTC)
    start = end - timedelta(days=3)
    print("prices loaded:", load_prices(fetch_prices(start, end)))
    weather = fetch_weather(BERLIN_LAT, BERLIN_LON, "2026-11-01", "2026-11-07")
    print("weather loaded:", load_weather(weather))
