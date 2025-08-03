import os
import asyncio
import asyncpg
import csv
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
SCHEMA = "nbuild_larouchepac"
OUTPUT_CSV = "data/glorious_overview.csv"
MAX_ROWS = 5

async def get_table_names(conn):
    query = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{SCHEMA}' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    rows = await conn.fetch(query)
    return [r['table_name'] for r in rows]

async def get_table_sample(conn, table_name):
    query = f'SELECT * FROM {SCHEMA}."{table_name}" LIMIT {MAX_ROWS}'
    try:
        rows = await conn.fetch(query)
    except Exception as e:
        print(f"Error querying {table_name}: {e}")
        return None, None
    if not rows:
        # Get column names even if no data
        col_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{SCHEMA}' AND table_name = '{table_name}' ORDER BY ordinal_position"
        cols = [r['column_name'] for r in await conn.fetch(col_query)]
        return cols, []
    cols = list(rows[0].keys())
    data = [list(row.values()) for row in rows]
    return cols, data

def transpose_table(table_name, cols, data):
    # Build the 2D array: first row table name repeated, second row headers, next rows data
    arr = [ [table_name]*len(cols), list(cols) ]
    arr.extend(data)
    # Transpose
    transposed = list(map(list, zip(*arr)))
    # Each row: table_name, col_name, val1, val2, ...
    for row in transposed:
        # Pad to MAX_ROWS+2 columns
        while len(row) < MAX_ROWS+2:
            row.append("")
    return transposed

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    table_names = await get_table_names(conn)
    all_rows = []
    for table_name in table_names:
        cols, data = await get_table_sample(conn, table_name)
        if cols is None:
            continue
        transposed = transpose_table(table_name, cols, data)
        all_rows.extend(transposed)
    await conn.close()
    # Write to CSV
    with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in all_rows:
            writer.writerow(row)
    print(f"Wrote {len(all_rows)} rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(main())
