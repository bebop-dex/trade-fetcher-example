import pytest

from trade_fetcher.trade_fetcher import TradeFetcher
from trade_fetcher.utils import MakerQuote, Swap


TEST_RPC = "https://ethereum-rpc.publicnode.com"


class TestTradeFetcher:

    @pytest.mark.asyncio
    async def test_single_order(self) -> None:
        # USDT <-> USDC
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x96420656aff10599cbd33f5495b364b7457d4f5d87369fcd91930f2d3844d530"
        quote = MakerQuote(
            is_gasless=False,
            taker_address="0x2d5805A423D6CE771f06972Ad4499f120902631a",
            maker_address="0xBEE3211ab312a8D065c4FeF0247448e17A8da000",
            receiver_address="0x2d5805A423D6CE771f06972Ad4499f120902631a",
            quotes=[
                Swap(
                    maker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    taker_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    maker_amount=411472629808,
                    taker_amount=411213463720,
                )
            ],
            taker_tokens=["0xdAC17F958D2ee523a2206206994597C13D831ec7"],
            maker_tokens=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
            taker_tokens_indices=[0],
            maker_tokens_indices=[0],
            event_id=158239944205041495033519717512851988700,
            commands="0x0000",
            order_type="121",
            order_signing_type="SingleOrder",
            is_aggregate_order=False,
        )
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].maker_amount == 411472629808
        assert quotes[0].filled_swaps[0].taker_amount == 411213463720

    @pytest.mark.asyncio
    async def test_single_order_with_partial_fill(self) -> None:
        # WETH <-> ENA
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x7c79e153370525889d3ec48a3325294c6047de435ccea4bb139215697be750f4"
        quote = MakerQuote(
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
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].maker_amount == 10077175086103207271797
        assert quotes[0].filled_swaps[0].taker_amount == 1929741490982895217

    @pytest.mark.asyncio
    async def test_gasless_single_order_with_surplus(self) -> None:
        # USDT <-> WETH
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x5a110a1760b9b4cebbff03a32ddc80db38c915cd0f6c081f45b62d24ac54740b"
        quote = MakerQuote(
            is_gasless=True,
            taker_address="0xbeb0b0623f66bE8cE162EbDfA2ec543A522F4ea6",
            maker_address="0x67336Cec42645F55059EfF241Cb02eA5cC52fF86",
            receiver_address="0x0DfB90A3ccfeE7b69277E7DF6CA4fA8FC68bAF1f",
            quotes=[
                Swap(
                    taker_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    maker_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    taker_amount=154445647,
                    maker_amount=97744683095197300,
                )
            ],
            taker_tokens=["0xdAC17F958D2ee523a2206206994597C13D831ec7"],
            maker_tokens=["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
            taker_tokens_indices=[0],
            maker_tokens_indices=[0],
            event_id=333977581496863956339675102836762284401,
            commands="0x0000",
            order_type="121",
            order_signing_type="SingleOrder",
            is_aggregate_order=False,
        )
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].maker_amount == 97718774975538100
        assert quotes[0].filled_swaps[0].taker_amount == 154445647
        assert len(quotes[0].surplus) == 1
        assert (
            quote.quotes[0].maker_amount - quotes[0].surplus["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]
        ) == 97718774975538100

    @pytest.mark.asyncio
    async def test_gasless_multi_order_m21(self) -> None:
        # AAVE+UNI <-> USDC
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x7fd2ac4849f4fa0fd0b571bb8ad3c6c10a1cdb69720d9b5df1c8e6efb55091c3"
        quote = MakerQuote(
            is_gasless=True,
            taker_address="0xbeb0b0623f66bE8cE162EbDfA2ec543A522F4ea6",
            maker_address="0x51C72848c68a965f66FA7a88855F9f7784502a7F",
            receiver_address="0x60770C6155f2974F41b802D983669f57b75d95B3",
            quotes=[
                Swap(
                    taker_token="0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                    maker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    taker_amount=85420000000000000,
                    maker_amount=13987595,
                ),
                Swap(
                    taker_token="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
                    maker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    taker_amount=1319300000000000000,
                    maker_amount=7568966,
                )
            ],
            taker_tokens=["0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"],
            maker_tokens=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
            taker_tokens_indices=[0, 1],
            maker_tokens_indices=[0, 0],
            event_id=52091406175822051395750048067182333401,
            commands="0x000000",
            order_type="M21",
            order_signing_type="MultiOrder",
            is_aggregate_order=False,
        )
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].taker_amount == 85420000000000000
        assert quotes[0].filled_swaps[0].maker_amount == 13987595
        assert quotes[0].filled_swaps[1].taker_amount == 1319300000000000000
        assert quotes[0].filled_swaps[1].maker_amount == 7568966
        assert quotes[0].surplus is None

    @pytest.mark.asyncio
    async def test_gasless_multi_order_12m_with_surplus(self) -> None:
        # USDC <-> USDT, WETH
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x278f463d4687bea7e2c0dbe27eeca4a4ea324b9c6b76da9689f0dde6dc77d868"
        quote = MakerQuote(
            is_gasless=True,
            taker_address="0xbeb0b0623f66bE8cE162EbDfA2ec543A522F4ea6",
            maker_address="0x51C72848c68a965f66FA7a88855F9f7784502a7F",
            receiver_address="0xDF3f49687aECE6D41763bc4B7bF333D6Ae10CEEd",
            quotes=[
                Swap(
                    taker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    maker_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    taker_amount=439718182,
                    maker_amount=439346287,
                ),
                Swap(
                    taker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    maker_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    taker_amount=439718182,
                    maker_amount=243539249711557465,
                )
            ],
            taker_tokens=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
            maker_tokens=["0xdAC17F958D2ee523a2206206994597C13D831ec7", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
            taker_tokens_indices=[0, 0],
            maker_tokens_indices=[0, 1],
            event_id=162373316173075221736893596071568675001,
            commands="0x000000",
            order_type="12M",
            order_signing_type="MultiOrder",
            is_aggregate_order=False,
        )
        self.tf.add_quote(quote)
        onchain_quotes = await self.tf.extract_quotes(tx_hash)
        assert onchain_quotes[0].filled_swaps[0].taker_amount == 439718182
        assert onchain_quotes[0].filled_swaps[0].maker_amount == 439346235
        assert onchain_quotes[0].filled_swaps[1].taker_amount == 439718182
        assert onchain_quotes[0].filled_swaps[1].maker_amount == 243528046705044298

        assert len(onchain_quotes[0].surplus) == 2
        assert (
            quote.quotes[0].maker_amount - onchain_quotes[0].surplus["0xdAC17F958D2ee523a2206206994597C13D831ec7"]
        ) == 439346235
        assert (
            quote.quotes[1].maker_amount - onchain_quotes[0].surplus["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]
        ) == 243528046705044298

    @pytest.mark.asyncio
    async def test_aggregate_order_with_simple_split_and_partial_fill(self) -> None:
        # LINK <--(2 makers)--> WETH
        # checking quote for maker=0x67336Cec42645F55059EfF241Cb02eA5cC52fF86
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x9a2e16c5faf43ed8036f1775506df2c5503cba474f9d6a8d9e767c0be9db54e9"
        quote = MakerQuote(
            is_gasless=False,
            taker_address="0xF00000003D31D4ab730A8e269Ae547F8F76996bA",
            maker_address="0x67336Cec42645F55059EfF241Cb02eA5cC52fF86",
            receiver_address="0xF00000003D31D4ab730A8e269Ae547F8F76996bA",
            quotes=[
                Swap(
                    taker_token="0x514910771AF9Ca656af840dff83E8264EcF986CA",
                    maker_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    taker_amount=563526810778959232242,
                    maker_amount=4674826269707890000,
                )
            ],
            taker_tokens=["0x514910771AF9Ca656af840dff83E8264EcF986CA"],
            maker_tokens=["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
            taker_tokens_indices=[0],
            maker_tokens_indices=[0],
            event_id=44221220727177499450494038114769059100,
            commands="0x0000",
            order_type="121",
            order_signing_type="MultiOrder",
            is_aggregate_order=True,
        )
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].taker_amount == 552256274563380047597
        assert quotes[0].filled_swaps[0].maker_amount == 4581329744313732200

    @pytest.mark.asyncio
    async def test_aggregate_order_with_2_hops(self) -> None:
        # 1INCH <-> USDC
        # 1INCH <--(maker1)--> USDT <--(maker2)--> USDC
        # checking quote for maker2=0xBEE3211ab312a8D065c4FeF0247448e17A8da000
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x93a1cf230441ddaf8729cd12e687caaf3b91ca280f8409f66687c4f4d1bb9ece"
        quote = MakerQuote(
            is_gasless=False,
            taker_address="0x2d5805A423D6CE771f06972Ad4499f120902631a",
            maker_address="0xBEE3211ab312a8D065c4FeF0247448e17A8da000",
            receiver_address="0x2d5805A423D6CE771f06972Ad4499f120902631a",
            quotes=[
                Swap(
                    taker_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    maker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    taker_amount=572491707199,
                    maker_amount=572138287259,
                )
            ],
            taker_tokens=["0xdAC17F958D2ee523a2206206994597C13D831ec7"],
            maker_tokens=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
            taker_tokens_indices=[0],
            maker_tokens_indices=[0],
            event_id=213981193413093061175115339315315863300,
            commands="0x0008",
            order_type="121",
            order_signing_type="MultiOrder",
            is_aggregate_order=True,
        )
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].taker_amount == 572491707199
        assert quotes[0].filled_swaps[0].maker_amount == 572138287259

    @pytest.mark.asyncio
    async def test_aggregate_order_with_2_hops_and_maker_in_both_hops(self) -> None:
        # COW <-> USDC  partial_fill 44.28%
        # COW <--(maker1+maker2)--> WETH <--(maker1)--> USDC
        # checking quote for maker1=0x51C72848c68a965f66FA7a88855F9f7784502a7F
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0xba46ec14e527542daa84cec26640f7f426fc3b61a8493651d6c5517e470e1f05"
        quote = MakerQuote(
            is_gasless=False,
            taker_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
            maker_address="0x51C72848c68a965f66FA7a88855F9f7784502a7F",
            receiver_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
            quotes=[
                Swap(
                    taker_token="0xDEf1CA1fb7FBcDC777520aa7f396b4E015F497aB",
                    maker_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    taker_amount=1869834787924423869977,
                    maker_amount=314317441219273741,
                ),
                Swap(
                    taker_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    maker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    taker_amount=4669915934252654492,
                    maker_amount=8443335757,
                )
            ],
            taker_tokens=["0xDEf1CA1fb7FBcDC777520aa7f396b4E015F497aB", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
            maker_tokens=["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
            taker_tokens_indices=[0, 1],
            maker_tokens_indices=[0, 1],
            event_id=129514213521666020668410670337799677700,
            commands="0x07000008",
            order_type="121",
            order_signing_type="MultiOrder",
            is_aggregate_order=True,
        )
        self.tf.add_quote(quote)
        quotes = await self.tf.extract_quotes(tx_hash)
        assert quotes[0].filled_swaps[0].taker_amount == 827869525214020692055
        assert quotes[0].filled_swaps[0].maker_amount == 139164076157515308
        assert quotes[0].filled_swaps[1].taker_amount == 2067605711609744947
        assert quotes[0].filled_swaps[1].maker_amount == 3738287686

    @pytest.mark.asyncio
    async def test_3_orders_in_one_tx(self) -> None:
        # 3 SingleOrders in one tx, all orders are partially filled
        # USDT <--(maker1)--> MKR
        # USDT <--(maker1)--> LINK
        # USDC <--(maker2)--> LINK
        self.tf = TradeFetcher(TEST_RPC)
        tx_hash = "0x658cfcdf391f10f2de96ac270430f514af619ef62e400ca47bdf3e376027ff9d"
        maker_quotes: list[MakerQuote] = [
            MakerQuote(
                is_gasless=False,
                taker_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                maker_address="0x67336Cec42645F55059EfF241Cb02eA5cC52fF86",
                receiver_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                quotes=[
                    Swap(
                        taker_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                        maker_token="0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
                        taker_amount=5440242089,
                        maker_amount=3507771250882405000,
                    ),
                ],
                taker_tokens=["0xdAC17F958D2ee523a2206206994597C13D831ec7"],
                maker_tokens=["0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2"],
                taker_tokens_indices=[0],
                maker_tokens_indices=[0],
                event_id=267331113452686270899678349403014777300,
                commands="0x0000",
                order_type="121",
                order_signing_type="SingleOrder",
                is_aggregate_order=False,
            ),
            MakerQuote(
                is_gasless=False,
                taker_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                maker_address="0x67336Cec42645F55059EfF241Cb02eA5cC52fF86",
                receiver_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                quotes=[
                    Swap(
                        taker_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                        maker_token="0x514910771AF9Ca656af840dff83E8264EcF986CA",
                        taker_amount=1908242826,
                        maker_amount=127385333119638100000,
                    ),
                ],
                taker_tokens=["0xdAC17F958D2ee523a2206206994597C13D831ec7"],
                maker_tokens=["0x514910771AF9Ca656af840dff83E8264EcF986CA"],
                taker_tokens_indices=[0],
                maker_tokens_indices=[0],
                event_id=103990371526789528608848788818467029200,
                commands="0x0000",
                order_type="121",
                order_signing_type="SingleOrder",
                is_aggregate_order=False,
            ),
            MakerQuote(
                is_gasless=False,
                taker_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                maker_address="0x51C72848c68a965f66FA7a88855F9f7784502a7F",
                receiver_address="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                quotes=[
                    Swap(
                        taker_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                        maker_token="0x514910771AF9Ca656af840dff83E8264EcF986CA",
                        taker_amount=246543634,
                        maker_amount=16444141360485168945,
                    ),
                ],
                taker_tokens=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
                maker_tokens=["0x514910771AF9Ca656af840dff83E8264EcF986CA"],
                taker_tokens_indices=[0],
                maker_tokens_indices=[0],
                event_id=199995637987204261153433910252447462900,
                commands="0x0000",
                order_type="121",
                order_signing_type="SingleOrder",
                is_aggregate_order=False,
            )
        ]
        for quote in maker_quotes:
            self.tf.add_quote(quote)
        onchain_quotes = await self.tf.extract_quotes(tx_hash)

        # USDT <--(maker1)--> MKR
        assert onchain_quotes[0].filled_swaps[0].taker_amount == 5181428827
        assert onchain_quotes[0].filled_swaps[0].maker_amount == 3340893066982031220

        # USDT <--(maker1)--> LINK
        assert onchain_quotes[1].filled_swaps[0].taker_amount == 1817460367
        assert onchain_quotes[1].filled_swaps[0].maker_amount == 121325122320692909620

        # USDC <--(maker2)--> LINK
        assert onchain_quotes[2].filled_swaps[0].taker_amount == 235075491
        assert onchain_quotes[2].filled_swaps[0].maker_amount == 15679231062155346862
