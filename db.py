import os

# —— Postgres via databases + SQLAlchemy ——
from databases import Database
from sqlalchemy import MetaData, Table, Column, Integer, String, Boolean, create_engine

# Load the database URL from environment
DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://projectx:projectx@postgres:5432/projectx_db"
)

# Async database client
database = Database(DATABASE_URL)
metadata = MetaData()

# Watchlists table model
watchlists = Table(
    "watchlists",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(10), index=True),
    Column("note", String, nullable=True),
)

# Users table model
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, index=True, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True),
)

# Create tables if they don't exist
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# —— Redis via redis-py asyncio API ——
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
