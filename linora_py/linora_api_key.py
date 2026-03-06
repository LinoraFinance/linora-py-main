import logging
from collections.abc import Callable

from linora_py._client_base import _ClientBase
from linora_py.api.api_client import linoraApiClient
from linora_py.api.ws_client import linoraWebsocketClient
from linora_py.auth_level import AuthLevel
from linora_py.environment import Environment, _validate_env
from linora_py.utils import raise_value_error

__all__ = ["linoraApiKey"]



class linoraApiKey(_ClientBase):
    """API key authentication: use a pre-generated long-lived token string.

    No private key required. Suitable for read-only or pre-authorized access.

    Args:
        env (Environment): Environment
        api_key (str): Pre-generated long-lived API token (required)
        logger (logging.Logger, optional): Logger. Defaults to None.
        ws_timeout (int, optional): WebSocket read timeout in seconds. Defaults to None (uses default).
        ws_enabled (bool, optional): Whether to create a WebSocket client. Defaults to True.
            Set to False for REST-only use cases to avoid starting background connection machinery.
        on_token_expired (Callable[[], str | None], optional): Called when the injected token
            expires. Expiry is detected from the JWT ``exp`` claim when present; falls back to
            a 4-minute window for opaque tokens. Should return a fresh token, or None if
            unavailable. Without this callback, expired tokens are silently reused until the
            server rejects them.

    Examples:
        >>> from linora_py import linoraApiKey
        >>> from linora_py.environment import Environment
        >>> linora = linoraApiKey(
        ...     env=Environment.TESTNET,
        ...     api_key="<long-lived-token>"
        ... )
        >>> linora.api_client.fetch_balances()
        >>> # With token refresh:
        >>> linora = linoraApiKey(
        ...     env=Environment.TESTNET,
        ...     api_key="<token>",
        ...     on_token_expired=lambda: fetch_new_token()
        ... )
    """

    def __init__(
        self,
        env: Environment,
        api_key: str,
        logger: logging.Logger | None = None,
        ws_timeout: int | None = None,
        ws_enabled: bool = True,
        on_token_expired: Callable[[], str | None] | None = None,
    ):
        _validate_env(env, "linoraApiKey")

        if not api_key:
            raise_value_error(f"linoraApiKey: API key is required, got {api_key!r}")

        self.env = env
        self.logger: logging.Logger = logger or logging.getLogger(__name__)

        self.api_client = linoraApiClient(env=env, logger=logger, auto_auth=False, on_token_expired=on_token_expired)
        self.ws_client: linoraWebsocketClient | None = (
            linoraWebsocketClient(env=env, logger=logger, ws_timeout=ws_timeout, api_client=self.api_client)
            if ws_enabled
            else None
        )
        self.config = self.api_client.fetch_system_config()
        self.api_client.set_token(api_key)

    @property
    def auth_level(self) -> AuthLevel:
        """Always ``AuthLevel.AUTHENTICATED`` — token present, no signing key."""
        return AuthLevel.AUTHENTICATED

    @property
    def is_authenticated(self) -> bool:
        """Always ``True`` — API key was provided at construction."""
        return True

    @property
    def can_trade(self) -> bool:
        """Always ``False`` — no L2 signing key available."""
        return False

    @property
    def can_withdraw(self) -> bool:
        """Always ``False`` — no L2 signing key available."""
        return False
