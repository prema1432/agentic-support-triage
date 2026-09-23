"""Seed MongoDB with sample tickets: python3 -m scripts.seed"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.settings import settings

SAMPLES = [
    {
        "subject": "Complete outage in EU region",
        "body": "We are seeing a full outage, the service is down for all our customers since 9am.",
        "customer_tier": "enterprise",
    },
    {
        "subject": "Webhook integration broken",
        "body": "Our webhook integration keeps failing with timeout errors after the latest deploy.",
        "customer_tier": "pro",
    },
    {
        "subject": "Refund for duplicate charge",
        "body": "We were billed twice on the last invoice, please refund the duplicate payment.",
        "customer_tier": "pro",
    },
    {
        "subject": "Dark mode request",
        "body": "It would be great to have a dark theme in the dashboard for night shifts.",
        "customer_tier": "free",
    },
]


async def seed() -> None:
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.mongo_db]
    await db.tickets.delete_many({})
    await db.tickets.insert_many(SAMPLES)
    print(f"Seeded {len(SAMPLES)} tickets into {settings.mongo_db}.tickets")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
