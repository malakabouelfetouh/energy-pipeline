CREATE TABLE IF NOT EXISTS raw_prices (
    start_ts TIMESTAMPTZ PRIMARY KEY,
    end_ts TIMESTAMPTZ NOT NULL,
    price_eur_mwh NUMERIC NOT NULL,
    unit TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);