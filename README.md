# PFE data-quality & observability pipeline

    docker compose up -d --build

| Service        | URL                     | Login        |
|----------------|-------------------------|--------------|
| Airflow        | http://localhost:8080   | admin / admin |
| Marquez UI     | http://localhost:3000   | -            |
| Grafana        | http://localhost:3001   | admin / admin |
| Postgres       | localhost:5432          | see .env     |

## Demo run
    python scripts/generate_sample_data.py 2026-10-01 --days 10        # 10 clean batches
    # Trigger backfills in Airflow (or: docker compose exec airflow-scheduler airflow dags backfill orders_pipeline -s 2026-10-01 -e 2026-10-10)
    python scripts/generate_sample_data.py 2026-10-11 --drift          # drifted batch -> shows up in Grafana
    python scripts/generate_sample_data.py 2026-10-12 --bad            # bad batch -> Soda blocks dbt

## Grafana query (time series of p-values)
    SELECT batch_date AS time, feature AS metric, p_value
    FROM monitoring.drift_metrics
    WHERE $__timeFilter(batch_date)
    ORDER BY 1
