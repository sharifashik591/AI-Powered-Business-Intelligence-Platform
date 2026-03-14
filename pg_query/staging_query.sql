-- 1️⃣1️⃣ Cleaned Vendors
CREATE TABLE staging.cleaned_vendors AS
SELECT
    vendor_id,
    TRIM(company_name) AS company_name,
    LOWER(region) AS region,
    rating
FROM raw.vendors
WHERE vendor_id IS NOT NULL;

-- 1️⃣2️⃣ Cleaned Warehouses
CREATE TABLE staging.cleaned_warehouses AS
SELECT
    warehouse_id,
    TRIM(warehouse_name) AS warehouse_name,
    LOWER(region) AS region,
    capacity
FROM raw.warehouses
WHERE warehouse_id IS NOT NULL
  AND capacity >= 0;

-- ======================================================
--  ✅ Staging Layer Complete
--  All raw tables are cleaned and stored in staging schema
-- ======================================================