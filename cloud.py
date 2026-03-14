import pandas as pd
import os
from dotenv import load_dotenv
from cloudflare import Cloudflare

load_dotenv()

# Credentials
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
DATABASE_ID = os.getenv("CLOUDFLARE_DATABASE_ID")

client = Cloudflare(api_token=CLOUDFLARE_API_TOKEN)

def get_sqlite_type(dtype):
    """Maps Pandas dtypes to SQLite types."""
    if "int" in str(dtype):
        return "INTEGER"
    if "float" in str(dtype):
        return "REAL"
    return "TEXT"

def flush_csv_to_d1(file_path, table_name):
    df = pd.read_csv(file_path)
    
    # --- AUTOMATIC TABLE CREATION ---
    columns = []
    for col_name, dtype in df.dtypes.items():
        # Sanitize column name (remove spaces/special chars)
        safe_name = col_name.replace(" ", "_").replace("-", "_")
        sql_type = get_sqlite_type(dtype)
        columns.append(f"{safe_name} {sql_type}")
    
    schema = ", ".join(columns)
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema});"
    
    print(f"Ensuring table '{table_name}' exists with schema...")
    client.d1.database.raw(
        database_id=DATABASE_ID,
        account_id=ACCOUNT_ID,
        sql=create_sql
    )
    # --------------------------------

    chunk_size = 100 
    total_rows = len(df)
    print(f"Starting upload of {total_rows} rows to '{table_name}'...")

    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        sql_list = []
        for _, row in chunk.iterrows():
            formatted_values = []
            for v in row.values:
                if pd.isna(v):
                    formatted_values.append("NULL")
                elif isinstance(v, (int, float)):
                    formatted_values.append(str(v))
                else:
                    safe_val = str(v).replace("'", "''")
                    formatted_values.append(f"'{safe_val}'")
            
            sql_list.append(f"INSERT INTO {table_name} VALUES ({', '.join(formatted_values)});")
        
        try:
            client.d1.database.raw(
                database_id=DATABASE_ID,
                account_id=ACCOUNT_ID,
                sql="\n".join(sql_list)
            )
            if (i + chunk_size) % 1000 == 0 or (i + chunk_size) >= total_rows:
                print(f"Progress: {min(i + chunk_size, total_rows)} / {total_rows} rows uploaded.")
        except Exception as e:
            print(f"Error at row {i}: {e}")
            break 

# Run the function
# flush_csv_to_d1('dataset/customers.csv', 'customers')
flush_csv_to_d1('dataset/vendors.csv', 'vendors')
flush_csv_to_d1('dataset/products.csv', 'products')
flush_csv_to_d1('dataset/warehouses.csv', 'warehouses')
flush_csv_to_d1('dataset/inventory.csv', 'inventory')
flush_csv_to_d1('dataset/orders.csv', 'orders')
flush_csv_to_d1('dataset/order_items.csv', 'order_items')
flush_csv_to_d1('dataset/payments.csv', 'payments')
flush_csv_to_d1('dataset/shipments.csv', 'shipments')
flush_csv_to_d1('dataset/pricing_history.csv', 'pricing_history')
flush_csv_to_d1('dataset/marketing_campaigns.csv', 'marketing_campaigns')   