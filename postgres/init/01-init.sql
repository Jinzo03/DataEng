-- Runs once, on first start of an empty pgdata volume.
CREATE DATABASE airflow;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- No primary key on purpose: raw must accept bad data so Soda can catch it.
CREATE TABLE IF NOT EXISTS raw.orders (
    order_id    BIGINT,
    customer_id BIGINT,
    product_id  BIGINT,
    quantity    INT,
    unit_price  NUMERIC(12,2),
    order_ts    TIMESTAMP,
    status      TEXT,
    batch_date  DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_raw_orders_batch ON raw.orders (batch_date);

CREATE TABLE IF NOT EXISTS monitoring.drift_metrics (
    id          BIGSERIAL PRIMARY KEY,
    batch_date  DATE NOT NULL,
    feature     TEXT NOT NULL,
    test_name   TEXT NOT NULL,
    statistic   DOUBLE PRECISION,
    p_value     DOUBLE PRECISION,
    drifted     BOOLEAN,
    n_current   INT,
    n_baseline  INT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_drift_batch ON monitoring.drift_metrics (batch_date);
