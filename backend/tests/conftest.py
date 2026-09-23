"""Shared pytest fixtures — in-memory MongoDB via mongomock-motor."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app import db as db_module
from app.main import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()
    fake = AsyncMongoMockClient()
    db_module.mongo.db = fake["support_triage_test"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
