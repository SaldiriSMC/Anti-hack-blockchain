import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from solcx import compile_source, install_solc

# Private key (directly included in the code)
PRIVATE_KEY = '0x4ef8433a2a51773f5fc2069c90328ab3f86f6960eab650efbaf5db7310f20076'  # Replace with your actual private key

# Connect to zkSync's Sepolia testnet
zkSync_sepolia_testnet_url = "https://sepolia.era.zksync.dev"
chain_id = 300

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(zkSync_sepolia_testnet_url))

# Add Geth POA middleware
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Check connection
if not w3.is_connected():
    raise Exception("Web3 is not connected")

print("Web3 is connected")

# Solidity source code
contract_source_code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ZeekMessages {
    struct Message {
        string content;
        uint256 timestamp;
        uint8 approvals;
        bool acknowledged;
    }

    address public owner;
    uint256 public delay;
    uint256 public messageNonce;

    mapping(uint256 => Message) public messages;
    mapping(uint256 => mapping(address => bool)) public approvals;

    address[] public signers;
    uint8 public requiredApprovals;

    // Event to acknowledge a new message
    event MessageReceived(uint256 indexed nonce, string content, uint256 timestamp);
    event MessageApproved(uint256 indexed nonce, address indexed approver);
    event MessageAcknowledged(uint256 indexed nonce, address indexed executor);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    modifier onlySigner() {
        require(isSigner(msg.sender), "Not a signer");
        _;
    }

    constructor(address[] memory _signers, uint8 _requiredApprovals, uint256 _delay) {
        owner = msg.sender;
        signers = _signers;
        requiredApprovals = _requiredApprovals;
        delay = _delay;
        emit MessageReceived(messageNonce, "Zeek welcomes you to ZKsync!", block.timestamp + delay);
    }

    function isSigner(address _address) public view returns (bool) {
        for (uint256 i = 0; i < signers.length; i++) {
            if (signers[i] == _address) {
                return true;
            }
        }
        return false;
    }

    function sendMessage(string memory _message) public onlySigner {
        messageNonce++;
        uint256 timestamp = block.timestamp + (delay + uint256(keccak256(abi.encodePacked(block.timestamp, block.difficulty))) % delay);
        
        messages[messageNonce] = Message({
            content: _message,
            timestamp: timestamp,
            approvals: 0,
            acknowledged: false
        });

        emit MessageReceived(messageNonce, _message, timestamp);
    }

    function approveMessage(uint256 _nonce) public onlySigner {
        require(messages[_nonce].timestamp != 0, "Message does not exist");
        require(!messages[_nonce].acknowledged, "Message already acknowledged");
        require(!approvals[_nonce][msg.sender], "Already approved");

        approvals[_nonce][msg.sender] = true;
        messages[_nonce].approvals++;

        emit MessageApproved(_nonce, msg.sender);
    }

    function acknowledgeMessage(uint256 _nonce) public onlySigner {
        require(messages[_nonce].timestamp != 0, "Message does not exist");
        require(messages[_nonce].approvals >= requiredApprovals, "Not enough approvals");
        require(block.timestamp >= messages[_nonce].timestamp, "Message is still in delay period");
        require(!messages[_nonce].acknowledged, "Message already acknowledged");

        messages[_nonce].acknowledged = true;

        emit MessageAcknowledged(_nonce, msg.sender);
    }

    // Function to count the total messages sent to Zeek
    function getTotalMessages() public view returns (uint256) {
        return messageNonce;
    }

    // Function to return the last message sent to Zeek
    function getLastMessage() public view returns (string memory) {
        require(messageNonce > 0, "No messages sent to Zeek yet!");
        return messages[messageNonce].content;
    }
}
'''

# Install solc
install_solc('0.8.0')

# Compile the contract
compiled_sol = compile_source(contract_source_code, solc_version='0.8.0')
contract_id, contract_interface = compiled_sol.popitem()

# Extract ABI and Bytecode
contract_abi = contract_interface['abi']
contract_bytecode = contract_interface['bin']

# Get account from private key
account = Account.from_key(PRIVATE_KEY)
w3.eth.default_account = account.address

# Define the contract
TransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

# Set up the constructor parameters
signers = ["0x5f8267F0AF048B478D4ad17423A4C8a098f87C40"]  # Add your actual signer addresses
required_approvals = 1
delay = 3600  # delay in seconds (e.g., 3600 seconds = 1 hour)

# Deploy the contract with error handling
def deploy_contract():
    try:
        # Build the transaction
        constructor = TransactionContract.constructor(signers, required_approvals, delay)
        transaction = constructor.transact({
            'from': account.address,
            'gas': 3000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': chain_id
        })

        # Debugging: Print the constructed transaction
        print(f"Constructed transaction: {transaction}")

        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)

        # Debugging: Print the signed transaction
        print(f"Signed transaction: {signed_txn}")

        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Debugging: Print the transaction hash
        print(f"Transaction hash: {tx_hash.hex()}")

        # Wait for the transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return tx_receipt
    except Exception as e:
        print(f"An error occurred during contract deployment: {e}")
        return None

if __name__ == "__main__":
    receipt = deploy_contract()
    if receipt:
        print(f"Contract deployed at address: {receipt.contractAddress}")
    else:
        print("Contract deployment failed.")
