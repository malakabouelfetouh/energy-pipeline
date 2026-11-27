# Energy Pipeline

An automated data pipeline that collects German electricity prices and weather data, stores them in PostgreSQL, and prepares them for analysis of how weather shapes power prices.

## Overview

Energy Pipeline is an end-to-end data engineering project that investigates how weather affects electricity prices in Germany. It pulls hourly day-ahead electricity prices for Germany from the aWATTar API and hourly weather for Berlin from Open-Meteo, loads both into a PostgreSQL database running in Docker, and keeps the raw data intact so it can be cleaned and analysed later without re-fetching it.

Loads are idempotent: each record is keyed by its timestamp, so the pipeline can run repeatedly without creating duplicates. All timestamps are stored in UTC, and each row records when it was last ingested.

> **Scope note:** prices are national, but weather currently comes from a single location (Berlin). Results are therefore an approximation of nationwide conditions. See [Design choices](#design-choices-and-trade-offs).

## Status

The project is under active development.

**Built so far**

- [x] Extract hourly electricity prices from aWATTar
- [x] Extract hourly weather from Open-Meteo
- [x] Load prices and weather into PostgreSQL with idempotent upserts
- [x] Unit tests for extraction and for mapping price records to table rows

**Coming next**

- [ ] dbt models (staging and analysis-ready tables) with data tests
- [ ] Prefect flow for scheduled, automatic runs
- [ ] Streamlit dashboard
- [ ] Continuous integration (lint and tests on every push)
- [ ] Weather date range that follows the price window (see [Known limitations](#known-limitations))

## Data sources

| Data | Source | Fields | Notes |
|---|---|---|---|
| Electricity prices | [aWATTar API](https://www.awattar.de) (`api.awattar.de/v1/marketdata`) | start and end time, price, unit (EUR/MWh) | No API key. Fair-use limit of about 100 requests per day. Prices can be negative. |
| Weather | [Open-Meteo historical archive](https://open-meteo.com/en/docs/historical-weather-api) | timestamp, latitude, longitude, temperature (degrees C), wind speed (km/h) | No API key. Modelled (reanalysis) data, not a single weather station. |

## Tech stack

Python, PostgreSQL 16, Docker Compose, psycopg, requests, pytest, Ruff. Planned: dbt, Prefect, Streamlit, GitHub Actions.

## Project structure

```
energy-pipeline/
  src/energy_pipeline/   extract.py, extract_weather.py, load.py, config.py
  sql/                   table definitions, applied in numeric order
  tests/                 pytest tests
  dbt/                   (planned) transformations
  dashboard/             (planned) Streamlit app
  docs/                  documentation and diagrams
  docker-compose.yml     PostgreSQL service
  .env.example           template for local settings
  pyproject.toml         dependencies and tool settings
```

## Quickstart

Requires Python 3.11 or newer, Git, and Docker Desktop.

**1. Clone the repository**

```
git clone https://github.com/malakabouelfetouh/energy-pipeline.git
cd energy-pipeline
```

**2. Create and activate a virtual environment, then install**

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

macOS or Linux:

```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**3. Create your local settings**

Windows (PowerShell): `Copy-Item .env.example .env`
macOS or Linux: `cp .env.example .env`

Open `.env` and set your own `POSTGRES_PASSWORD`. Never commit `.env`.

**4. Start the database**

```
docker compose up -d
docker compose ps
```

Wait until the status shows `healthy`.

**5. Create the tables**

Run each file in `sql/` in numeric order. Use the values from your `.env` for the user and database names (the defaults are `energy`).

Windows (PowerShell):

```
Get-Content sql\001_raw_prices.sql | docker compose exec -T db psql -U energy -d energy
Get-Content sql\002_raw_weather.sql | docker compose exec -T db psql -U energy -d energy
```

macOS or Linux:

```
cat sql/001_raw_prices.sql | docker compose exec -T db psql -U energy -d energy
cat sql/002_raw_weather.sql | docker compose exec -T db psql -U energy -d energy
```

You should see `CREATE TABLE` twice.

**6. Load data**

```
python -m energy_pipeline.load
```

Expected output is similar to:

```
prices loaded: 71
weather loaded: 168
```

Running the load again does not create duplicates. To check, count the rows before and after:

```
docker compose exec db psql -P pager=off -U energy -d energy -c "SELECT count(*) FROM raw_prices;"
```

**7. Stop the database**

```
docker compose down
```

This keeps your data. `docker compose down -v` also deletes the stored data, so use it only on purpose.

## Tests and code quality

```
pytest -v
ruff check .
ruff format .
```

The tests run without internet access or a database: HTTP calls are replaced with fakes, and row mapping is tested directly. The database upsert itself is verified manually for now; automated database tests are planned together with continuous integration.

## Design choices and trade-offs

- **UTC timestamps (`TIMESTAMPTZ`).** UTC is one unambiguous moment for everyone. Local time is only a display concern. Storing UTC avoids daylight-saving bugs.
- **Raw layer first.** Data is loaded as the source delivered it, with only light typing (epoch milliseconds become timestamps, columns get clear names). Cleaning and combining will happen later in dbt. If a cleaning rule turns out to be wrong, it can be fixed and rebuilt from stored data without re-fetching from a rate-limited API.
- **Primary keys and upserts.** Each price row is keyed by its start time, each weather row by time and location. Loading uses `INSERT ... ON CONFLICT DO UPDATE`, so the pipeline can run every hour with overlapping windows. A plain `INSERT` would make the second run fail with a duplicate-key error, and without a key, duplicates would silently distort averages.
- **`ingested_at`.** Each row records when the pipeline last confirmed it, which helps with data freshness checks and debugging.
- **Single weather location.** Prices are national, but weather is fetched for one point (Berlin, 52.52 N, 13.41 E) to keep the first version simple. This understates regional differences, especially wind in northern Germany. The weather table's key already includes latitude and longitude, so more locations can be added without changing the table.
- **Prefect (planned).** Chosen over Airflow because it is lighter to set up for a project of this size.

## Known limitations

- Weather currently loads a fixed historical week (1 to 7 November 2026), set in `load.py`, while prices load the last three days. The date ranges are not yet aligned or automatic.
- Weather comes from one location only (Berlin).
- Database loading is not yet covered by automated tests.
- The aWATTar API is rate limited (about 100 requests per day), so avoid running the load in a tight loop.

## License

Released under the MIT License. See [LICENSE](LICENSE).