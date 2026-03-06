"""Tests for RPC version functionality in linoraAccount and linora."""

from unittest.mock import MagicMock, patch

from linora_py import linora
from linora_py.account.account import linoraAccount
from linora_py.environment import TESTNET
from tests.mocks.api_client import MockApiClient

TEST_L1_ADDRESS = "0xd2c7314539dCe7752c8120af4eC2AA750Cf2035e"
TEST_L1_PRIVATE_KEY = "0xf8e4d1d772cdd44e5e77615ad11cc071c94e4c06dc21150d903f28e6aa6abdff"
TEST_L2_PRIVATE_KEY = "0x543b6cf6c91817a87174aaea4fb370ac1c694e864d7740d728f8344d53e815"


class TestlinoraAccountRpcVersion:
    """Test RPC version functionality in linoraAccount."""

    def test_account_without_rpc_version(self):
        """Test that account uses default RPC URL when rpc_version is not provided."""
        api_client = MockApiClient()
        config = api_client.fetch_system_config()
        

        with patch("linora_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            linoraAccount(
                config=config,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
            )

            # Verify that FullNodeClient was called with the default RPC URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            assert call_args.kwargs["node_url"] == config.starknet_fullnode_rpc_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.linora.trade/rpc/v0.5"

    def test_account_with_rpc_version(self):
        """Test that account constructs RPC URL with version when rpc_version is provided."""
        api_client = MockApiClient()
        config = api_client.fetch_system_config()

        with patch("linora_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            linoraAccount(
                config=config,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
                rpc_version="v0_9",
            )

            # Verify that FullNodeClient was called with the constructed URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{config.starknet_fullnode_rpc_base_url}/rpc/v0_9"
            assert call_args.kwargs["node_url"] == expected_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.linora.trade/rpc/v0_9"

    def test_account_with_different_rpc_version(self):
        """Test that account works with different RPC versions."""
        api_client = MockApiClient()
        config = api_client.fetch_system_config()

        with patch("linora_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            linoraAccount(
                config=config,
                l1_address=TEST_L1_ADDRESS,
                l2_private_key=TEST_L2_PRIVATE_KEY,
                rpc_version="v0_8",
            )

            # Verify that FullNodeClient was called with the correct version
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{config.starknet_fullnode_rpc_base_url}/rpc/v0_8"
            assert call_args.kwargs["node_url"] == expected_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.linora.trade/rpc/v0_8"


class TestlinoraRpcVersion:
    """Test RPC version functionality in linora class."""

    def test_linora_init_account_with_rpc_version(self):
        """Test that linora.init_account passes rpc_version to linoraAccount."""
        # Create a mock linora instance
        linora = linora.__new__(linora)
        linora.env = TESTNET
        linora.logger = MagicMock()
        linora.api_client = MockApiClient()
        linora.ws_client = MagicMock()
        linora.config = linora.api_client.fetch_system_config()
        linora.account = None

        with patch("linora_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Initialize account with rpc_version
            linora.init_account(
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
                rpc_version="v0_9",
            )

            # Verify that FullNodeClient was called with the correct URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{linora.config.starknet_fullnode_rpc_base_url}/rpc/v0_9"
            assert call_args.kwargs["node_url"] == expected_url
            assert linora.account is not None

    @patch("linora_py.linora.linoraApiClient")
    @patch("linora_py.linora.linoraWebsocketClient")
    def test_linora_init_with_rpc_version(self, mock_ws_client, mock_api_client):
        """Test that linora.__init__ passes rpc_version to linoraAccount."""
        # Setup mocks
        mock_api_instance = MockApiClient()
        mock_api_client.return_value = mock_api_instance
        mock_ws_client.return_value = MagicMock()

        with patch("linora_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Create linora instance with rpc_version
            linora = linora(
                env=TESTNET,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
                rpc_version="v0_9",
            )

            # Verify that FullNodeClient was called with the correct URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{linora.config.starknet_fullnode_rpc_base_url}/rpc/v0_9"
            assert call_args.kwargs["node_url"] == expected_url
            assert linora.account is not None

    @patch("linora_py.linora.linoraApiClient")
    @patch("linora_py.linora.linoraWebsocketClient")
    def test_linora_init_without_rpc_version(self, mock_ws_client, mock_api_client):
        """Test that linora.__init__ uses default RPC URL when rpc_version is not provided."""
        # Setup mocks
        mock_api_instance = MockApiClient()
        mock_api_client.return_value = mock_api_instance
        mock_ws_client.return_value = MagicMock()

        with patch("linora_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Create linora instance without rpc_version
            linora = linora(
                env=TESTNET,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
            )

            # Verify that FullNodeClient was called with default RPC URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            assert call_args.kwargs["node_url"] == linora.config.starknet_fullnode_rpc_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.linora.trade/rpc/v0.5"
            assert linora.account is not None
