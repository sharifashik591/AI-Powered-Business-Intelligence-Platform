import duckdb
from pathlib import Path
import plotly.express as px

# Resolve DB path relative to this script's location (works from any CWD)
DB_PATH = str(Path(__file__).parent / "business_bi.duckdb")


def database_audit(db_path):
    con = duckdb.connect(db_path)
    tables = con.execute("SHOW TABLES").fetchall()
    
    print(f"{'Table Name':<20} | {'Rows':<10} | {'Cols':<5}")
    print("-" * 40)
    
    for (table_name,) in tables:
        count = con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        cols = con.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name = '{table_name}'").fetchone()[0]
        print(f"{table_name:<20} | {count:<10,} | {cols:<5}")
    
    con.close()

database_audit(DB_PATH)


# ---------- Summary Query ----------

con = duckdb.connect(DB_PATH)

# Get column counts per table
col_counts = con.execute("""
    SELECT table_name, count(column_name) AS total_columns
    FROM information_schema.columns
    WHERE table_schema = 'main'
    GROUP BY table_name
    ORDER BY table_name
""").df()

# Get row counts per table
tables = con.execute("SHOW TABLES").fetchall()
row_counts = []
for (tbl,) in tables:
    n = con.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
    row_counts.append({"table_name": tbl, "row_count": n})

import pandas as pd
df_rows = pd.DataFrame(row_counts)
df_summary = col_counts.merge(df_rows, on="table_name").sort_values("row_count", ascending=False)
print(df_summary.to_string(index=False))

con.close()

# ---------- Plotly Visualization ----------

# Chart 1: Row count per table
fig1 = px.bar(
    df_summary,
    x="table_name",
    y="row_count",
    title="Row Count per Table",
    labels={"table_name": "Table", "row_count": "Rows"},
    color="row_count",
    color_continuous_scale="Blues",
    text_auto=True,
)
fig1.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
fig1.show()

# Chart 2: Column count per table
fig2 = px.bar(
    df_summary,
    x="table_name",
    y="total_columns",
    title="Column Count per Table",
    labels={"table_name": "Table", "total_columns": "Columns"},
    color="total_columns",
    color_continuous_scale="Purples",
    text_auto=True,
)
fig2.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
fig2.show()