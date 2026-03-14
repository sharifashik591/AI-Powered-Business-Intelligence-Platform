-- Run bash comand
-- psql -U postgres -d ai_bi_project -f warehouse_layer_fixed.sql

-- ======================================================
-- PostgreSQL Warehouse Layer SQL Script (Fixed)
-- Builds warehouse tables from staging layer
-- ======================================================

-- 1️⃣ Create warehouse schema
CREATE SCHEMA IF NOT EXISTS warehouse;

-- 2️⃣ Dimension Tables

-- dim_customer
CREATE TABLE IF NOT EXISTS warehouse.dim_customer AS
SELECT
    customer_id,
    name,
    email,
    region,
    signup_date
FROM staging.cleaned_customers;

-- dim_product
CREATE TABLE IF NOT EXISTS warehouse.dim_product AS
SELECT
    product_id,
    product_name,
    category,
    vendor_id,
    base_price,
    cost_price,
    margin
FROM staging.cleaned_products;

-- dim_vendor
CREATE TABLE IF NOT EXISTS warehouse.dim_vendor AS
SELECT
    vendor_id,
    company_name,
    region,
    rating
FROM staging.cleaned_vendors;

-- dim_warehouse
CREATE TABLE IF NOT EXISTS warehouse.dim_warehouse AS
SELECT
    warehouse_id,
    warehouse_name,
    region,
    capacity
FROM staging.cleaned_warehouses;

-- dim_date
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_id INT PRIMARY KEY,
    full_date DATE,
    day INT,
    month INT,
    year INT,
    quarter INT,
    weekday VARCHAR(10),
    is_weekend BOOLEAN
);

-- Populate dim_date using generate_series
INSERT INTO warehouse.dim_date (date_id, full_date, day, month, year, quarter, weekday, is_weekend)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT,
    d,
    EXTRACT(DAY FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    EXTRACT(YEAR FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    TO_CHAR(d, 'Day'),
    CASE WHEN EXTRACT(DOW FROM d) IN (0,6) THEN TRUE ELSE FALSE END
FROM generate_series('2023-01-01'::DATE, '2030-12-31'::DATE, '1 day') AS d;

-- 3️⃣ Fact Tables

-- fact_sales
CREATE TABLE IF NOT EXISTS warehouse.fact_sales AS
SELECT
    oi.order_id,
    oi.product_id,
    o.customer_id,
    TO_CHAR(o.order_date, 'YYYYMMDD')::INT AS date_id,
    oi.quantity,
    oi.total_price AS revenue,
    (oi.quantity * p.cost_price) AS cost,
    (oi.total_price - (oi.quantity * p.cost_price)) AS profit,
    o.payment_method,
    o.status AS order_status
FROM staging.cleaned_order_items oi
JOIN staging.cleaned_orders o ON oi.order_id = o.order_id
JOIN staging.cleaned_products p ON oi.product_id = p.product_id;

-- fact_payments
CREATE TABLE IF NOT EXISTS warehouse.fact_payments AS
SELECT
    p.order_id,
    o.customer_id,
    TO_CHAR(p.payment_date, 'YYYYMMDD')::INT AS date_id,
    p.total_price AS amount_paid,
    p.payment_status,
    p.payment_method
FROM staging.cleaned_payments p
JOIN staging.cleaned_orders o ON p.order_id = o.order_id;

-- fact_shipments (fixed days_to_deliver calculation)
CREATE TABLE IF NOT EXISTS warehouse.fact_shipments AS
SELECT
    s.order_id,
    s.warehouse_id,
    TO_CHAR(s.ship_date, 'YYYYMMDD')::INT AS ship_date_id,
    TO_CHAR(s.delivery_date, 'YYYYMMDD')::INT AS delivery_date_id,
    (s.delivery_date - s.ship_date) AS days_to_deliver,
    s.status
FROM staging.cleaned_shipments s;

-- fact_inventory
CREATE TABLE IF NOT EXISTS warehouse.fact_inventory AS
SELECT
    i.product_id,
    i.warehouse_id,
    stock_qty
FROM staging.cleaned_inventory i;

-- 4️⃣ Indexes for Performance

-- fact_sales indexes
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON warehouse.fact_sales(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON warehouse.fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON warehouse.fact_sales(customer_id);

-- fact_payments indexes
CREATE INDEX IF NOT EXISTS idx_fact_payments_date ON warehouse.fact_payments(date_id);

-- fact_shipments indexes
CREATE INDEX IF NOT EXISTS idx_fact_shipments_shipdate ON warehouse.fact_shipments(ship_date_id);
CREATE INDEX IF NOT EXISTS idx_fact_shipments_deliverydate ON warehouse.fact_shipments(delivery_date_id);

-- 5️⃣ Analytics Layer (Materialized Views)

CREATE SCHEMA IF NOT EXISTS analytics;

-- Daily revenue view
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.daily_revenue AS
SELECT
    date_id,
    SUM(revenue) AS total_revenue,
    SUM(profit) AS total_profit
FROM warehouse.fact_sales
GROUP BY date_id;

-- Daily payments view
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.daily_payments AS
SELECT
    date_id,
    SUM(amount_paid) AS total_paid
FROM warehouse.fact_payments
GROUP BY date_id;

-- ======================================================
-- ✅ Warehouse Layer Complete
--  Dimension & Fact tables ready for BI / Analytics
-- ======================================================