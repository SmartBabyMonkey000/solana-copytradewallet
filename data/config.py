from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair #type: ignore

#########################################################################################
# Wallet a copiar
#########################################################################################
copy_wallet_address = ""


#########################################################################################
# Configuracion de swaps
#########################################################################################
amount_buy_sol = 0.00066
profit_percent = 10
FeeLamports = 0.00035
slippage_bps = 1000

#########################################################################################
# Clave publica & clave privada
#########################################################################################
PUB_KEY = ""
PRIV_KEY = ""


#########################################################################################
# RPC - https://api.mainnet-beta.solana.com & WSS: 
#########################################################################################
RPC = ""
solana_wss = ""


#########################################################################################
# Configuracion extra
#########################################################################################
WRAPPED_SOL_MINT = "So11111111111111111111111111111111111111112"
Pool_raydium = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
Pool_jupiter = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
raydium_V4 = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
lamports_per_sol = 1_000_000_000  # 1 SOL = 1,000,000,000 lamports
solana_client = Client(RPC)
async_client = AsyncClient(RPC)
payer_keypair = Keypair.from_base58_string(PRIV_KEY)