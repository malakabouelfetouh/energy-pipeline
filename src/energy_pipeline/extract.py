from datetime import UTC, datetime, timedelta

import requests

API_URL = "https://api.awattar.de/v1/marketdata"


def to_epoch_ms(
    moment: datetime,
) -> int:  # converts timezone date to epoch in milliseconds which is the API default
    return int(moment.timestamp() * 1000)


def fetch_prices(
    start: datetime, end: datetime
) -> list[dict]:  # returns the raw price record between start and end
    params = {
        "start": to_epoch_ms(start),
        "end": to_epoch_ms(end),
    }
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["data"]


if __name__ == "__main__":
    end = datetime.now(UTC)
    start = end - timedelta(days=3)
    records = fetch_prices(start, end)
    print(len(records))
    print(records[0])
    print(records[-1])
