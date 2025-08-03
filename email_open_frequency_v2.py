import asyncpg
import asyncio
import os
import csv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "dev_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "dev_password"),
    "database": os.getenv("POSTGRES_DB", "campaign_buddy_ai"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

SCHEMA = "nbuild_larouchepac"
DATE_CUTOFF = datetime(2025, 1, 1)

async def main():
    conn = await asyncpg.connect(**DB_CONFIG)

    # 1. Filter mailing_events_sent by created_at >= 2025-01-01
    sent_rows = await conn.fetch(f"""
        SELECT mailing_id, signup_id, created_at, broadcaster_id
        FROM {SCHEMA}.mailing_events_sent
        WHERE created_at >= $1 AND broadcaster_id <> 1062
    """, DATE_CUTOFF)

    # Export filtered mailing_events_sent
    with open("mailing_events_sent_filtered.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["mailing_id", "signup_id", "created_at", "broadcaster_id"])
        for row in sent_rows:
            writer.writerow([row["mailing_id"], row["signup_id"], row["created_at"], row["broadcaster_id"]])

    # 2. For each unique signup_id, count unique mailing_id in sent
    sent_counts = {}
    sent_mailing_ids = set()
    for row in sent_rows:
        signup_id = row["signup_id"]
        mailing_id = row["mailing_id"]
        sent_mailing_ids.add(mailing_id)
        sent_counts.setdefault(signup_id, set()).add(mailing_id)
    sent_counts = {k: len(v) for k, v in sent_counts.items()}

    # 3. Filter mailing_events_opened by mailing_id in sent_mailing_ids
    opened_rows = await conn.fetch(f"""
        SELECT mailing_id, signup_id, created_at, broadcaster_id
        FROM {SCHEMA}.mailing_events_opened
        WHERE mailing_id = ANY($1::bigint[]) AND broadcaster_id <> 1062
    """, list(sent_mailing_ids))

    # Export filtered mailing_events_opened
    with open("mailing_events_opened_filtered.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["mailing_id", "signup_id", "created_at", "broadcaster_id"])
        for row in opened_rows:
            writer.writerow([row["mailing_id"], row["signup_id"], row["created_at"], row["broadcaster_id"]])

    # 4. For each unique signup_id, count unique mailing_id in opened
    opened_counts = {}
    for row in opened_rows:
        signup_id = row["signup_id"]
        mailing_id = row["mailing_id"]
        opened_counts.setdefault(signup_id, set()).add(mailing_id)
    opened_counts = {k: len(v) for k, v in opened_counts.items()}

    # 5. Calculate open frequency for each signup_id
    results = []
    for signup_id in sent_counts:
        sent_count = sent_counts.get(signup_id, 0)
        opened_count = opened_counts.get(signup_id, 0)
        frequency = opened_count / sent_count if sent_count else 0
        results.append([signup_id, sent_count, opened_count, frequency])

    # Sort results by frequency descending
    results.sort(key=lambda x: x[3], reverse=True)

    # Export frequencies
    with open("email_open_frequency.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["signup_id", "sent_count", "opened_count", "open_frequency"])
        for row in results:
            writer.writerow(row)

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
