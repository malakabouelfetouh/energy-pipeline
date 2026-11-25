from datetime import UTC, datetime

import pytest
import requests

fake_hourly = {
    "time": ["2026-11-01T00:00", "2026-11-01T01:00"],
    "temperature_2m": [6.5, 6.1],
    "wind_speed_10m": [8.5, 9.0],
}

from energy_pipeline import extract_weather


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_reshape_hourly():
    rows = extract_weather.reshape_hourly(fake_hourly, 52.52, 13.41)

    assert len(rows) == 2
    assert rows[0]["ts"] == datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
    assert rows[0]["temperature_2m"] == 6.5


def test_fetch_weather_returns_rows(monkeypatch):
    captured: dict = {}

    def fake_get(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse({"hourly": fake_hourly})

    monkeypatch.setattr(requests, "get", fake_get)

    rows = extract_weather.fetch_weather(52.52, 13.41, "2026-11-01", "2026-11-02")
    assert len(rows) == 2
    assert captured["params"]["hourly"] == "temperature_2m,wind_speed_10m"


def test_fetch_weather_raises_on_bad_status(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return FakeResponse({}, status_code=500)

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(requests.HTTPError):
        extract_weather.fetch_weather(52.52, 13.41, "2026-11-01", "2026-11-02")
