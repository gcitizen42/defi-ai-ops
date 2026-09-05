// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title Vault - the sealed pool.
/// It only grows: Fork mints and Lineage increments flow in. It is locked by a hash;
/// the secret is held off-chain by the steward, so nothing on-chain names its future.
/// One day the steward decides where "Lost" becomes "Found" - or builds something
/// permissionless on top of it. Until then, it simply accumulates in plain sight.
contract Vault {
    bytes32 public immutable SEAL; // keccak256(secret), the secret kept off-chain
    bool public found;

    event Funded(address indexed from, uint256 amount);
    event Found(address indexed to, uint256 amount);

    constructor(bytes32 seal_) {
        SEAL = seal_;
    }

    receive() external payable {
        emit Funded(msg.sender, msg.value);
    }

    function state() external view returns (string memory) {
        return found ? "Found" : "Lost";
    }

    /// the on-chain readme. a subtle nudge, never an address: whoever wants the rest
    /// follows the hands that fill it.
    function rules() external pure returns (string memory) {
        return "Lost. a pool that only grows, sealed by a hash: its preimage opens it once, to a destination chosen that day. one of a set. read the hands that fill it.";
    }

    function balance() external view returns (uint256) {
        return address(this).balance;
    }

    /// whoever holds the secret decides, once, where the pool goes.
    function unlock(bytes calldata secret, address payable to) external {
        require(!found, "found");
        require(keccak256(secret) == SEAL, "wrong key");
        found = true;
        uint256 bal = address(this).balance;
        (bool ok,) = to.call{value: bal}("");
        require(ok, "send");
        emit Found(to, bal);
    }
}
