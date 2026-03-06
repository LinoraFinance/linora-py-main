from unittest.mock import AsyncMock, patch

import pytest
from websockets import State

from linora_py import linora
from linora_py.account.account import linoraAccount
from linora_py.api.ws_client import linoraWebsocketClient
from linora_py.environment import TESTNET

MOCK_L1_PRIVATE_KEY = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
MOCK_L1_ADDRESS = "0xabcdef0123456789abcdef0123456789abcdef01"


@pytest.fixture
def mock_linora() -> linora:
    return linora(l1_address=MOCK_L1_ADDRESS, l1_private_key=MOCK_L1_PRIVATE_KEY, env=TESTNET)


@pytest.fixture
def ws_client(mock_linora: linora) -> linoraWebsocketClient:
    return mock_linora.ws_client


@pytest.mark.asyncio
@patch("websockets.connect", new_callable=AsyncMock)
async def test_connect_authenticated(
    mock_connect: AsyncMock,
    ws_client: linoraWebsocketClient,
    mock_linora: linora,
) -> None:
    """Tests successful authenticated connection."""
    mock_ws_connection = AsyncMock()
    mock_ws_connection.state = State.OPEN
    mock_connect.return_value = mock_ws_connection

    mock_account: linoraAccount = mock_linora.account

    # Mock _send_auth_id to prevent actual sending during test
    with patch.object(ws_client, "_send_auth_id", new_callable=AsyncMock) as mock_send_auth:
        connected = await ws_client.connect()

        assert connected is True
        # Verify both User-Agent and Authorization headers are included
        call_args = mock_connect.call_args
        headers = call_args.kwargs["additional_headers"]
        assert "User-Agent" in headers
        assert headers["User-Agent"].startswith("linora-py/")
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {mock_account.jwt_token}"

        mock_send_auth.assert_called_once_with(mock_ws_connection, mock_account.jwt_token)
        assert ws_client.ws.state == State.OPEN


@pytest.mark.asyncio
@patch("websockets.connect", new_callable=AsyncMock)
async def test_connect_unauthenticated_with_user_agent(mock_connect: AsyncMock) -> None:
    """Tests that User-Agent is included even in unauthenticated connections."""
    mock_ws_connection = AsyncMock()
    mock_ws_connection.state = State.OPEN
    mock_connect.return_value = mock_ws_connection

    # Create ws_client without account (unauthenticated)
    ws_client = linoraWebsocketClient(env=TESTNET)

    connected = await ws_client.connect()

    assert connected is True
    # Verify User-Agent is still included even without authentication
    call_args = mock_connect.call_args
    headers = call_args.kwargs["additional_headers"]
    assert "User-Agent" in headers
    assert headers["User-Agent"].startswith("linora-py/")
    # No Authorization header in unauthenticated mode
    assert "Authorization" not in headers
