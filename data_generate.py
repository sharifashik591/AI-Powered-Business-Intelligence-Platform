import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
from tqdm import tqdm
import duckdb

fake = Faker()

# ---------- CONFIG ----------
N_CUSTOMERS = 100_000
N_PRODUCTS = 5_000
N_VENDORS = 200
N_WAREHOUSES = 10
N_ORDERS = 1_000_000

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)

REGIONS = ["Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna", "Barishal", "Rangpur", "Mymensingh"]
CATEGORIES = ["Rice", "Vegetables", "Fruits", "Fish", "Meat", "Spices", "Oil", "Dairy", "Snacks"]
PAYMENT_METHODS = ["COD", "bKash", "Nagad", "Rocket", "Card", "Bank Transfer"]

# ---------- UTILS ----------

def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

# ---------- GENERATORS ----------

def generate_customers(n):
    data = []
    for i in range(1, n+1):
        data.append({
            "customer_id": i,
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.msisdn()[:11],
            "region": random.choice(REGIONS),
            "signup_date": random_date(START_DATE, END_DATE)
        })
    return pd.DataFrame(data)

def generate_vendors(n):
    data = []
    for i in range(1, n+1):
        data.append({
            "vendor_id": i,
            "company_name": fake.company(),
            "region": random.choice(REGIONS),
            "rating": round(random.uniform(3.0, 5.0), 2)
        })
    return pd.DataFrame(data)

def generate_products(n, vendors):
    data = []
    for i in range(1, n+1):
        base_price = random.randint(20, 800)
        data.append({
            "product_id": i,
            "product_name": fake.word().capitalize(),
            "category": random.choice(CATEGORIES),
            "vendor_id": random.choice(vendors["vendor_id"]),
            "base_price": base_price,
            "cost_price": round(base_price * random.uniform(0.6, 0.85), 2)
        })
    return pd.DataFrame(data)

def generate_warehouses(n):
    data = []
    for i in range(1, n+1):
        data.append({
            "warehouse_id": i,
            "warehouse_name": f"Warehouse-{i}",
            "region": random.choice(REGIONS),
            "capacity": random.randint(50_000, 200_000)
        })
    return pd.DataFrame(data)

def generate_inventory(products, warehouses):
    data = []
    for _, p in products.iterrows():
        for _, w in warehouses.iterrows():
            data.append({
                "product_id": p["product_id"],
                "warehouse_id": w["warehouse_id"],
                "stock_qty": max(0, int(np.random.normal(500, 200)))
            })
    return pd.DataFrame(data)

def generate_orders(n, customers):
    data = []
    for i in tqdm(range(1, n+1)):
        data.append({
            "order_id": i,
            "customer_id": random.choice(customers["customer_id"]),
            "order_date": random_date(START_DATE, END_DATE),
            "region": random.choice(REGIONS),
            "payment_method": random.choice(PAYMENT_METHODS),
            "status": random.choice(["Completed", "Cancelled", "Returned", "Pending"])
        })
    return pd.DataFrame(data)

def generate_order_items(orders, products):
    data = []
    item_id = 1
    for _, o in tqdm(orders.iterrows(), total=len(orders)):
        for _ in range(random.randint(1, 5)):
            p = products.sample(1).iloc[0]
            qty = random.randint(1, 10)
            data.append({
                "order_item_id": item_id,
                "order_id": o["order_id"],
                "product_id": p["product_id"],
                "quantity": qty,
                "unit_price": p["base_price"],
                "total_price": round(qty * p["base_price"], 2)
            })
            item_id += 1
    return pd.DataFrame(data)

def generate_payments(orders, order_items):
    total_amount = order_items.groupby("order_id")["total_price"].sum().reset_index()
    df = orders.merge(total_amount, on="order_id", how="left")
    df["payment_status"] = np.where(df["status"] == "Completed", "Paid", "Unpaid")
    df["payment_date"] = df["order_date"] + pd.to_timedelta(np.random.randint(0, 3, size=len(df)), unit="D")
    return df[["order_id", "total_price", "payment_method", "payment_status", "payment_date"]]

