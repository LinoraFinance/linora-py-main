from linora_py import linora
from linora_py.environment import TESTNET


def test_system_config():
    linora = linora(env=TESTNET)
    assert linora.config.starknet_gateway_url == ""
    assert linora.config.starknet_chain_id == "PRIVATE_SN_POTC_SEPOLIA"
    assert linora.config.block_explorer_url == "https://app.testnet.linora.trade/explorer"
    assert linora.config.bridged_tokens[0].name == "TEST USDC"
