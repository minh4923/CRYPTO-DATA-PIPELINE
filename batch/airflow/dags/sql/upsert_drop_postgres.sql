CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS core.{{ var.json.bybit.product | lower }} (
    timestamp TIMESTAMP PRIMARY KEY,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume NUMERIC
);

INSERT INTO core.{{ var.json.bybit.product }} (timestamp, open, high, low, close, volume)
SELECT timestamp, open, high, low, close, volume FROM staging.{{ var.json.bybit.product }}{{ ds_nodash }}
ON CONFLICT(timestamp) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume;

DROP TABLE staging.{{ var.json.bybit.product }}{{ ds_nodash }};