import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Fetch credentials
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db_engine():
    """Creates a SQLAlchemy engine for PostgreSQL."""
    # Construct the PostgreSQL connection URL
    connection_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Create the engine
    engine = create_engine(connection_url)
    return engine

def fetch_forecasting_data():
    """Queries the data warehouse and returns a Pandas DataFrame."""
    engine = get_db_engine()
    query = """
        SELECT 
            d.full_date AS ds, 
            p.category,
            c.region,                
            SUM(oi.quantity) AS y
        FROM warehouse.fact_sales oi
        JOIN warehouse.dim_date d ON oi.date_id = d.date_id        
        JOIN warehouse.dim_customer c ON oi.customer_id = c.customer_id 
        JOIN warehouse.dim_product p ON oi.product_id = p.product_id
        GROUP BY 1, 2, 3
        ORDER BY 1 ASC;
    """

    # 3. Write your analytical SQL query (joining Fact and Dim tables)
    
    print("Executing query and fetching data...")
    
    # 4. Execute the query directly into a Pandas DataFrame
    try:
        df = pd.read_sql(query, con=engine)
        print(f"✅ Success! Loaded {len(df)} rows into the DataFrame.")
        return df
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

# --- Run the function ---
if __name__ == "__main__":
    sales_df = fetch_forecasting_data()
    
    if sales_df is not None:
        # Check the first 5 rows to verify it worked
        print(sales_df.head())
        
        # Optional: Save to CSV as a backup or for offline modeling
        sales_df.to_csv("ML_Layer/Demand_Forecasting/warehouse_sales_export.csv", index=False)