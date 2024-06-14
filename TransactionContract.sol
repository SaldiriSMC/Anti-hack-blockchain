// Save the file as TransactionContract.sol

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransactionContract {
    address public owner;

    event TransactionMade(address indexed from, uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    function makeTransaction() public payable {
        require(msg.value > 0, "Must send some ether");
        emit TransactionMade(msg.sender, msg.value);
    }
}
