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
    mapping(address => uint256) public lastApprovalTime; // Rate limiting

    address[] public signers;
    uint8 public requiredApprovals;

    // Event to acknowledge a new message
    event MessageReceived(uint256 indexed nonce, string content, uint256 timestamp);
    event MessageApproved(uint256 indexed nonce, address indexed approver);
    event MessageAcknowledged(uint256 indexed nonce, address indexed executor);
    event SignerAdded(address indexed newSigner);
    event SignerRemoved(address indexed removedSigner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    modifier onlySigner() {
        require(isSigner(msg.sender), "Not a signer");
        _;
    }

    modifier rateLimited() {
        require(block.timestamp >= lastApprovalTime[msg.sender] + delay, "Approval rate limited");
        _;
    }

    constructor(uint8 _requiredApprovals, uint256 _delay) {
        owner = msg.sender;
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
        uint256 timestamp = block.timestamp + (delay + uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao))) % delay);
        
        messages[messageNonce] = Message({
            content: _message,
            timestamp: timestamp,
            approvals: 0,
            acknowledged: false
        });

        emit MessageReceived(messageNonce, _message, timestamp);
    }

    function approveMessage(uint256 _nonce) public onlySigner rateLimited {
        require(messages[_nonce].timestamp != 0, "Message does not exist");
        require(!messages[_nonce].acknowledged, "Message already acknowledged");
        require(!approvals[_nonce][msg.sender], "Already approved");
        require(block.timestamp >= messages[_nonce].timestamp, "Approval period not started");

        approvals[_nonce][msg.sender] = true;
        messages[_nonce].approvals++;
        lastApprovalTime[msg.sender] = block.timestamp; // Update last approval time

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

    function addSigner(address _newSigner) public onlyOwner {
        require(_newSigner != address(0), "Invalid address");
        require(!isSigner(_newSigner), "Already a signer");
        signers.push(_newSigner);
        emit SignerAdded(_newSigner);
    }

    function removeSigner(address _signer) public onlyOwner {
        require(isSigner(_signer), "Not a signer");
        for (uint256 i = 0; i < signers.length; i++) {
            if (signers[i] == _signer) {
                signers[i] = signers[signers.length - 1];
                signers.pop();
                emit SignerRemoved(_signer);
                break;
            }
        }
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
