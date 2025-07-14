# project-x-backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tradingview_ta import TA_Handler, Interval
from db import redis

app = FastAPI(title="Project X API", version="0.3")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Health(BaseModel):
    status: str

@app.get("/", response_model=Health)
async def root():
    return {"status": "OK"}

class Stock(BaseModel):
    symbol: str
    price: float

@app.get("/stocks/{symbol}", response_model=Stock)
async def get_stock(symbol: str):
    symbol = symbol.upper()
    cache_key = f"stock:{symbol}"
    # 1) Try cache
    cached = await redis.get(cache_key)
    if cached:
        return Stock(symbol=symbol, price=float(cached))

    # 2) Fetch from TradingView
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="america",       # or "india" for NSE symbols
            exchange="NASDAQ",        # or "NSE" for Indian stocks
            interval=Interval.INTERVAL_1_MINUTE
        )
        quote = handler.get_analysis().indicators["close"]
    except Exception as e:
        raise HTTPException(404, f"Could not fetch {symbol}: {e}")

    # 3) Cache for 60s
    await redis.set(cache_key, str(quote), ex=60)
    return Stock(symbol=symbol, price=quote)

# Watchlist models + endpoints
class WatchItem(BaseModel):
    id: int = None
    symbol: str
    note: str = None

# In-memory store for now (you can swap to Postgres later)
WATCHLIST = []
NEXT_ID = 1

@app.post("/watchlist/", response_model=WatchItem)
async def add_watchlist(item: WatchItem):
    global NEXT_ID
    record = {"id": NEXT_ID, "symbol": item.symbol.upper(), "note": item.note}
    WATCHLIST.append(record)
    NEXT_ID += 1
    return record

@app.get("/watchlist/", response_model=list[WatchItem])
async def list_watchlist():
    return WATCHLIST

@app.delete("/watchlist/{item_id}", status_code=204)
async def delete_watchlist(item_id: int):
    global WATCHLIST
    WATCHLIST = [r for r in WATCHLIST if r["id"] != item_id]
    return
