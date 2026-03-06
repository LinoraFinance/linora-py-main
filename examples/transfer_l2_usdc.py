import asyncio
import os
from decimal import Decimal

from starknet_py.common import int_from_hex

from linora_py import linora
from linora_py.environment import TESTNET


# Environment variables
TEST_L1_ADDRESS = os.getenv("L1_ADDRESS", "")
TEST_L1_PRIVATE_KEY = int_from_hex(os.getenv("L1_PRIVATE_KEY", ""))
LOG_FILE = os.getenv("LOG_FILE", "FALSE").lower() == "true"

if LOG_FILE:
    from linora_py.common.file_logging import file_logger

    logger = file_logger
else:
    from linora_py.common.console_logging import console_logger

    logger = console_logger


linora = linora(env=TESTNET, l1_address=TEST_L1_ADDRESS, l1_private_key=TEST_L1_PRIVATE_KEY)

recipient_address = ""
amount = Decimal(0)
logger.info(f"Transferring USDC from {TEST_L1_ADDRESS} to {recipient_address} amount {amount}")

asyncio.run(linora.account.transfer_on_l2(recipient_address, amount))
