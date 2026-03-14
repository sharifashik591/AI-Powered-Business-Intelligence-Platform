import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch MySQL credentials from .env
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "flagship_project")

# 1. Setup Connection String
# Format: mysql+mysqlconnector://user:password@host:port/dbname
DB_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
engine = create_engine(DB_URL)

# 2. Define the files and their corresponding table names
data_map = {
    'vendors': 'dataset/vendors.csv',
    'customers': 'dataset/customers.csv',
    'products': 'dataset/products.csv',
    'warehouses': 'dataset/warehouses.csv',
    'inventory': 'dataset/inventory.csv',
    'orders': 'dataset/orders.csv',
    'order_items': 'dataset/order_items.csv',
    'payments': 'dataset/payments.csv',
    'shipments': 'dataset/shipments.csv',
    'pricing_history': 'dataset/pricing_history.csv',
    'marketing_campaigns': 'dataset/marketing_campaigns.csv'
}

def upload_data():
    try:
        # Connect to the database
        with engine.begin() as connection:
            print("✅ Connection established. Starting upload...")

            for table_name, file_path in data_map.items():
                if os.path.exists(file_path):
                    try:
                        print(f"⌛ Uploading {file_path} to table '{table_name}'...")
                        
                        # Use chunksize to send data in smaller bites (e.g., 50,000 rows at a time)
                        # Use method='multi' for faster insertion if your connector supports it
                        df = pd.read_csv(file_path)
                        
                        df.to_sql(
                            table_name, 
                            con=connection, 
                            if_exists='replace', 
                            index=False, 
                            chunksize=50000,  # Sends 50k rows at a time
                            method='multi'     # Optimizes the INSERT statement
                        )
                        
                        print(f"   ✔️ Successfully uploaded {len(df)} rows.")
                    except Exception as e:
                        print(f"   ❌ Error uploading {table_name}: {e}")
                        # No need to manually rollback here because 'engine.begin()' 
                        # handles it automatically if an error occurs!
                else:
                    print(f"   ⚠️ File not found: {file_path}")

        print("\n🚀 All tasks processed.")

    except Exception as connection_error:
        print(f"❌ Failed to connect to MySQL: {connection_error}")

if __name__ == "__main__":
    upload_data()