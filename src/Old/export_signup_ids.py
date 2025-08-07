import asyncio
import asyncpg
import csv
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def export_signup_ids():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        "SELECT signup_id FROM nbuild_larouchepac.path_journeys WHERE path_id = $1", 1110
    )
    await conn.close()

    with open("data/path_journeys_signup_ids.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["signup_id"])
        for row in rows:
            writer.writerow([row["signup_id"]])

if __name__ == "__main__":
    asyncio.run(export_signup_ids())