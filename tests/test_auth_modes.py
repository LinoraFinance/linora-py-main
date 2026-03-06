"""Tests for AuthLevel, linoraL2, linoraSubkey, linoraApiKey, and on_token_expired."""

import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from linora_py import AuthLevel, linoraApiKey, linoraL2, linoraSubkey
from linora_py.api.api_client import linoraApiClient, _jwt_exp
from linora_py.environment import TESTNET

MOCK_SYSTEM_CONFIG = MagicMock()

L2_KEY = "0x1234567890abcdef"
L2_ADDR = "0xdeadbeef"
API_KEY = "test-api-key-token"


def _make_jwt(exp: float) -> str:
    """Build a minimal but structurally valid JWT with the given exp claim."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


# ---------------------------------------------------------------------------
# AuthLevel
# ---------------------------------------------------------------------------


class TestAuthLevel:
    def test_ordering(self):
        assert AuthLevel.UNAUTHENTICATED < AuthLevel.AUTHENTICATED
        assert AuthLevel.AUTHENTICATED < AuthLevel.TRADING
        assert AuthLevel.TRADING < AuthLevel.FULL
        

    def test_gte_comparisons(self):
        assert AuthLevel.FULL >= AuthLevel.TRADING
        assert AuthLevel.FULL >= AuthLevel.AUTHENTICATED
        assert AuthLevel.FULL >= AuthLevel.UNAUTHENTICATED
        assert AuthLevel.TRADING >= AuthLevel.TRADING
        assert AuthLevel.TRADING >= AuthLevel.AUTHENTICATED
        assert not (AuthLevel.TRADING >= AuthLevel.FULL)
        assert not (AuthLevel.AUTHENTICATED >= AuthLevel.TRADING)

    def test_values(self):
        assert AuthLevel.UNAUTHENTICATED == 0
        assert AuthLevel.AUTHENTICATED == 1
        assert AuthLevel.TRADING == 2
        assert AuthLevel.FULL == 3


# ---------------------------------------------------------------------------
# linoraL2 — full account key
# ---------------------------------------------------------------------------


class TestlinoraL2:
    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_successful_init(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        mock_api = MockApiClient.return_value
        mock_api.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG

        p = linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR)

        MockApiClient.assert_called_once_with(env=TESTNET, logger=None)
        mock_api.fetch_system_config.assert_called_once()
        MockSubkeyAccount.assert_called_once_with(config=MOCK_SYSTEM_CONFIG, l2_private_key=L2_KEY, l2_address=L2_ADDR)
        mock_api.init_account.assert_called_once_with(MockSubkeyAccount.return_value)
        MockWsClient.return_value.init_account.assert_called_once_with(MockSubkeyAccount.return_value)
        assert p.config is MOCK_SYSTEM_CONFIG

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_ws_timeout_forwarded(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR, ws_timeout=42)
        MockWsClient.assert_called_once_with(
            env=TESTNET, logger=None, ws_timeout=42, api_client=MockApiClient.return_value
        )

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_ws_enabled_false_skips_ws_client(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR, ws_enabled=False)
        MockWsClient.assert_not_called()
        assert p.ws_client is None

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_ws_enabled_false_no_ws_init_account(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR, ws_enabled=False)
        MockWsClient.return_value.init_account.assert_not_called()

    def test_missing_env_raises(self):
        with pytest.raises((ValueError, TypeError)):
            linoraL2(env=None, l2_private_key=L2_KEY, l2_address=L2_ADDR)

    @patch("linora_py.linora_l2.linoraApiClient")
    def test_missing_l2_private_key_raises(self, MockApiClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        with pytest.raises(ValueError):
            linoraL2(env=TESTNET, l2_private_key="", l2_address=L2_ADDR)

    @patch("linora_py.linora_l2.linoraApiClient")
    def test_missing_l2_address_raises(self, MockApiClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        with pytest.raises(ValueError):
            linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address="")

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_capabilities_full(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR)
        assert p.auth_level == AuthLevel.FULL
        assert p.is_authenticated is True
        assert p.can_trade is True
        assert p.can_withdraw is True


# ---------------------------------------------------------------------------
# linoraSubkey — trade-scoped, no withdrawals
# ---------------------------------------------------------------------------


class TestlinoraSubkey:
    def test_is_subclass_of_linora_l2(self):
        assert issubclass(linoraSubkey, linoraL2)

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_capabilities_trading_no_withdraw(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraSubkey(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR)
        assert p.auth_level == AuthLevel.TRADING
        assert p.is_authenticated is True
        assert p.can_trade is True
        assert p.can_withdraw is False

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_auth_level_differs_from_parent(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        """linoraSubkey overrides auth_level to TRADING; linoraL2 returns FULL."""
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        subkey = linoraSubkey(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR)
        l2 = linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR)
        assert subkey.auth_level == AuthLevel.TRADING
        assert l2.auth_level == AuthLevel.FULL


# ---------------------------------------------------------------------------
# linoraApiKey — read-only
# ---------------------------------------------------------------------------


class TestlinoraApiKey:
    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_successful_init(self, MockApiClient, MockWsClient):
        mock_api = MockApiClient.return_value
        mock_api.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG

        p = linoraApiKey(env=TESTNET, api_key=API_KEY)

        MockApiClient.assert_called_once_with(env=TESTNET, logger=None, auto_auth=False, on_token_expired=None)
        mock_api.fetch_system_config.assert_called_once()
        mock_api.set_token.assert_called_once_with(API_KEY)
        assert p.config is MOCK_SYSTEM_CONFIG

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_on_token_expired_wired_to_api_client(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        callback = MagicMock(return_value="new-token")

        linoraApiKey(env=TESTNET, api_key=API_KEY, on_token_expired=callback)

        MockApiClient.assert_called_once_with(env=TESTNET, logger=None, auto_auth=False, on_token_expired=callback)

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_ws_client_receives_api_client(self, MockApiClient, MockWsClient):
        mock_api = MockApiClient.return_value
        mock_api.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG

        linoraApiKey(env=TESTNET, api_key=API_KEY)

        MockWsClient.assert_called_once_with(env=TESTNET, logger=None, ws_timeout=None, api_client=mock_api)

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_ws_timeout_forwarded(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        linoraApiKey(env=TESTNET, api_key=API_KEY, ws_timeout=30)
        MockWsClient.assert_called_once_with(
            env=TESTNET, logger=None, ws_timeout=30, api_client=MockApiClient.return_value
        )

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_ws_enabled_false_skips_ws_client(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraApiKey(env=TESTNET, api_key=API_KEY, ws_enabled=False)
        MockWsClient.assert_not_called()
        assert p.ws_client is None

    def test_missing_env_raises(self):
        with pytest.raises((ValueError, TypeError)):
            linoraApiKey(env=None, api_key=API_KEY)

    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_missing_api_key_raises(self, MockApiClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        with pytest.raises(ValueError):
            linoraApiKey(env=TESTNET, api_key="")

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_capabilities_authenticated_read_only(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraApiKey(env=TESTNET, api_key=API_KEY)
        assert p.auth_level == AuthLevel.AUTHENTICATED
        assert p.is_authenticated is True
        assert p.can_trade is False
        assert p.can_withdraw is False

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_no_account_attribute(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraApiKey(env=TESTNET, api_key=API_KEY)
        assert not hasattr(p, "account")

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    def test_set_token_called_after_config(self, MockApiClient, MockWsClient):
        mock_api = MockApiClient.return_value
        call_order = []
        mock_api.fetch_system_config.side_effect = lambda: call_order.append("fetch_config") or MOCK_SYSTEM_CONFIG
        mock_api.set_token.side_effect = lambda _: call_order.append("set_token")

        linoraApiKey(env=TESTNET, api_key=API_KEY)

        assert call_order == ["fetch_config", "set_token"]


# ---------------------------------------------------------------------------
# _jwt_exp helper
# ---------------------------------------------------------------------------


class TestJwtExp:
    def test_extracts_exp_from_valid_jwt(self):
        exp = time.time() + 3600
        token = _make_jwt(exp)
        result = _jwt_exp(token)
        assert result is not None
        assert abs(result - exp) < 1

    def test_returns_none_for_non_jwt(self):
        assert _jwt_exp("not-a-jwt") is None
        assert _jwt_exp("") is None
        assert _jwt_exp("only.two") is None

    def test_returns_none_for_jwt_without_exp(self):
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(b'{"sub":"user"}').rstrip(b"=").decode()
        token = f"{header}.{payload}.sig"
        assert _jwt_exp(token) is None


# ---------------------------------------------------------------------------
# on_token_expired — api_client._validate_auth behavior
# ---------------------------------------------------------------------------


class TestOnTokenExpired:
    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_called_when_token_expired(self, mock_config):
        new_token = "fresh-token"  # noqa: S105
        callback = MagicMock(return_value=new_token)

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token("old-token")
        client.auth_timestamp = time.time() - 300  # 5 minutes ago → expired

        client._validate_auth()

        callback.assert_called_once()
        assert "Bearer fresh-token" in str(client.client.headers.get("Authorization", ""))

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_not_called_when_token_fresh(self, mock_config):
        callback = MagicMock(return_value="fresh-token")

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token("current-token")
        # auth_timestamp set by set_token — token is fresh

        client._validate_auth()

        callback.assert_not_called()

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_no_callback_expired_token_no_error(self, mock_config):
        """Without a callback, expired manual tokens are silently reused (no crash)."""
        client = linoraApiClient(env=TESTNET, auto_auth=False)
        client.set_token("old-token")
        client.auth_timestamp = time.time() - 300

        # Should not raise
        client._validate_auth()

        assert "Bearer old-token" in str(client.client.headers.get("Authorization", ""))

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_returning_none_leaves_old_token(self, mock_config):
        """If callback returns None, the old token stays in place."""
        callback = MagicMock(return_value=None)

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token("old-token")
        client.auth_timestamp = time.time() - 300

        client._validate_auth()

        callback.assert_called_once()
        assert "Bearer old-token" in str(client.client.headers.get("Authorization", ""))

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_returning_none_logs_warning(self, mock_config):
        """If callback returns None, a warning is logged."""
        callback = MagicMock(return_value=None)

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token("old-token")
        client.auth_timestamp = time.time() - 300

        with patch.object(client.logger, "warning") as mock_warning:
            client._validate_auth()
            mock_warning.assert_called_once()
            assert "None" in mock_warning.call_args[0][0] or "expired" in mock_warning.call_args[0][0]

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_updates_auth_timestamp(self, mock_config):
        """set_token() called by callback resets auth_timestamp."""
        callback = MagicMock(return_value="new-token")

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token("old-token")
        client.auth_timestamp = time.time() - 300

        before = int(time.time())
        client._validate_auth()
        after = int(time.time()) + 1  # +1 to absorb int truncation

        assert before <= client.auth_timestamp <= after

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_called_when_jwt_exp_in_past(self, mock_config):
        """Callback fires when JWT exp claim is in the past (JWT-based expiry)."""
        expired_token = _make_jwt(time.time() - 10)
        callback = MagicMock(return_value="fresh-token")

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token(expired_token)

        client._validate_auth()

        callback.assert_called_once()

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_callback_not_called_when_jwt_exp_in_future(self, mock_config):
        """Callback does not fire when JWT exp claim is well in the future."""
        fresh_token = _make_jwt(time.time() + 3600)
        callback = MagicMock(return_value="fresh-token")

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token(fresh_token)

        client._validate_auth()

        callback.assert_not_called()

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_jwt_exp_takes_precedence_over_auth_timestamp(self, mock_config):
        """A token with a far-future exp is not refreshed even if auth_timestamp is old."""
        far_future_token = _make_jwt(time.time() + 3600)
        callback = MagicMock(return_value="new-token")

        client = linoraApiClient(env=TESTNET, auto_auth=False, on_token_expired=callback)
        client.set_token(far_future_token)
        # Simulate old auth_timestamp (would trigger fallback path)
        client.auth_timestamp = time.time() - 300

        client._validate_auth()

        # JWT exp says token is still valid — callback must NOT be called
        callback.assert_not_called()


# ---------------------------------------------------------------------------
# _validate_auth precedence: manual token > auth_provider
# ---------------------------------------------------------------------------


class TestValidateAuthPrecedence:
    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_manual_token_bypasses_auth_provider(self, mock_config):
        """When both _manual_token and auth_provider are set, auth_provider is ignored."""
        auth_provider = MagicMock()
        auth_provider.refresh_if_needed.return_value = "provider-token"

        client = linoraApiClient(env=TESTNET, auto_auth=False, auth_provider=auth_provider)
        client.set_token(_make_jwt(time.time() + 3600))

        client._validate_auth()

        auth_provider.refresh_if_needed.assert_not_called()
        assert "Authorization" in client.client.headers

    @patch.object(linoraApiClient, "fetch_system_config", return_value=MagicMock())
    def test_manual_token_with_provider_logs_warning(self, mock_config):
        """A warning is logged when both _manual_token and auth_provider are set."""
        auth_provider = MagicMock()
        auth_provider.refresh_if_needed.return_value = "provider-token"

        client = linoraApiClient(env=TESTNET, auto_auth=False, auth_provider=auth_provider)
        client.set_token(_make_jwt(time.time() - 10))  # expired → triggers refresh path
        callback = MagicMock(return_value="new-token")
        client.on_token_expired = callback

        with patch.object(client.logger, "warning") as mock_warning:
            client._validate_auth()
            mock_warning.assert_called_once()
            assert "auth_provider" in mock_warning.call_args[0][0]


# ---------------------------------------------------------------------------
# async with context manager
# ---------------------------------------------------------------------------


class TestAsyncContextManager:
    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    @pytest.mark.asyncio
    async def test_linora_l2_async_with(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        mock_ws = MockWsClient.return_value
        mock_ws.close = AsyncMock()

        async with linoraL2(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR) as client:
            assert client is not None

        mock_ws.close.assert_called_once()

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    @pytest.mark.asyncio
    async def test_linora_api_key_async_with(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        mock_ws = MockWsClient.return_value
        mock_ws.close = AsyncMock()

        async with linoraApiKey(env=TESTNET, api_key=API_KEY) as client:
            assert client is not None

        mock_ws.close.assert_called_once()

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    @pytest.mark.asyncio
    async def test_async_with_returns_self(self, MockApiClient, MockWsClient):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        MockWsClient.return_value.close = AsyncMock()

        p = linoraApiKey(env=TESTNET, api_key=API_KEY)
        result = await p.__aenter__()
        assert result is p
        await p.__aexit__(None, None, None)

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    @pytest.mark.asyncio
    async def test_aexit_returns_false(self, MockApiClient, MockWsClient):
        """__aexit__ must return False so exceptions propagate normally."""
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        MockWsClient.return_value.close = AsyncMock()

        p = linoraApiKey(env=TESTNET, api_key=API_KEY)
        await p.__aenter__()
        result = await p.__aexit__(None, None, None)
        assert result is False


# ---------------------------------------------------------------------------
# linoraSubkey with ws_enabled=False
# ---------------------------------------------------------------------------


class TestlinoraSubkeyWsDisabled:
    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_ws_client_is_none(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraSubkey(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR, ws_enabled=False)
        assert p.ws_client is None

    @patch("linora_py.linora_l2.SubkeyAccount")
    @patch("linora_py.linora_l2.linoraWebsocketClient")
    @patch("linora_py.linora_l2.linoraApiClient")
    def test_capabilities_preserved_when_ws_disabled(self, MockApiClient, MockWsClient, MockSubkeyAccount):
        MockApiClient.return_value.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        p = linoraSubkey(env=TESTNET, l2_private_key=L2_KEY, l2_address=L2_ADDR, ws_enabled=False)
        assert p.auth_level == AuthLevel.TRADING
        assert p.can_trade is True
        assert p.can_withdraw is False


# ---------------------------------------------------------------------------
# close() on partially-initialized client
# ---------------------------------------------------------------------------


class TestClosePartialInit:
    @pytest.mark.asyncio
    async def test_close_before_ws_client_set(self):
        """close() must not raise AttributeError if ws_client was never assigned."""
        from linora_py._client_base import _ClientBase

        obj = object.__new__(_ClientBase)
        # Neither ws_client nor api_client are set — simulates constructor raising early
        await obj.close()  # must not raise

    @pytest.mark.asyncio
    async def test_close_with_none_ws_client(self):
        """close() is safe when ws_client is explicitly None."""
        from linora_py._client_base import _ClientBase

        obj = object.__new__(_ClientBase)
        obj.ws_client = None
        # api_client not set
        await obj.close()  # must not raise

    @patch("linora_py.linora_api_key.linoraWebsocketClient")
    @patch("linora_py.linora_api_key.linoraApiClient")
    @pytest.mark.asyncio
    async def test_close_with_ws_enabled_false(self, MockApiClient, MockWsClient):
        """close() on a ws_enabled=False client closes only the HTTP client."""
        mock_api = MockApiClient.return_value
        mock_api.fetch_system_config.return_value = MOCK_SYSTEM_CONFIG
        mock_api.client = MagicMock()

        p = linoraApiKey(env=TESTNET, api_key=API_KEY, ws_enabled=False)
        await p.close()

        MockWsClient.return_value.close.assert_not_called()
        mock_api.client.close.assert_called_once()


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------


def test_all_classes_importable_from_linora_py():
    from linora_py import AuthLevel, linoraApiKey, linoraL2, linoraSubkey  # noqa: F401


def test_environment_importable_from_linora_py():
    from linora_py import PROD, TESTNET, Environment  # noqa: F401

    assert PROD == "prod"
    assert TESTNET == "testnet"


def test_invalid_env_string_raises():
    with pytest.raises(ValueError, match="mainnet"):
        linoraL2(env="mainnet", l2_private_key=L2_KEY, l2_address=L2_ADDR)


def test_invalid_env_string_raises_api_key():
    with pytest.raises(ValueError, match="mainnet"):
        linoraApiKey(env="mainnet", api_key=API_KEY)
