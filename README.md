
## Trade-fetcher example for Bebop

Trade-fetcher that constructs filled trades by analyzing events from `eth_getTransactionReceipt` responses.

It can be useful for chains like HyperEVM that don't have `debug_traceTransaction` or `debug_traceCall` RPC methods.


### Usage

#### Example

```commandline
poetry install
poetry run python example.py
```

#### Server example
Run as a server in docker container:

```commandline
docker build -t trade-fetcher .
docker run -e RPC="https://ethereum-rpc.publicnode.com" -p 8000:8000 trade-fetcher
```

For adding quotes to memory use the following endpoint:

`/POST add_quote(quote: MakerQuote)`

When you detect bebop event using eth_subscribe or eth_getLogs, you can call following endpoint to extract filled quotes:

`/GET localhost:8000/extract_quotes/{tx_hash}`

Flow:
1) receive ws-quote-request from bebop server
2) respond to it and also call `/POST add_quote` to add this quote to trade-fetcher's memory
3) detect tx_hash with bebop event in it using eth_subscribe or eth_getLogs
4) call `/GET extract_quotes/{tx_hash}` to get information about filled amounts onchain
