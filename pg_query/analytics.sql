-- =====================================================
-- ANALYTICS KPI LAYER — SINGLE FILE (PostgreSQL)
-- =====================================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- =====================================================
-- 1️⃣ DAILY REVENUE + PROFIT
-- =====================================================

DROP TABLE IF EXISTS analytics.daily_revenue;

CREATE TABLE analytics.daily_revenue AS
SELECT
    d.full_date,
    SUM(f.revenue) AS total_revenue,
    SUM(f.profit)  AS total_profit,
    COUNT(DISTINCT f.order_id) AS total_orders
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON f.date_id = d.date_id
GROUP BY d.full_date;


-- =====================================================
-- 2️⃣ CORE BUSINESS KPIs
-- =====================================================

DROP TABLE IF EXISTS analytics.core_kpis;

CREATE TABLE analytics.core_kpis AS
SELECT
    SUM(f.revenue)                               AS revenue,
    SUM(f.profit)                               AS gross_margin,
    COUNT(DISTINCT f.order_id)                  AS total_orders,
    SUM(f.quantity)                             AS total_units_sold,
    COUNT(DISTINCT f.customer_id)               AS total_customers
FROM warehouse.fact_sales f;


-- =====================================================
-- 3️⃣ CUSTOMER LIFETIME VALUE (CLV)
-- =====================================================

DROP TABLE IF EXISTS analytics.customer_clv;

CREATE TABLE analytics.customer_clv AS
SELECT
    c.customer_id,
    c.name,
    SUM(f.revenue) AS lifetime_value,
    COUNT(DISTINCT f.order_id) AS total_orders
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c 
    ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;


-- =====================================================
-- 4️⃣ REPEAT PURCHASE RATE
-- =====================================================

DROP TABLE IF EXISTS analytics.repeat_purchase_rate;

CREATE TABLE analytics.repeat_purchase_rate AS
SELECT
    COUNT(*) FILTER (WHERE order_count > 1)::float
    / COUNT(*) * 100 AS repeat_purchase_rate_pct
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM warehouse.fact_sales
    GROUP BY customer_id
) x;


-- =====================================================
-- 5️⃣ INVENTORY TURNOVER & STOCKOUT RATE
-- =====================================================

DROP TABLE IF EXISTS analytics.inventory_kpis;

CREATE TABLE analytics.inventory_kpis AS
SELECT
    fi.product_id,
    dp.product_name,

    SUM(fi.stock_qty) AS total_stock,
    COALESCE(SUM(fs.quantity),0) AS total_sold,

    CASE 
        WHEN SUM(fi.stock_qty) = 0 THEN 1 
        ELSE 0 
    END AS stockout_flag,

    COALESCE(
        SUM(fs.quantity)::float / NULLIF(SUM(fi.stock_qty),0),0
    ) AS inventory_turnover

FROM warehouse.fact_inventory fi
LEFT JOIN warehouse.fact_sales fs 
    ON fi.product_id = fs.product_id
JOIN warehouse.dim_product dp 
    ON fi.product_id = dp.product_id
GROUP BY fi.product_id, dp.product_name;


-- =====================================================
-- 6️⃣ DELIVERY PERFORMANCE KPIs
-- =====================================================

DROP TABLE IF EXISTS analytics.delivery_kpis;

CREATE TABLE analytics.delivery_kpis AS
SELECT
    dw.warehouse_name,

    AVG(
        dd_delivery.full_date::date - 
        dd_ship.full_date::date
    ) AS avg_delivery_days,

    COUNT(fs.order_id) AS total_shipments

FROM warehouse.fact_shipments fs
JOIN warehouse.dim_warehouse dw 
    ON fs.warehouse_id = dw.warehouse_id
JOIN warehouse.dim_date dd_ship 
    ON fs.ship_date_id = dd_ship.date_id
JOIN warehouse.dim_date dd_delivery 
    ON fs.delivery_date_id = dd_delivery.date_id
GROUP BY dw.warehouse_name;




-- =====================================================
-- DONE
-- =====================================================