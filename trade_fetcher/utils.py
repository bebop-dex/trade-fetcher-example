from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import async_geth_poa_middleware, async_simple_cache_middleware
from trade_fetcher.constants import PMM_CONTRACT_ADDRESS, JAM_CONTRACT_ADDRESS


class Swap(BaseModel):
    taker_token: str
    maker_token: str
    taker_amount: int
    maker_amount: int


# Data that maker receives from ws quote-request and fills it with quotes.maker_amount
class MakerQuote(BaseModel):
    is_gasless: bool  # True if msg_topic="quote"; False if msg_topic="taker_quote"
    taker_address: str
    maker_address: str
    receiver_address: str
    quotes: list[Swap]
    taker_tokens: list[str]
    maker_tokens: list[str]
    taker_tokens_indices: list[int]
    maker_tokens_indices: list[int]
    event_id: int
    commands: str  # 0x...
    order_type: str  # 121/12M/M21  (One-to-One, One-to-Many, Many-to-One)
    order_signing_type: str  # SingleOrder or MultiOrder
    is_aggregate_order: bool

    def __post_init__(self):
        commands_num: int = int(len(self.commands[2:]) / 2)
        assert commands_num == len(self.taker_tokens) + len(self.maker_tokens)
        assert len(self.quotes) == len(self.taker_tokens_indices)
        assert len(self.quotes) == len(self.maker_tokens_indices)
        if self.order_type == "121":
            if self.is_aggregate_order:
                assert self.order_signing_type == "MultiOrder"
            else:
                assert self.order_signing_type == "SingleOrder"
        else:
            assert self.order_signing_type == "MultiOrder"
        if self.is_gasless and self.taker_address != JAM_CONTRACT_ADDRESS:
            print(f"Warning: {self.taker_address=} for gasless order usually should be BebopJAM address")

    @property
    def quote_maker_amounts(self) -> list[int]:
        maker_amounts = [0 for _ in self.maker_tokens]
        for i, swap in enumerate(self.quotes):
            maker_amounts[self.maker_tokens_indices[i]] += swap.maker_amount
        return maker_amounts

    @property
    def quote_taker_amounts(self) -> list[int]:
        taker_amounts = [0 for _ in self.taker_tokens]
        for i, swap in enumerate(self.quotes):
            taker_amounts[self.taker_tokens_indices[i]] += swap.taker_amount
        return taker_amounts

    @property
    def ordered_transfers(self) -> list[Transfer]:
        if self.order_signing_type == "SingleOrder":
            return [
                Transfer(from_address=None, to_address=self.maker_address, is_maker_token=False, index_in_tokens=0),
                Transfer(from_address=self.maker_address, to_address=None, is_maker_token=True, index_in_tokens=0),
            ]

        taker_transfers: list[Transfer] = []
        maker_transfers: list[Transfer] = []
        pending_transfers_to_makers: list[Transfer] = []
        maker_commands: list[Command] = [
            Command(self.commands[(i + 1) * 2 : (i + 2) * 2]) for i in range(len(self.maker_tokens))
        ]
        taker_commands: list[Command] = [
            Command(self.commands[(i + 1 + len(self.maker_tokens)) * 2 : (i + 2 + len(self.maker_tokens)) * 2])
            for i in range(len(self.taker_tokens))
        ]
        for i, (maker_command, maker_token) in enumerate(zip(maker_commands, self.maker_tokens, strict=True)):
            if maker_command == Command.SIMPLE_TRANSFER:
                maker_transfers.append(Transfer(self.maker_address, self.receiver_address, True, i))
            elif maker_command in {Command.TRANSFER_TO_CONTRACT, Command.NATIVE_TRANSFER}:
                maker_transfers.append(Transfer(self.maker_address, PMM_CONTRACT_ADDRESS, True, i))
            else:
                raise ValueError(f"Unknown maker command: {maker_command}")

        for i, (taker_command, taker_token) in enumerate(zip(taker_commands, self.taker_tokens, strict=True)):
            if taker_command in {
                Command.SIMPLE_TRANSFER, Command.PERMIT2_TRANSFER,
                Command.CALL_PERMIT_THEN_TRANSFER, Command.CALL_PERMIT2_THEN_TRANSFER
            }:
                taker_transfers.append(Transfer(self.taker_address, self.maker_address, False, i))
            elif taker_command in {Command.TRANSFER_FROM_CONTRACT, Command.NATIVE_TRANSFER}:
                if self.is_aggregate_order:
                    pending_transfers_to_makers.append(Transfer(PMM_CONTRACT_ADDRESS, self.maker_address, False, i))
                else:
                    taker_transfers.append(Transfer(PMM_CONTRACT_ADDRESS, self.maker_address, False, i))
            else:
                raise ValueError(f"Unknown taker command: {taker_command}")

        if self.is_aggregate_order:
            return maker_transfers + taker_transfers + pending_transfers_to_makers
        return taker_transfers + maker_transfers

    def transfers_to_amounts_list(self, transfers: list[Transfer], is_maker: bool) -> list[int]:
        arr_len = len(self.maker_tokens) if is_maker else len(self.taker_tokens)
        amounts = [0 for _ in range(arr_len)]
        for transfer in transfers:
            assert transfer.amount
            if transfer.is_maker_token != is_maker:
                continue
            amounts[transfer.index_in_tokens] += transfer.amount
        return amounts

    def get_filled_swaps(self, taker_amounts: list[int], maker_amounts: list[int]) -> list[Swap]:
        assert len(taker_amounts) == len(self.taker_tokens)
        assert len(maker_amounts) == len(self.maker_tokens)
        filled_quotes: list[Swap] = []
        for i, swap in enumerate(self.quotes):
            quoted_token_taker_amount, quoted_token_maker_amount = 0, 0
            taker_index, maker_index = self.taker_tokens_indices[i], self.maker_tokens_indices[i]
            for j, ind in enumerate(self.taker_tokens_indices):
                if ind == taker_index:
                    quoted_token_taker_amount += self.quotes[j].taker_amount
            filled_taker_amount: int
            if swap.taker_amount == quoted_token_taker_amount:
                filled_taker_amount = taker_amounts[taker_index]
            else:
                filled_taker_amount = int(
                    taker_amounts[taker_index] * swap.taker_amount / quoted_token_taker_amount
                )

            for j, ind in enumerate(self.maker_tokens_indices):
                if ind == maker_index:
                    quoted_token_maker_amount += self.quotes[j].maker_amount
            filled_maker_amount: int
            if swap.maker_amount == quoted_token_maker_amount:
                filled_maker_amount = maker_amounts[maker_index]
            else:
                filled_maker_amount = int(
                    maker_amounts[maker_index] * swap.maker_amount / quoted_token_maker_amount
                )
            filled_quotes.append(
                Swap(
                    taker_token=self.taker_tokens[taker_index],
                    maker_token=self.maker_tokens[maker_index],
                    taker_amount=filled_taker_amount,
                    maker_amount=filled_maker_amount,
                )
            )
        return filled_quotes

    def get_filled_quotes(self, all_transfers: list[Transfer]) -> FilledQuote:
        taker_amounts = self.transfers_to_amounts_list(all_transfers, is_maker=False)
        maker_amounts = self.transfers_to_amounts_list(all_transfers, is_maker=True)
        filled_swaps = self.get_filled_swaps(taker_amounts, maker_amounts)
        surplus: dict[str, int] | None = None
        if self.is_gasless:
            for i, (amount, quoted_amount) in enumerate(zip(maker_amounts, self.quote_maker_amounts, strict=True)):
                if amount > quoted_amount:
                    raise ValueError("Unexpected: Maker amount is greater than quoted amount")
                elif amount < quoted_amount:
                    if surplus is None:
                        surplus = {}
                    token = self.maker_tokens[i]
                    surplus[token] = quoted_amount - amount
        return FilledQuote(filled_swaps=filled_swaps, event_id=self.event_id, surplus=surplus)


# MakerQuote with onchain filled amounts
class FilledQuote(BaseModel):
    filled_swaps: list[Swap]
    event_id: int
    surplus: dict[str, int] | None = None  # token->amount in case of gasless order with surplus


@dataclass
class Transfer:
    from_address: str | None
    to_address: str | None
    is_maker_token: bool
    index_in_tokens: int
    amount: int | None = None


class Command(Enum):
    SIMPLE_TRANSFER = "00"
    PERMIT2_TRANSFER = "01"
    CALL_PERMIT_THEN_TRANSFER = "02"
    CALL_PERMIT2_THEN_TRANSFER = "03"
    NATIVE_TRANSFER = "04"
    TRANSFER_TO_CONTRACT = "07"
    TRANSFER_FROM_CONTRACT = "08"


def make_web3(http_url: str) -> AsyncWeb3:
    http_provider = AsyncHTTPProvider(http_url, request_kwargs={"timeout": 6})
    web3 = AsyncWeb3(http_provider)
    web3.middleware_onion.inject(async_geth_poa_middleware, "poa", layer=0)
    web3.middleware_onion.inject(async_simple_cache_middleware, layer=0)
    return web3
