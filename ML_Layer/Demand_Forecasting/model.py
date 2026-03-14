import pandas as pd
import os

# Get the directory where model.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "warehouse_sales_export.csv")

df = pd.read_csv(file_path)
# df['order_date'] = pd.to_datetime(df['order_date'])

print(df.head())
print(df.info())
print(df.describe())


from IPython.core.display_functions import display
# Extract time-based features
df['day_of_week'] = df['order_date'].dt.dayofweek
df['month'] = df['order_date'].dt.month
df['quarter'] = df['order_date'].dt.quarter

# Lag features
df['lag_1'] = df['y'].shift(1)
df['lag_7'] = df['y'].shift(7)
df['lag_30'] = df['y'].shift(30)

# Rolling features
df['rolling_7'] = df['y'].rolling(7).mean()
df['rolling_30'] = df['y'].rolling(30).mean()

# One-hot encode categorical features
df = pd.get_dummies(df, columns=['region', 'category'])
df.dropna(inplace=True)  # remove rows with NaN after lag/rolling

