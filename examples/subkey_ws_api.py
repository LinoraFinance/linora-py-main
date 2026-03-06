#!/usr/bin/env python3
"""
Example script demonstrating L2-only WebSocket usage with linoraSubkey.

This example shows how to use WebSocket functionality with only L2 credentials (subkey mode),
without requiring L1 Ethereum address or private key.

Requirements:
- L2_PRIVATE_KEY: Starknet private key for the subkey
- L2_ADDRESS: L2 address of the main account (not the subkey address)

Usage:
    export L2_PRIVATE_KEY="0x..."
    export L2_ADDRESS="0x..."
    python examples/subkey_ws_api.py
"""

import asyncio
import os
import sys

from linora_py import linoraSubkey
from linora_py.api.ws_client import linoraWebsocketChannel
from linora_py.environment import TESTNET

# Add the parent directory to the path so we can import linora_py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def on_markets_summary(ws_channel, message):
    """Callback for markets summary WebSocket messages."""
    print(f"📊 Markets Summary: {message}")


async def on_orders(ws_channel, message):
    """Callback for orders WebSocket messages."""
    print(f"📋 Orders: {message}")


async def on_fills(ws_channel, message):
    """Callback for fills WebSocket messages."""
    print(f"💰 Fills: {message}")


async def main():
    """Main function demonstrating L2-only WebSocket usage."""
    # Get L2 credentials from environment variables
    l2_private_key = os.getenv("L2_PRIVATE_KEY")
    l2_address = os.getenv("L2_ADDRESS")

    if not l2_private_key:
        print("Error: L2_PRIVATE_KEY environment variable not set")
        print("Please set your L2 private key: export L2_PRIVATE_KEY='0x...'")
        return

    
    if not l2_address:
        print("Error: L2_ADDRESS environment variable not set")
        print("Please set the L2 address of the main account: export L2_ADDRESS='0x...'")
        return

    print("🚀 Starting linora L2-only WebSocket example...")
    print(f"L2 Address: {l2_address}")
    print(f"L2 Private Key: {l2_private_key[:10]}...")

    # Initialize linoraSubkey with L2-only credentials
    linora = linoraSubkey(
        env=TESTNET,
        l2_private_key=l2_private_key,
        l2_address=l2_address,
    )

    try:
        print("\n🔌 Connecting to WebSocket...")
        await linora.ws_client.connect()
        print("✅ WebSocket connected successfully!")

        # Subscribe to public channels
        print("\n📊 Subscribing to public channels...")
        await linora.ws_client.subscribe(channel=linoraWebsocketChannel.MARKETS_SUMMARY, callback=on_markets_summary)
        print("✅ Subscribed to markets summary")

        # Subscribe to private channels (requires authentication)
        print("\n🔐 Subscribing to private channels...")
        await linora.ws_client.subscribe(
            channel=linoraWebsocketChannel.ORDERS, callback=on_orders, params={"market": "ALL"}
        )
        print("✅ Subscribed to orders")

        await linora.ws_client.subscribe(
            channel=linoraWebsocketChannel.FILLS, callback=on_fills, params={"market": "ETH-USD-PERP"}
        )
        print("✅ Subscribed to fills")

        # Wait for messages (run forever like the original example)
        print("\n⏳ Listening for WebSocket messages...")
        print("(Press Ctrl+C to stop)")

        try:
            # Run forever like the original connect_ws_api.py
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")

        print("\n🔌 WebSocket session completed!")

        print("\n🎉 L2-only WebSocket example completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
