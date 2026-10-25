from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

INCOMING = Path("/opt/airflow/data/incoming")
SODA_BIN = "/home/airflow/soda_venv/bin/soda"
SODA_DIR = "/opt/airflow/soda"
DBT_OL = "/home/airflow/dbt_venv/bin/dbt-ol"
DBT_DIR = "/opt/airflow/dbt_project"


def ingest_orders(ds: str, **_) -> None:
    """Load orders_<ds>.csv into raw.orders. Idempotent: replaces that batch on re-run."""
    path = INCOMING / f"orders_{ds}.csv"
    if not path.exists():
        raise FileNotFoundError(f"No batch file for {ds}: {path}")

    df = pd.read_csv(path, parse_dates=["order_ts"])
    df["batch_date"] = date.fromisoformat(ds)

    engine = PostgresHook(postgres_conn_id="warehouse").get_sqlalchemy_engine()
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM raw.orders WHERE batch_date = %s", (ds,))
        df.to_sql("orders", conn, schema="raw", if_exists="append",
                  index=False, method="multi", chunksize=1000)


def soda_scan(data_source: str, checks_file: str) -> str:
    # Non-zero exit on failed checks -> task fails -> downstream tasks are skipped
    return (
        f"{SODA_BIN} scan -d {data_source} "
        f"-c {SODA_DIR}/configuration.yml "
        f"-v BATCH_DATE={{{{ ds }}}} "
        f"{SODA_DIR}/checks/{checks_file}"
    )


with DAG(
    dag_id="orders_pipeline",
    description="CSV -> raw -> Soda -> dbt -> Soda -> drift, with OpenLineage to Marquez",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["pfe", "data-quality"],
) as dag:

    ingest = PythonOperator(task_id="ingest_orders", python_callable=ingest_orders)

    soda_raw = BashOperator(
        task_id="soda_check_raw",
        bash_command=soda_scan("warehouse_raw", "raw_orders.yml"),
    )

    # dbt-ol = dbt wrapped by OpenLineage, so model-level lineage reaches Marquez
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"{DBT_OL} run --project-dir {DBT_DIR} --profiles-dir {DBT_DIR} "
            "--target-path /tmp/dbt_target --log-path /tmp/dbt_logs"
        ),
    )

    soda_marts = BashOperator(
        task_id="soda_check_marts",
        bash_command=soda_scan("warehouse_marts", "marts_fct_sales.yml"),
    )

    drift = BashOperator(
        task_id="drift_detection",
        bash_command="python /opt/airflow/scripts/drift_check.py --batch-date {{ ds }}",
    )

    ingest >> soda_raw >> dbt_run >> soda_marts >> drift
