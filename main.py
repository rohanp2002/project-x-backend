from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Project X API", version="0.1")

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
    # TODO: wire up real data
    return {"symbol": symbol.upper(), "price": 123.45}
