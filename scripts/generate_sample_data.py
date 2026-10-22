"""Generate demo CSV batches.  Usage: python scripts/generate_sample_data.py 2026-10-01 [--days 10] [--drift] [--bad]"""
import argparse
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "incoming"


def write_batch(day: date, n: int, drift: bool, bad: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"orders_{day.isoformat()}.csv"
    base_id = int(day.strftime("%Y%m%d")) * 10_000
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "product_id", "quantity", "unit_price", "order_ts", "status"])
        for i in range(n):
            qty = random.randint(1, 5) if not drift else random.randint(4, 15)
            price = round(random.uniform(5, 100) * (1.8 if drift else 1.0), 2)
            ts = datetime.combine(day, datetime.min.time()) + timedelta(seconds=random.randint(0, 86399))
            status = random.choices(["completed", "pending", "cancelled"], [0.8, 0.1, 0.1])[0]
            w.writerow([base_id + i, random.randint(1, 500), random.randint(1, 80), qty, price, ts.isoformat(sep=" "), status])
        if bad:  # duplicate id + negative quantity: should make Soda fail the raw check
            w.writerow([base_id, 1, 1, -3, 10.0, f"{day} 10:00:00", "completed"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("start")
    p.add_argument("--days", type=int, default=1)
    p.add_argument("--rows", type=int, default=500)
    p.add_argument("--drift", action="store_true", help="shift quantity/price distributions (last day only)")
    p.add_argument("--bad", action="store_true", help="inject bad rows (last day only)")
    a = p.parse_args()
    s = date.fromisoformat(a.start)
    for d in range(a.days):
        last = d == a.days - 1
        write_batch(s + timedelta(days=d), a.rows, a.drift and last, a.bad and last)
