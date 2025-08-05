import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER", "dev_user"),
        password=os.getenv("POSTGRES_PASSWORD", "dev_password"),
        database=os.getenv("POSTGRES_DB", "campaign_buddy_ai"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    rows = await conn.fetch("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'mailing_events_sent'
          AND schemaname = 'nbuild_larouchepac';
    """)
    if not rows:
        print("No indexes found for mailing_events_sent in nbuild_larouchepac.")
    else:
        for row in rows:
            print(row['indexname'], row['indexdef'])
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
