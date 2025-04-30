from cachetools import TTLCache
from eth_typing import HexStr
from web3 import AsyncWeb3
from web3.types import TxReceipt

from trade_fetcher.constants import PMM_CONTRACT_ADDRESS, BEBOP_TOPIC, TRANSFER_TOPIC
from trade_fetcher.utils import make_web3, MakerQuote, Transfer, FilledQuote


class TradeFetcher:

    def __init__(self, http_rpc: str) -> None:
        self.web3: AsyncWeb3 = make_web3(http_rpc)
        self.event_id_to_quote: TTLCache[int, MakerQuote] = TTLCache(maxsize=1000000, ttl=6 * 60 * 60)

    def add_quote(self, quote: MakerQuote) -> None:
        # adding to cache on ws-quote-request
        self.event_id_to_quote[quote.event_id] = quote

    async def extract_quotes(self, tx_hash: str) -> list[FilledQuote]:
        tx_receipt: TxReceipt = await self.web3.eth.get_transaction_receipt(HexStr(tx_hash))
        filled_maker_quotes: list[FilledQuote] = []
        cur_event_id: int = 0
        cur_transfers: list[Transfer] = []
        cur_transfer_index: int = 0
        for log in reversed(tx_receipt["logs"]):
            if log["address"].lower() == PMM_CONTRACT_ADDRESS.lower() and log["topics"][0].hex() == BEBOP_TOPIC:
                log_event_id: int = int(log["topics"][1].hex(), 16)
                if log_event_id not in self.event_id_to_quote:
                    # maker didn't participate in this tx
                    continue
                if len(cur_transfers) > 0:
                    if len(cur_transfers) != cur_transfer_index:
                        raise ValueError(f"Something went wrong for {cur_event_id}")
                    filled_maker_quotes.append(self.event_id_to_quote[cur_event_id].get_filled_quotes(cur_transfers))
                cur_event_id = log_event_id
                cur_transfers = self.event_id_to_quote[cur_event_id].ordered_transfers
                cur_transfers.reverse()
                cur_transfer_index = 0
            elif log["topics"][0].hex() == TRANSFER_TOPIC and len(cur_transfers) > 0 and \
                    cur_transfer_index < len(cur_transfers):
                from_address = AsyncWeb3.to_checksum_address(f"0x{log['topics'][1].hex()[26:]}")
                to_address = AsyncWeb3.to_checksum_address(f"0x{log['topics'][2].hex()[26:]}")
                amount: int = int(log["data"].hex(), 16)
                if (expected_from_address := cur_transfers[cur_transfer_index].from_address) and \
                        expected_from_address != from_address:
                    continue
                if (expected_to_address := cur_transfers[cur_transfer_index].to_address) and \
                        expected_to_address != to_address:
                    continue
                cur_transfers[cur_transfer_index].amount = amount
                cur_transfer_index += 1

        if len(cur_transfers) == 0:
            return []

        # fill the last one
        if len(cur_transfers) != cur_transfer_index:
            raise ValueError(f"Something went wrong for {cur_event_id}")
        filled_maker_quotes.append(self.event_id_to_quote[cur_event_id].get_filled_quotes(cur_transfers))
        filled_maker_quotes.reverse()

        return filled_maker_quotes



