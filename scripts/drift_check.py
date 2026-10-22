"""Compare one batch of raw.orders against a trailing baseline and log KS-test results."""
import argparse
import os
from datetime import date, timedelta

import pandas as pd
from scipy.stats import ks_2samp
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

FEATURES = ["quantity", "unit_price"]
ALPHA = 0.05          # p < ALPHA -> flagged as drifted
BASELINE_DAYS = 30    # baseline = the 30 days of batches before this one
MIN_ROWS = 30         # skip a feature when either sample is too small to test


def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("WAREHOUSE_HOST", "postgres"),
        port=5432,
        database=os.environ["POSTGRES_DB"],
    )
    return create_engine(url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-date", required=True)
    batch_date = date.fromisoformat(parser.parse_args().batch_date)
    start = batch_date - timedelta(days=BASELINE_DAYS)

    engine = get_engine()
    cols = ", ".join(FEATURES)
    current = pd.read_sql(
        text(f"SELECT {cols} FROM raw.orders WHERE batch_date = :d"),
        engine, params={"d": batch_date},
    )
    baseline = pd.read_sql(
        text(f"SELECT {cols} FROM raw.orders WHERE batch_date >= :s AND batch_date < :d"),
        engine, params={"s": start, "d": batch_date},
    )

    rows = []
    for feat in FEATURES:
        cur, base = current[feat].dropna(), baseline[feat].dropna()
        if len(cur) < MIN_ROWS or len(base) < MIN_ROWS:
            print(f"[skip] {feat}: not enough data (current={len(cur)}, baseline={len(base)})")
            continue
        stat, p = ks_2samp(cur, base)
        rows.append({
            "batch_date": batch_date, "feature": feat, "test_name": "ks_2samp",
            "statistic": float(stat), "p_value": float(p), "drifted": bool(p < ALPHA),
            "n_current": len(cur), "n_baseline": len(base),
        })
        print(f"[{'DRIFT' if p < ALPHA else 'ok'}] {feat}: KS={stat:.4f}, p={p:.4g}")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM monitoring.drift_metrics WHERE batch_date = :d"), {"d": batch_date})
        if rows:
            conn.execute(text("""
                INSERT INTO monitoring.drift_metrics
                (batch_date, feature, test_name, statistic, p_value, drifted, n_current, n_baseline)
                VALUES (:batch_date, :feature, :test_name, :statistic, :p_value, :drifted, :n_current, :n_baseline)
            """), rows)


if __name__ == "__main__":
    main()
