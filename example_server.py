import os

from fastapi import FastAPI, HTTPException
from trade_fetcher.trade_fetcher import TradeFetcher
from trade_fetcher.utils import MakerQuote, FilledQuote

app = FastAPI()
rpc = os.getenv("RPC")
assert rpc, "RPC environment variable is not set"
trade_fetcher = TradeFetcher(http_rpc=rpc)


@app.post("/add_quote")
def add_quote(quote: MakerQuote):
    trade_fetcher.add_quote(quote)


@app.get("/extract_quotes/{tx_hash}", response_model=list[FilledQuote])
async def extract_quotes(tx_hash: str):
    try:
        quotes = await trade_fetcher.extract_quotes(tx_hash)
        if not quotes:
            raise HTTPException(status_code=404, detail="No quotes found")
        return quotes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
