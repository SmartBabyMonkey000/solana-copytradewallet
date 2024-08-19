import asyncio
import concurrent.futures
import queue
import datetime
import json
import os
import sys
from threading import Thread, Event
import threading
import time
import websockets

from already_bought import storeToken, soldToken

from solders import message
from solders.pubkey import Pubkey
from solders.signature import Signature

from data.config import solana_wss, solana_client, copy_wallet_address, WRAPPED_SOL_MINT, Pool_raydium, Pool_jupiter, raydium_V4

from jupiter.jupiter_functions import buy_token_jupiter, open_limit_order, get_token_balance

event_thread = Event()

# Constants and Structures
seen_signatures = set()

def getTimestamp():
    return "[" + datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] + "]"

#########################################################################################
# Enviamos peticion de compra
#########################################################################################
async def start_token_buy(token_mint):
    tmpCompro = await buy_token_jupiter(token_mint)
    if tmpCompro:
        tmpTokensComprados = await get_balance(token_mint)
        print(tmpTokensComprados)
        await open_limit_order(token_mint, tmpTokensComprados)

#########################################################################################
# Vemos la cantidad de tokens
#########################################################################################
async def get_balance(tmpToken):
    while True:
        tmpTokensComprados = 0
        tmpTokensComprados = await get_token_balance(tmpToken)
        if tmpTokensComprados is not None and int(tmpTokensComprados) > 0:
            break
        print("Balance is 0, trying again in 2 seconds...")
        await asyncio.sleep(2)

    tmpTokensLamports = str(tmpTokensComprados).replace(".", "")
    return tmpTokensLamports

#########################################################################################
# Procesar transacciones
#########################################################################################
class TransactionProcessor:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def process_transactions(self):
        while True:
            signature = await self.queue.get()
            try:
                xsignature = Signature.from_string(signature)
                transaction = solana_client.get_transaction(xsignature, encoding="jsonParsed", max_supported_transaction_version=0).value
                #print(transaction)

                if transaction is None:
                    print(f"{getTimestamp()} -No se encontro la transaccion: {signature}")
                    continue

                instruction_list = transaction.transaction.meta.inner_instructions
                pre_token_balances = transaction.transaction.meta.pre_token_balances
                post_token_balances = transaction.transaction.meta.post_token_balances
                programmidswap = transaction.transaction.transaction.message.instructions
                account_signer = transaction.transaction.transaction.message.account_keys[0].pubkey

                #print(programmidswap)

                if account_signer == Pubkey.from_string(copy_wallet_address):
                    print(f"{getTimestamp()} -Nueva actualizacion recibida: , https://solscan.io/tx/{signature}")

                    for compareprogramm in programmidswap:
                        
                        if compareprogramm.program_id == Pubkey.from_string(Pool_raydium):
                            print("Encontre raydium")

                            if pre_token_balances[0].ui_token_amount.amount < post_token_balances[0].ui_token_amount.amount:
                                print(f"Es una compra")

                                if WRAPPED_SOL_MINT == str(pre_token_balances[0].mint):

                                    token_mint = str(pre_token_balances[1].mint)
                                else:
                                    token_mint = str(pre_token_balances[0].mint)

                                print (token_mint)
                                await start_token_buy(token_mint)

                                #fee_gas = (transaction.transaction.meta.fee) / 1000000000
                                #print (fee_gas)
                                

                            elif pre_token_balances[0].ui_token_amount.amount > post_token_balances[0].ui_token_amount.amount:
                                print(f"Es una venta")

                                if WRAPPED_SOL_MINT == str(pre_token_balances[0].mint):
                                    token_mint = str(pre_token_balances[1].mint)
                                else:
                                    token_mint = str(pre_token_balances[0].mint)

                                #fee_gas = (transaction.transaction.meta.fee) / 1000000000
                                #print (fee_gas)
                                #print (token_mint)

                            else:
                                print("No puedo identificar compra o venta")

                        if compareprogramm.program_id == Pubkey.from_string(Pool_jupiter):
                            print("Encontre jupiter")

                            if pre_token_balances[0].ui_token_amount.amount < post_token_balances[0].ui_token_amount.amount:
                                print(f"Es una compra")

                                if WRAPPED_SOL_MINT == str(pre_token_balances[0].mint):
                                    token_mint = str(pre_token_balances[1].mint)
                                else:
                                    token_mint = str(pre_token_balances[0].mint)
                                #fee_gas = (transaction.transaction.meta.fee) / 1000000000
                                #print (fee_gas)
                                print(token_mint)

                                await start_token_buy(token_mint)

                            elif pre_token_balances[0].ui_token_amount.amount > post_token_balances[0].ui_token_amount.amount:
                                print(f"Es una venta")

                                if WRAPPED_SOL_MINT == str(pre_token_balances[0].mint):
                                    token_mint = str(pre_token_balances[1].mint)
                                else:
                                    token_mint = str(pre_token_balances[0].mint)

                                #fee_gas = (transaction.transaction.meta.fee) / 1000000000
                                #print (fee_gas)
                                #print (token_mint)

                            else:
                                print("No puedo identificar compra o venta")

            #except Exception as e:
            #    print(f"{getTimestamp()} - Error - Procesando transaccion: {signature}: {e}")
            finally:
                print("Finalizado")

    async def enqueue_transaction(self, signature):
            await self.queue.put(signature)

#########################################################################################
# Inicio copy trade
#########################################################################################
async def run():
    # Procesos de transacciones
    processor = TransactionProcessor()
    asyncio.create_task(processor.process_transactions())

    async def connect_and_listen():
        while True:
            try:
                async with websockets.connect(solana_wss) as websocket:
                    # Send subscription request
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "logsSubscribe",
                        "params": [
                            {"mentions": [copy_wallet_address]},
                            {"commitment": "finalized"}
                        ]
                    }))

                    # Receive the first response and verify subscription success
                    first_resp = await websocket.recv()
                    print(first_resp)
                    response_dict = json.loads(first_resp)
                    if 'result' in response_dict:
                        print("Subscription successful. Subscription ID: ", response_dict['result'])

                        # Continuously read from the WebSocket
                        async for response in websocket:
                            response_dict = json.loads(response)
                            if response_dict['params']['result']['value']['err'] is None:
                                signature = response_dict['params']['result']['value']['signature']
                                if signature not in seen_signatures:
                                    seen_signatures.add(signature)
                                    await processor.enqueue_transaction(signature)
            except websockets.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}. Reconnecting...")
            except Exception as e:
                print(f"An error occurred: {e}. Reconnecting...")

            # Wait before reconnecting to avoid rapid reconnection attempts
            await asyncio.sleep(5)

    await connect_and_listen()

asyncio.run(run())