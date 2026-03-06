"""linora Python SDK.

Choose the right client class for your use-case:

+------------------+------------------+---------+-----------+--------+------------------+
| Class            | Credentials      | Trade   | Withdraw  | Auth   | Typical use-case |
+==================+==================+=========+===========+========+==================+
| linora          | L1 private key   | yes     | yes       | FULL   | Full account via |
|                  | (or Ledger)      |         |           |        | L1 key           |
+------------------+------------------+---------+-----------+--------+------------------+
| linoraL2        | L2 private key   | yes     | yes       | FULL   | Full account via |
|                  | + L2 address     |         |           |        | L2 key directly  |
+------------------+------------------+---------+-----------+--------+------------------+
| linoraSubkey    | L2 subkey        | yes     | no        | TRADING| Registered       |
|                  | + main L2 addr   |         |           |        | trade-scoped key |
+------------------+------------------+---------+-----------+--------+------------------+
| linoraApiKey    | Pre-generated    | no      | no        | AUTH   | Read-only /      |
|                  | API token        |         |           |        | server-side apps |
+------------------+------------------+---------+-----------+--------+------------------+
"""

from .auth_level import AuthLevel
from .environment import NIGHTLY, PROD, TESTNET, Environment
from .linora import linora
from .linora_api_key import linoraApiKey
from .linora_l2 import linoraL2
from .linora_subkey import linoraSubkey

__all__ = [
    "AuthLevel",
    "Environment",
    "NIGHTLY",
    "PROD",
    "TESTNET",
    "linora",
    "linoraApiKey",
    "linoraL2",
    "linoraSubkey",
]
