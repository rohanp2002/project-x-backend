from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from tradingview_ta import TA_Handler, Interval
from db import database, watchlists, redis, users

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

app = FastAPI(title="Project X API", version="0.4")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Auth configuration ----------
SECRET_KEY = "CHANGE_THIS_TO_A_SECURE_RANDOM_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_user(email: str):
    query = users.select().where(users.c.email == email)
    return await database.fetch_one(query)

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/signup/", status_code=201)
async def signup(form: OAuth2PasswordRequestForm = Depends()):
    existing = await get_user(form.username)
    if existing:
        raise HTTPException(400, "Email already registered")
    hashed_pw = get_password_hash(form.password)
    stmt = users.insert().values(email=form.username, hashed_password=hashed_pw)
    user_id = await database.execute(stmt)
    return {"id": user_id, "email": form.username}

@app.post("/token")
async def login_for_access_token(form: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    access_token = create_access_token(
        {"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ---------- Startup / Shutdown ----------
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# ---------- Health check ----------
class Health(BaseModel):
    status: str

@app.get("/", response_model=Health)
async def root():
    return {"status": "OK"}

# ---------- Stock endpoint ----------
class Stock(BaseModel):
    symbol: str
    price: float

@app.get("/stocks/{symbol}", response_model=Stock)
async def get_stock(symbol: str):
    symbol = symbol.upper()
    cache_key = f"stock:{symbol}"
    cached = await redis.get(cache_key)
    if cached:
        return Stock(symbol=symbol, price=float(cached))
    handler = TA_Handler(
        symbol=symbol,
        screener="america",
        exchange="NASDAQ",
        interval=Interval.INTERVAL_1_MINUTE
    )
    quote = handler.get_analysis().indicators["close"]
    await redis.set(cache_key, str(quote), ex=60)
    return Stock(symbol=symbol, price=quote)

# ---------- Watchlist endpoints ----------
class WatchItem(BaseModel):
    id: int | None = None
    symbol: str
    note: str | None = None

@app.post("/watchlist/", response_model=WatchItem)
async def add_watch(item: WatchItem):
    stmt = watchlists.insert().values(symbol=item.symbol.upper(), note=item.note)
    new_id = await database.execute(stmt)
    return {**item.dict(), "id": new_id}

@app.get("/watchlist/", response_model=List[WatchItem])
async def list_watch():
    rows = await database.fetch_all(watchlists.select())
    return [WatchItem(**r) for r in rows]

@app.delete("/watchlist/{item_id}", status_code=204)
async def delete_watch(item_id: int):
    await database.execute(watchlists.delete().where(watchlists.c.id == item_id))
    return
