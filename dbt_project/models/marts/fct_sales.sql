select
    order_id,
    customer_id,
    product_id,
    quantity,
    unit_price,
    round(quantity * unit_price, 2) as revenue,
    order_ts::date                  as order_date,
    batch_date
from {{ source('raw', 'orders') }}
where status <> 'cancelled'
