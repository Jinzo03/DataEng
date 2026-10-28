FROM apache/airflow:2.8.1-python3.10

USER airflow

# Main env: OpenLineage provider + scipy for drift checks (pinned via Airflow's constraints)
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.10.txt" \
    apache-airflow-providers-openlineage scipy

# dbt and Soda live in their own virtualenvs so their dependencies never clash with Airflow's.
# PIP_USER=false: the Airflow image defaults to `pip --user`, which is invalid inside a venv.
RUN python -m venv /home/airflow/dbt_venv \
 && PIP_USER=false /home/airflow/dbt_venv/bin/pip install --no-cache-dir \
    dbt-postgres==1.7.9 openlineage-dbt

RUN python -m venv /home/airflow/soda_venv \
 && PIP_USER=false /home/airflow/soda_venv/bin/pip install --no-cache-dir \
    soda-core-postgres