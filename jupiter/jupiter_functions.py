import asyncio
import base64
import json
import datetime
import requests

from solders import message
from solders.transaction import VersionedTransaction
from solders.signature import Signature

from solana.rpc.types import TxOpts
from solana.rpc.commitment import Processed

from data.config import async_client, payer_keypair, lamports_per_sol, profit_percent, FeeLamports, amount_buy_sol, slippage_bps, PUB_KEY, RPC

from jupiter.jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA

def getTimestamp():
    return "[" + datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] + "]"

#########################################################################################
# Compramos Token en Jupiter
#########################################################################################
async def buy_token_jupiter(tokenmint):
    try:
        amount_lamports = int(amount_buy_sol * lamports_per_sol)
        amount_lamports_prioritization = int(FeeLamports * lamports_per_sol)

        jupiter = Jupiter(
            async_client=async_client,
            keypair=payer_keypair,
            quote_api_url="https://quote-api.jup.ag/v6/quote?",
            swap_api_url="https://quote-api.jup.ag/v6/swap"
        )

        transaction_data = await jupiter.swap(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint=tokenmint,
            amount=amount_lamports,
            slippage_bps=int(slippage_bps),
            prioritization_fee_lamports=int(amount_lamports_prioritization),
        )

        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
        signature = payer_keypair.sign_message(message.to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        result = await async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        transaction_id = json.loads(result.to_json())['result']
        print(f"{getTimestamp()} - Transaccion Enviada: https://explorer.solana.com/tx/{transaction_id}")
        
        #await confirm_txn("2oHoZKq3KBWqk5WCWEUdxXS3iFLtjqg7sSygqmaKVbQcTJgTxUmt6T9GpSjV8M3TmJiur5s7hyESa51H4uLzPybG")
        tmpBuyConfirmed = await check_transaction_status(transaction_id)
        if tmpBuyConfirmed:

            return True
        else:
            return False
    except Exception as e:
        print(f"{getTimestamp()} - Error - Procesar transaccion: {signature}: {e}")

#########################################################################################
# Verificamos que la transaccion se confirma
#########################################################################################
async def check_transaction_status(tx_signature_str, max_tries=20, delay=2):
    for attempt in range(max_tries):
        try:
            tx_signature = Signature.from_string(tx_signature_str)
            response = await async_client.get_signature_statuses([tx_signature])
            status_list = response.value
            status = status_list[0]

            if status is not None:
                confirmation_status = status.confirmation_status
                if str(confirmation_status) == str("TransactionConfirmationStatus.Finalized"):
                    return True
                elif str(confirmation_status) == str("TransactionConfirmationStatus.Confirmed"):
                    return True
        except Exception as e:
            print(f"{getTimestamp()} - Error - Check Transaccion: {e} (Intento {attempt + 1})")

        await asyncio.sleep(delay)
    return False

#########################################################################################
# Verificamos que la transaccion open limit se confirma
#########################################################################################
async def check_limit_transaction_status(tx_signature_str, tokenmint, amount_tokens, max_tries=20, delay=2):
    for attempt in range(max_tries):
        try:
            tx_signature = Signature.from_string(tx_signature_str)
            response = await async_client.get_signature_statuses([tx_signature])
            status_list = response.value
            status = status_list[0]

            if status is not None:
                confirmation_status = status.confirmation_status
                if str(confirmation_status) == str("TransactionConfirmationStatus.Finalized"):
                    print("Orden limite finalizada")
                    return True
                elif str(confirmation_status) == str("TransactionConfirmationStatus.Confirmed"):
                    print("Orden limite confirmada")
                    return True
        except Exception as e:
            print(f"{getTimestamp()} - Error - Check Transaccion: {e} (Intento {attempt + 1})")

        await asyncio.sleep(delay)
    #Si no entra la orden la volvemos a enviar
    await open_limit_order(tokenmint, amount_tokens)
    return False

#########################################################################################
# Ponemos orden de venta en Jupiter
#########################################################################################
async def open_limit_order(tokenmint, amount_tokens: int):
    try:
        amount_lamports = int(amount_buy_sol * lamports_per_sol)
        total_profit = amount_lamports * (profit_percent / 100)
        amount_lamports_profit = amount_lamports + total_profit
        
        jupiter = Jupiter(
            async_client=async_client,
            keypair=payer_keypair,
            open_order_api_url="https://jup.ag/api/limit/v1/createOrder"
        )
        
        transaction_data = await jupiter.open_order(
            input_mint=tokenmint,
            output_mint="So11111111111111111111111111111111111111112",
            in_amount=amount_tokens,
            out_amount=amount_lamports_profit,
        )
        # Returns dict: {'transaction_data': serialized transactions to create the limit order, 'signature2': signature of the account that will be opened}

        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data['transaction_data']))
        signature = payer_keypair.sign_message(message.to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature, transaction_data['signature2']])
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        result = await async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        transaction_id = json.loads(result.to_json())['result']
        print(f"{getTimestamp()} - Open Order Limit Enviada: https://explorer.solana.com/tx/{transaction_id}")

        await check_limit_transaction_status(transaction_id, tokenmint, amount_tokens)

    except Exception as e:
        print(f"{getTimestamp()}  - Error - Open Order Limit: {transaction_id}")


#########################################################################################
# Vemos precio del token en USD
#########################################################################################
async def get_mint_price(input_mint, output_mint: str=None):
    tmpTokenPrice = await Jupiter.get_token_price(input_mint)
    print(tmpTokenPrice)
    return False

#########################################################################################
# Vemos los tokens que tengo en mi cuenta
#########################################################################################
async def get_token_balance(token_address: str) -> float:
    try:

        headers = {"accept": "application/json", "content-type": "application/json"}

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "getTokenAccountsByOwner",
            "params": [
                PUB_KEY,
                {"mint": token_address},
                {"encoding": "jsonParsed"},
            ],
        }
        
        response = requests.post(RPC, json=payload, headers=headers)
        ui_amount = await find_data(response.json(), "uiAmount")
        return float(ui_amount)
    except:
        print(f"{getTimestamp()} - Error - Get Balance Token: {token_address}")
        return None
    
async def find_data(data: dict, field: str) -> str:
    if isinstance(data, dict):
        if field in data:
            return data[field]
        else:
            for value in data.values():
                result = await find_data(value, field)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = await find_data(item, field)
            if result is not None:
                return result
    return None