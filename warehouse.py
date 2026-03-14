import pandas as pd
from sqlalchemy import create_engine

# PostgreSQL connection string
engine = create_engine('postgresql+psycopg2://postgres:1234@localhost:5432/ai_bi_project')

# Path to your CSV file
# Method 1 --------------------<,<<<<<<<<<<<<

import os

csv_folder = 'dataset/'  # Folder containing CSV files

for file in os.listdir(csv_folder):
    if file.endswith('.csv'):
        df = pd.read_csv(os.path.join(csv_folder, file))
        table_name = os.path.splitext(file)[0]  # Use filename as table name
        df.to_sql(
            table_name,
            engine,
            schema='raw',       # ✅ specify schema
            if_exists='replace',
            index=False,
            chunksize=5000
        )
        print(f"Created table: {table_name} with {len(df)} rows")

# method 2 --------------------<,<<<<<<<<<<<<
# # Customer data push in pgsql
# customer = pd.read_csv('dataset/customer.csv')
# customer.to_sql('customer', engine, if_exists='replace', index=False)

# # Inventory data push in pgsql
# inventory = pd.read_csv('dataset/inventory.csv')
# inventory.to_sql('inventory', engine, if_exists='replace', index=False)

# # Marketing data push in pgsql
# marketing_campaign = pd.read_csv('dataset/marketing_campaign.csv')
# marketing_campaign.to_sql('marketing_campaign', engine, if_exists='replace', index=False)


# # order data push in pgsql
# orders = pd.read_csv('dataset/order.csv')
# orders.to_sql('orders', engine, if_exists='replace', index=False)
# # order item data push in pgsql
# order_items = pd.read_csv('dataset/order_item.csv')
# order_items.to_sql('order_items', engine, if_exists='replace', index=False)
 
# # payment data push in pgsql
# payments = pd.read_csv('dataset/payments.csv')
# payments.to_sql('payments', engine, if_exists='replace', index=False)

# # pricing_history data push in pgsql
# pricing_history = pd.read_csv('dataset/pricing_history.csv')
# pricing_history.to_sql('pricing_history', engine, if_exists='replace', index=False)

# # products data push in pgsql
# products = pd.read_csv('dataset/products.csv')
# products.to_sql('products', engine, if_exists='replace', index=False)

# # shipments data push in pgsql
# shipments = pd.read_csv('dataset/shipments.csv')
# shipments.to_sql('shipments', engine, if_exists='replace', index=False)

# # vendors data push in pgsql
# vendors = pd.read_csv('dataset/vendors.csv')
# vendors.to_sql('vendors', engine, if_exists='replace', index=False)

# # warehouses data push in pgsql
# warehouses = pd.read_csv('dataset/warehouses.csv')
# warehouses.to_sql('warehouses', engine, if_exists='replace', index=False)

