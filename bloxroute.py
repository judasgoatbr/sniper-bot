import asyncio
import websockets
import json
from solders import keypair as kp
from solders import pubkey as pk
from solders import transaction as tx
from solders import instruction as ins
from solders import system_program as sp
import base64

# Constants and authentication
RPC_ENDPOINT = "wss://ny.solana.dex.blxrbdn.com/api/v2/rate-limit"  # WebSocket endpoint
AUTHORIZATION_HEADER = "ZjEwM2ExYmEtNDcwMi00YmY4LThhZTMtMmNmMGE3MjUwMTAyOjQyMmFkMDU4NjgyMzcyZjc5OTcyM2QwZWY4MDFkYzgz"

# Replace with your keypair
payer = kp.Keypair.from_base58_string('56fSd6SEJxmPS7P9GDCxUi84sH8DyoqmRBgAWnus2utxd5rbWR1QcKc1vCpApZBc9tovSiU1UbcpH2JbpGjJ89Rf')
payer_public_key = payer.pubkey()

# Replace with the recipient's public key
recipient_public_key = pk.Pubkey.from_string('DNvKnjcewdwwD3vsJSKCF2dZzYKmkW9BBwNM1gUDpump')

# Fetch recent blockhash
async def fetch_recent_blockhash():
    async with websockets.connect(RPC_ENDPOINT, extra_headers={"Authorization": f"Bearer {AUTHORIZATION_HEADER}"}) as websocket:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getRecentBlockhash"
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        data = json.loads(response)
        if 'result' in data and 'value' in data['result']:
            return data['result']['value']['blockhash']
        else:
            raise ValueError(f"Unexpected response format: {data}")

# Create the transaction
async def create_transaction():
    recent_blockhash = await fetch_recent_blockhash()
    if recent_blockhash is None:
        raise ValueError("Failed to fetch recent blockhash.")

    # Create the transaction message
    message = tx.Message(
        recent_blockhash=recent_blockhash,
        instructions=[
            sp.transfer(
                sender=payer_public_key,
                receiver=recipient_public_key,
                lamports=int(0.01 * 10**9)  # Convert SOL to lamports
            ),
            # Optional Compute Unit Limit
            ins.Instruction(
                program_id=pk.Pubkey.from_string('ComputeBudget111111111111111111111111111111'),
                accounts=[],
                data=bytes([0]) + (1000000).to_bytes(8, byteorder='little')
            ),
            # Optional Priority Fee
            ins.Instruction(
                program_id=pk.Pubkey.from_string('ComputeBudget111111111111111111111111111111'),
                accounts=[],
                data=bytes([1]) + (5000).to_bytes(8, byteorder='little')
            )
        ]
    )

    # Initialize the transaction with the message
    transaction = tx.Transaction(
        from_keypairs=[payer],  # Provide the payer keypair
        message=message
    )

    # Sign and serialize the transaction
    transaction.sign()
    serialized_transaction = base64.b64encode(transaction.serialize()).decode('utf-8')
    return serialized_transaction

# Function to submit the transaction
async def submit_transaction(serialized_tx):
    async with websockets.connect(RPC_ENDPOINT, extra_headers={"Authorization": f"Bearer {AUTHORIZATION_HEADER}"}) as websocket:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [serialized_tx]
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        print("Response:", response)

# Main function to create and submit the transaction
async def main():
    serialized_transaction = await create_transaction()
    await submit_transaction(serialized_transaction)

# Run the main function
asyncio.run(main())
