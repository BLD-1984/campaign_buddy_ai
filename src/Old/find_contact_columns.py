import os
import asyncio
import asyncpg
import csv
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
OUTPUT_CSV = "data/columns_with_name_or_email.csv"

QUERY = """
SELECT table_schema, table_name, column_name
FROM information_schema.columns
WHERE column_name LIKE '%email%' OR column_name LIKE '%name%'
ORDER BY table_schema, table_name, column_name;
"""

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(QUERY)
    await conn.close()
    # Print results to console
    for r in rows:
        print(f"Schema: {r['table_schema']}, Table: {r['table_name']}, Column: {r['column_name']}")
    # Save results to CSV
    with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["schema", "table", "column"])
        for r in rows:
            writer.writerow([r['table_schema'], r['table_name'], r['column_name']])
    print(f"Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(main())
