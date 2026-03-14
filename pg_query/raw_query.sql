-- ======================================================
--  PostgreSQL Staging Layer SQL Script
--  Creates staging schema and all cleaned staging tables
-- ======================================================

-- 1️⃣ Create staging schema
CREATE SCHEMA IF NOT EXISTS staging;

-- 2️⃣ Cleaned Customers
CREATE TABLE staging.cleaned_customers AS
SELECT
    customer_id,
    TRIM(name) AS name,
    LOWER(email) AS email,
    phone,
    region,
    TO_DATE(signup_date, 'YYYY-MM-DD') AS signup_date
FROM raw.customers
WHERE customer_id IS NOT NULL;

-- 3️⃣ Cleaned Inventory
CREATE TABLE staging.cleaned_inventory AS
SELECT
    product_id,
    warehouse_id,
    stock_qty
FROM raw.inventory
WHERE product_id IS NOT NULL
  AND warehouse_id IS NOT NULL
  AND stock_qty >= 0;

-- 4️⃣ Cleaned Marketing Campaigns
CREATE TABLE staging.cleaned_marketing_campaigns AS
SELECT
    campaign_id,
    TRIM(campaign_name) AS campaign_name,
    TO_DATE(start_date, 'YYYY-MM-DD') AS start_date,
    TO_DATE(end_date, 'YYYY-MM-DD') AS end_date,
    budget
FROM raw.marketing_campaigns
WHERE campaign_id IS NOT NULL
  AND start_date IS NOT NULL;

-- 5️⃣ Cleaned Orders
CREATE TABLE staging.cleaned_orders AS
SELECT
    order_id,
    customer_id,
    TO_DATE(order_date, 'YYYY-MM-DD') AS order_date,
    LOWER(region) AS region,
    LOWER(payment_method) AS payment_method,
    LOWER(status) AS status
FROM raw.orders
WHERE order_id IS NOT NULL
  AND customer_id IS NOT NULL;

-- 6️⃣ Cleaned Order Items
CREATE TABLE staging.cleaned_order_items AS
SELECT
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    total_price
FROM raw.order_items
WHERE order_item_id IS NOT NULL
  AND order_id IS NOT NULL
  AND product_id IS NOT NULL;

-- 7️⃣ Cleaned Payments
CREATE TABLE staging.cleaned_payments AS
SELECT
    order_id,
    total_price,
    LOWER(payment_method) AS payment_method,
    LOWER(payment_status) AS payment_status,
    TO_DATE(payment_date, 'YYYY-MM-DD') AS payment_date
FROM raw.payments
WHERE order_id IS NOT NULL;

-- 8️⃣ Cleaned Pricing History
CREATE TABLE staging.cleaned_pricing_history AS
SELECT
    product_id,
    TO_DATE(price_date, 'YYYY-MM-DD') AS price_date,
    price
FROM raw.pricing_history
WHERE product_id IS NOT NULL;

-- 9️⃣ Cleaned Products
CREATE TABLE staging.cleaned_products AS
SELECT
    product_id,
    TRIM(product_name) AS product_name,
    LOWER(category) AS category,
    vendor_id,
    base_price,
    cost_price,
    (base_price - cost_price) AS margin
FROM raw.products
WHERE product_id IS NOT NULL
  AND base_price >= 0
  AND cost_price >= 0;

-- 🔟 Cleaned Shipments
CREATE TABLE staging.cleaned_shipments AS
SELECT
    order_id,
    warehouse_id,
    TO_DATE(ship_date, 'YYYY-MM-DD') AS ship_date,
    TO_DATE(delivery_date, 'YYYY-MM-DD') AS delivery_date,
    LOWER(status) AS status
FROM raw.shipments
WHERE order_id IS NOT NULL
  AND warehouse_id IS NOT NULL;