def generate_shipments(orders, warehouses):
    data = []
    for _, o in tqdm(orders.iterrows(), total=len(orders)):
        ship_days = random.randint(1, 7)
        data.append({
            "order_id": o["order_id"],
            "warehouse_id": random.choice(warehouses["warehouse_id"]),
            "ship_date": o["order_date"] + timedelta(days=ship_days),
            "delivery_date": o["order_date"] + timedelta(days=ship_days + random.randint(1, 3)),
            "status": random.choice(["Delivered", "In Transit", "Delayed"])
        })
    return pd.DataFrame(data)

def generate_pricing_history(products):
    data = []
    for _, p in tqdm(products.iterrows(), total=len(products)):
        date = START_DATE
        price = p["base_price"]
        while date < END_DATE:
            price = round(price * random.uniform(0.95, 1.08), 2)
            data.append({
                "product_id": p["product_id"],
                "price_date": date,
                "price": price
            })
            date += timedelta(days=30)
    return pd.DataFrame(data)

def generate_marketing_campaigns():
    campaigns = ["New Year Sale", "Ramadan Offer", "Eid Campaign", "Monsoon Discount", "Flash Sale"]
    data = []
    for i, c in enumerate(campaigns, start=1):
        data.append({
            "campaign_id": i,
            "campaign_name": c,
            "start_date": random_date(START_DATE, END_DATE),
            "end_date": random_date(START_DATE, END_DATE),
            "budget": random.randint(100_000, 2_000_000)
        })
    return pd.DataFrame(data)

# ---------- PIPELINE ----------

def main():
    print("Generating customers...")
    customers = generate_customers(N_CUSTOMERS)

    print("Generating vendors...")
    vendors = generate_vendors(N_VENDORS)

    print("Generating products...")
    products = generate_products(N_PRODUCTS, vendors)

    print("Generating warehouses...")
    warehouses = generate_warehouses(N_WAREHOUSES)

    print("Generating inventory...")
    inventory = generate_inventory(products, warehouses)

    print("Generating orders...")
    orders = generate_orders(N_ORDERS, customers)

    print("Generating order items...")
    order_items = generate_order_items(orders, products)

    print("Generating payments...")
    payments = generate_payments(orders, order_items)

    print("Generating shipments...")
    shipments = generate_shipments(orders, warehouses)

    print("Generating pricing history...")
    pricing_history = generate_pricing_history(products)

    print("Generating marketing campaigns...")
    campaigns = generate_marketing_campaigns()

    print("Saving CSV files...")
    customers.to_csv("dataset/customers.csv", index=False)
    vendors.to_csv("dataset/vendors.csv", index=False)
    products.to_csv("dataset/products.csv", index=False)
    warehouses.to_csv("dataset/warehouses.csv", index=False)
    inventory.to_csv("dataset/inventory.csv", index=False)
    orders.to_csv("dataset/orders.csv", index=False)
    order_items.to_csv("dataset/order_items.csv", index=False)
    payments.to_csv("dataset/payments.csv", index=False)
    shipments.to_csv("dataset/shipments.csv", index=False)
    pricing_history.to_csv("dataset/pricing_history.csv", index=False)
    campaigns.to_csv("dataset/marketing_campaigns.csv", index=False)

    print("✅ Enterprise synthetic data generation completed.")


    # ------------------------------------ database<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    print("Saving to DuckDB...")
    
    # 1. Connect to a persistent database file
    # This creates 'business_bi.duckdb' in your project folder
    con = duckdb.connect("dataset/business_bi.duckdb")

    # 2. Map your table names to your DataFrame variables
    tables = {
        "customers": customers,
        "vendors": vendors,
        "products": products,
        "warehouses": warehouses,
        "inventory": inventory,
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "shipments": shipments,
        "pricing_history": pricing_history,
        "marketing_campaigns": campaigns
    }

    # 3. Write each DataFrame to a DuckDB table
    for table_name, df in tables.items():
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        print(f"  - Table '{table_name}' stored.")

    # 4. Close the connection
    con.close()

    # You can keep your CSV saves if you want them as backups, 
    # but DuckDB is now your "Source of Truth"
    print("✅ Enterprise synthetic data stored in DuckDB.")


if __name__ == "__main__":
    main()