# project-x-backend/db.py

import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Async Redis client
redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
