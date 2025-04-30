import asyncio

from trade_fetcher.trade_fetcher import TradeFetcher
from trade_fetcher.utils import MakerQuote, Swap


async def run(rpc: str, tx_hash: str, quote: MakerQuote) -> None:
    tf = TradeFetcher(http_rpc=rpc)
    tf.add_quote(quote)
    quotes = await tf.extract_quotes(tx_hash)
    print(f"Found {len(quotes)} quote in {tx_hash=}")
    for quote in quotes:
        print(quote)


if __name__ == "__main__":
    RPC = "https://ethereum-rpc.publicnode.com"

    TX_HASH = "0x7c79e153370525889d3ec48a3325294c6047de435ccea4bb139215697be750f4"
    QUOTE = MakerQuote(
        is_gasless=False,
        taker_address="0xF00000003D31D4ab730A8e269Ae547F8F76996bA",
        maker_address="0x51C72848c68a965f66FA7a88855F9f7784502a7F",
        receiver_address="0xF00000003D31D4ab730A8e269Ae547F8F76996bA",
        quotes=[
            Swap(
                maker_token="0x57e114B691Db790C35207b2e685D4A43181e6061",
                taker_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                maker_amount=10078525028900661709485,
                taker_amount=1930000000000000000,
            )
        ],
        taker_tokens=["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
        maker_tokens=["0x57e114B691Db790C35207b2e685D4A43181e6061"],
        taker_tokens_indices=[0],
        maker_tokens_indices=[0],
        event_id=170295854396643636174023642980340964700,
        commands="0x0000",
        order_type="121",
        order_signing_type="SingleOrder",
        is_aggregate_order=False,
    )

    asyncio.run(run(RPC, TX_HASH, QUOTE))
