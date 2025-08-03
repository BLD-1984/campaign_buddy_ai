import asyncio
import asyncpg
import os
import csv
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")

async def get_counts(conn, table, date):
    query = f"""
        SELECT signup_id, COUNT(DISTINCT mailing_id) AS mailing_count
        FROM nbuild_larouchepac.{table}
        WHERE created_at >= $1
        GROUP BY signup_id
    """
    rows = await conn.fetch(query, date)
    return {row['signup_id']: row['mailing_count'] for row in rows}

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        date_filter = datetime.strptime('2025-01-01', '%Y-%m-%d')

        # Export filtered mailing_events_sent
        sent_rows = await conn.fetch(
            """
            SELECT * FROM nbuild_larouchepac.mailing_events_sent WHERE created_at >= $1
            """, date_filter
        )
        with open('mailing_events_sent_filtered.csv', 'w', newline='') as csvfile:
            if sent_rows:
                fieldnames = list(sent_rows[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in sent_rows:
                    writer.writerow(dict(row))
            else:
                csvfile.write('')

        # Export filtered mailing_events_opened by sent date
        opened_rows = await conn.fetch(
            """
            SELECT o.*, s.created_at AS created_at_sent
            FROM nbuild_larouchepac.mailing_events_opened o
            JOIN nbuild_larouchepac.mailing_events_sent s ON o.mailing_id = s.mailing_id
            WHERE s.created_at >= $1
            """, date_filter
        )
        with open('mailing_events_opened_filtered.csv', 'w', newline='') as csvfile:
            if opened_rows:
                fieldnames = list(opened_rows[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in opened_rows:
                    writer.writerow(dict(row))
            else:
                csvfile.write('')

        # Existing open frequency logic
        sent_counts = await get_counts(conn, 'mailing_events_sent', date_filter)
        opened_counts = await get_counts(conn, 'mailing_events_opened', date_filter)

        results = []
        for signup_id, sent in sent_counts.items():
            opened = opened_counts.get(signup_id, 0)
            freq = opened / sent if sent > 0 else 0
            results.append({'signup_id': signup_id, 'sent': sent, 'opened': opened, 'open_frequency': freq})

        # Sort by open_frequency descending
        results.sort(key=lambda x: x['open_frequency'], reverse=True)

        # Export to CSV
        with open('email_open_frequency.csv', 'w', newline='') as csvfile:
            fieldnames = ['signup_id', 'sent', 'opened', 'open_frequency']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print("Exported to email_open_frequency.csv")
        print("Exported mailing_events_sent_filtered.csv and mailing_events_opened_filtered.csv")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
