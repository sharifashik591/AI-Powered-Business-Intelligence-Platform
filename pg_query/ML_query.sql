-- ML-ready feature views in Postgres

-- Daily demand per product + region
CREATE OR REPLACE VIEW analytics.ml_daily_demand AS
SELECT
  d.full_date,
  f.product_id,
  c.region,
  SUM(f.quantity) AS daily_qty,
  SUM(f.revenue)  AS daily_revenue,
  AVG(p.base_price) AS base_price,
  AVG(p.cost_price) AS cost_price
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d      ON f.date_id = d.date_id
JOIN warehouse.dim_customer c  ON f.customer_id = c.customer_id
JOIN warehouse.dim_product p   ON f.product_id = p.product_id
GROUP BY d.full_date, f.product_id, c.region;



-- Inventory snapshot
CREATE OR REPLACE VIEW analytics.ml_inventory AS
SELECT
  fi.product_id,
  dw.region AS warehouse_region,
  SUM(fi.stock_qty) AS stock_qty
FROM warehouse.fact_inventory fi
JOIN warehouse.dim_warehouse dw ON fi.warehouse_id = dw.warehouse_id
GROUP BY fi.product_id, dw.region;


-- Payments daily (financial signal)
CREATE OR REPLACE VIEW analytics.ml_daily_payments AS
SELECT
  d.full_date,
  SUM(fp.amount_paid) AS total_paid
FROM warehouse.fact_payments fp
JOIN warehouse.dim_date d ON fp.date_id = d.date_id
GROUP BY d.full_date;

