import asyncio
import os

from starknet_py.common import int_from_hex

from linora_py import linora
from linora_py.api.ws_client import linoraWebsocketChannel
from linora_py.environment import TESTNET

# Environment variables
TEST_L1_ADDRESS = os.getenv("L1_ADDRESS", "")
TEST_L1_PRIVATE_KEY = int_from_hex(os.getenv("L1_PRIVATE_KEY", ""))
LOG_FILE = os.getenv("LOG_FILE", "FALSE").lower() == "true"


if LOG_FILE:
    from linora_py.common.file_logging import file_logger

    logger = file_logger
    logger.info("Using file logger")
else:
    from linora_py.common.console_logging import console_logger

    logger = console_logger
    logger.info("Using console logger")


async def callback_general(ws_channel: linoraWebsocketChannel, message: dict) -> None:
    message.get("params", {}).get("channel")
    market = message.get("params", {}).get("data", {}).get("market")
    logger.info(f"callback_general(): Channel:{ws_channel} market:{market} message:{message}")


async def linora_ws_subscribe(linora: linora) -> None:
    """This function subscribes to all Websocket channels
    For market specific channels subscribe to ETH-USD-PERP market"""
    is_connected = False
    while not is_connected:
        is_connected = await linora.ws_client.connect()
        if not is_connected:
            logger.info("connection failed, retrying in 1 second")
            await asyncio.sleep(1)
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.ACCOUNT,
        callback_general,
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.BALANCE_EVENTS,
        callback_general,
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.BBO,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.FILLS,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.FUNDING_DATA,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.FUNDING_PAYMENTS,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.MARKETS_SUMMARY,
        callback=callback_general,
        params={"market": "BTC-USD-PERP"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.ORDERS,
        callback=callback_general,
        params={"market": "ALL"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.ORDER_BOOK,
        callback=callback_general,
        params={"market": "ETH-USD-PERP", "refresh_rate": "100ms", "price_tick": "0_1", "depth": 15},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.POSITIONS,
        callback_general,
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.TRADES,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.TRADEBUSTS,
        callback_general,
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.TRANSACTIONS,
        callback_general,
    )
    await linora.ws_client.subscribe(
        linoraWebsocketChannel.TRANSFERS,
        callback_general,
    )


linora = linora(
    env=TESTNET,
    l1_address=TEST_L1_ADDRESS,
    l1_private_key=TEST_L1_PRIVATE_KEY,
    logger=logger,
)

asyncio.get_event_loop().run_until_complete(linora_ws_subscribe(linora))
asyncio.get_event_loop().run_forever()
