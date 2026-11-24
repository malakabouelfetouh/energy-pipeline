from datetime import UTC, datetime

import pytest
import requests

from energy_pipeline import extract


class FakeResponse:  # pretends to be what requests.get returns
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_to_epoch_ms_known_date():
    moment = datetime(2026, 11, 19, 22, 0, tzinfo=UTC)
    assert extract.to_epoch_ms(moment) == 1795125600000


def test_fetch_prices_returns_records(monkeypatch):
    fake_records = [
        {
            "start_timestamp": 1,
            "end_timestamp": 2,
            "marketprice": 10.0,
            "unit": "Eur/MWh",
        }
    ]
    captured = {}

    def fake_get(url, params, timeout):
        captured["params"] = params
        return FakeResponse({"object": "list", "data": fake_records})

    monkeypatch.setattr(requests, "get", fake_get)
    start = datetime(2026, 11, 19, tzinfo=UTC)
    end = datetime(2026, 11, 20, tzinfo=UTC)

    result = extract.fetch_prices(start, end)

    assert result == fake_records
    assert captured["params"]["start"] == 1795046400000


def test_fetch_prices_raises_on_bad_status(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse({}, status_code=500)

    monkeypatch.setattr(requests, "get", fake_get)
    start = datetime(2026, 11, 19, tzinfo=UTC)
    end = datetime(2026, 11, 20, tzinfo=UTC)

    with pytest.raises(requests.HTTPError):
        extract.fetch_prices(start, end)
