# Museum Visitor Interaction ETL Pipeline

A single-file ETL pipeline that consumes visitor interaction events from Kafka (topic `lmnh`), validates and transforms them, and stores them in a remote PostgreSQL database (RDS or equivalent). Designed for realtime processing, reusability, clear logging, and unit testing.

## Features
- Realtime Kafka consumer (confluent-kafka)
- JSON parsing, field validation and type-normalisation (see `validations.py`)
- Button-type mapping and transformation logic
- Postgres loader (psycopg2) with simple transactional insert
- Comprehensive logging (success and error logs)
- Unit tests (pytest) for validation and transformation logic
- Simple, testable structure for dependency injection and mocking

## Project layout
- `etl.py` — main single-file ETL pipeline (consumer + ETL loop)
- `validations.py` — validation helpers (`validate_at`, `validate_site`, `validate_val`, `validate_data`)
- `database.py` — DB connection and `load_interaction` function
- `tests/` — pytest unit tests
- `.env` — environment variables (not committed)
- `consumer_success.log`, `consumer_error.log` — runtime logs

## Requirements
- Python 3.11+ (project uses modern typing and dataclasses patterns)
- Dependencies:
  - confluent-kafka
  - psycopg2-binary
  - python-dotenv
  - pytest (dev)

Install:
```bash
python -m pip install -r requirements.txt
```

## Configuration (.env)
Place `.env` in the project root (or provide explicit path). Example:
```
DB_HOST=your-db-host.rds.amazonaws.com
DB_USER=postgres
DB_PASSWORD=secret
BOOTSTRAP_SERVERS=broker:9092
SECURITY_PROTOCOL=SASL_SSL
SASL_MECHANISM=PLAIN
USERNAME=kafka_user
PASSWORD=kafka_pass
GROUP=etl_group
TOPIC=lmnh
```