import os
from databases import Database
from sqlalchemy import (MetaData, Table, Column, Integer, String, 
                        Float, create_engine)
import redis.asyncio as aioredis  # alias to minimize downstream changes

# Load from env
DATABASE_URL = os.getenv("POSTGRES_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Postgres via `databases`
database = Database(DATABASE_URL)
metadata = MetaData()

# Watchlist table
watchlists = Table(
    "watchlists",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(length=10), index=True),
    Column("note", String, nullable=True),
)

# Create the SQLAlchemy engine & tables
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# Redis async client
redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
