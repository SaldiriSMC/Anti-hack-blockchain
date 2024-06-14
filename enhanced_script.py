import json
import time
import random
from web3 import Web3
from solcx import compile_source, install_solc

# Install Solidity compiler version
install_solc('0.8.0')

# Connect to zkSync provider
w3 = Web3(Web3.HTTPProvider('https://zksync2-testnet.zksync.dev'))

# Read private key from environment variable or secure source
private_key = 'YOUR_PRIVATE_KEY'

# Read and compile Solidity contract
with open('TransactionContract.sol', 'r') as file:
    contract_source_code = file.read()

compiled_sol = compile_source(contract_source_code, solc_version='0.8.0')
contract_id, contract_interface = compiled_sol.popitem()

# Extract bytecode and ABI
bytecode = contract_interface['evm']['bytecode']['object']
abi = contract_interface['abi']

# Create contract object
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Create an account from the private key
account = w3.eth.account.from_key(private_key)

# Get the latest transaction count (nonce)
nonce = w3.eth.getTransactionCount(account.address)

# Build the transaction
transaction = Contract.constructor().buildTransaction({
    'chainId': 280,  # zkSync testnet chain ID
    'gas': 2000000,
    'gasPrice': w3.toWei('10', 'gwei'),
    'nonce': nonce,
})

# Introduce a randomized delay before signing the transaction
time.sleep(random.uniform(1, 5))

# Sign the transaction
signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

# Introduce another randomized delay before sending the transaction
time.sleep(random.uniform(1, 5))

# Send the transaction
tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

# Wait for the transaction receipt
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

print(f'Contract deployed at address: {tx_receipt.contractAddress}')
