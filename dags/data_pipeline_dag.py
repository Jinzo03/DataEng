from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

from scripts.calculate_drift import compute_ks_drift

from scripts.calculate_drift import compute_ks_drift

with DAG(
    dag_id='data_quality_observability_pipeline',
    start_date=datetime(2026, 1, 1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    ingest_task = BashOperator(
        task_id='ingest_raw_data',
        bash_command='python /opt/airflow/scripts/ingest_data.py'
    )

    soda_raw_check = BashOperator(
        task_id='soda_check_raw',
        bash_command='soda scan -d warehouse -c /opt/airflow/soda/configuration.yml /opt/airflow/soda/checks/raw_checks.yml'
    )

    dbt_run = BashOperator(
        task_id='dbt_run_transformations',
        bash_command='cd /opt/airflow/dbt_project && dbt run --profiles-dir .'
    )

    soda_mart_check = BashOperator(
        task_id='soda_check_marts',
        bash_command='soda scan -d warehouse -c /opt/airflow/soda/configuration.yml /opt/airflow/soda/checks/mart_checks.yml'
    )

    drift_check = PythonOperator(
        task_id='detect_data_drift',
        python_callable=compute_ks_drift
    )

    ingest_task >> soda_raw_check >> dbt_run >> soda_mart_check >> drift_check