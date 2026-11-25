CREATE TABLE IF NOT EXISTS raw_weather(
    ts TIMESTAMPTZ NOT NULL, 
    latitude    NUMERIC NOT NULL,
    longitude NUMERIC NOT NULL,
    temperature_2m NUMERIC,
    wind_speed_10m NUMERIC,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ts, latitude, longitude)
);