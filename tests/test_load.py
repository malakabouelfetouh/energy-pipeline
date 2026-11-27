from datetime import UTC, datetime

from energy_pipeline import load


def test_price_record_to_row():
    record = {
        "start_timestamp": 1795125600000,
        "end_timestamp": 1795129200000,
        "marketprice": 183.94,
        "unit": "Eur/MWh",
    }

    row = load.price_record_to_row(record)

    assert row == {
        "start_ts": datetime(2026, 11, 19, 22, 0, tzinfo=UTC),
        "end_ts": datetime(2026, 11, 19, 23, 0, tzinfo=UTC),
        "price_eur_mwh": 183.94,
        "unit": "Eur/MWh",
    }
