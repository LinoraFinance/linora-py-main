from linora_py.auth_level import AuthLevel
from linora_py.linora_l2 import linoraL2

__all__ = ["linoraSubkey"]


class linoraSubkey(linoraL2):
    """Registered subkey authentication — trade-scoped subclass of linoraL2
    with trade-scoped capabilities (no withdrawals).

    Subkeys are registered signing keys scoped to order management only.
    Use ``linoraL2`` directly when authenticating with a main account key.

    Args:
        env (Environment): Environment
        l2_private_key (str): The subkey's L2 private key (required)
        l2_address (str): The *main account* address this subkey is registered under.
            This is **not** the subkey's own derived address — it must be the address
            of the parent account that registered this subkey.
        logger (logging.Logger, optional): Logger. Defaults to None.
        ws_timeout (int, optional): WebSocket read timeout in seconds. Defaults to None.
        ws_enabled (bool, optional): Whether to create a WebSocket client. Defaults to True.

    Examples:
        >>> from linora_py import linoraSubkey
        >>> from linora_py.environment import TESTNET
        >>> linora = linoraSubkey(
        ...     env=TESTNET,
        ...     l2_private_key="0x<subkey-private-key>",
        ...     l2_address="0x<main-account-address>",  # parent account, not subkey address
        ... )
        >>> linora.can_trade
        True
        >>> linora.can_withdraw
        False
    """
    

    @property
    def auth_level(self) -> AuthLevel:
        """``AuthLevel.TRADING`` — subkey can sign orders but not withdrawals."""
        return AuthLevel.TRADING

    @property
    def can_withdraw(self) -> bool:
        """Always ``False`` — subkeys can only sign orders; direct on-chain operations
        (deposit, withdraw, transfer) require the full account key."""
        return False
