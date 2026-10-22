SELECT
    id AS order_id,
    customer_id,
    amount::FLOAT AS amount,
    order_date::DATE AS order_date
FROM {{ source('raw_data', 'orders') }}