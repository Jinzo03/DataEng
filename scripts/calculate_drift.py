import pandas as pd
from scipy.stats import ks_2samp
from sqlalchemy import create_engine

ENGINE = create_engine('postgresql://de_user:de_password@postgres:5432/warehouse')

def compute_ks_drift():
    # Load baseline vs current batch
    baseline = pd.read_sql("SELECT amount FROM marts.fct_sales WHERE order_date < NOW() - INTERVAL '7 days'", ENGINE)
    current = pd.read_sql("SELECT amount FROM marts.fct_sales WHERE order_date >= NOW() - INTERVAL '7 days'", ENGINE)
    
    # Perform Kolmogorov-Smirnov test
    stat, p_value = ks_2samp(baseline['amount'], current['amount'])
    is_drifted = bool(p_value < 0.05)
    
    # Log drift result to Postgres for Grafana tracking
    df_res = pd.DataFrame([{
        'check_time': pd.Timestamp.now(),
        'feature': 'amount',
        'p_value': float(p_value),
        'drift_detected': is_drifted
    }])
    df_res.to_sql('drift_metrics', ENGINE, schema='monitoring', if_exists='append', index=False)

if __name__ == "__main__":
    compute_ks_drift()