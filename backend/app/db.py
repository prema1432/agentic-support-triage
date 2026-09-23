"""Async MongoDB connection layer (motor)."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.settings import settings


class Mongo:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongo = Mongo()


async def connect_mongo() -> None:
    mongo.client = AsyncIOMotorClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
    mongo.db = mongo.client[settings.mongo_db]
    await mongo.client.admin.command("ping")


async def close_mongo() -> None:
    if mongo.client is not None:
        mongo.client.close()
        mongo.client = None
        mongo.db = None


def get_db() -> AsyncIOMotorDatabase:
    if mongo.db is None:
        raise RuntimeError("MongoDB not connected")
    return mongo.db
