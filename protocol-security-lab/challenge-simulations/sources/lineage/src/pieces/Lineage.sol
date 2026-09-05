// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Lineage - the price is its own history.
/// To add your name you pay generation x 0.01 ETH. The former holder is refunded
/// exactly what they paid (break-even); the increment funds the Vault; the contract
/// engraves every owner and price. Nobody profits from holding it; the more storied
/// it is, the more it costs to join.
contract Lineage is Collectible {
    address public immutable vault;
    uint256 public constant BASE = 0.01 ether;

    struct Step { address owner; uint256 price; uint64 blockNo; }
    Step[] public trail;
    uint256 public paid; // what the current holder paid, for the refund

    constructor(address steward_, IArt art_, address vault_) Collectible("Lineage", "LNG", steward_, art_) {
        vault = vault_;
        _mint(steward_, 1);
        trail.push(Step(steward_, 0, uint64(block.number)));
    }

    function generation() public view returns (uint256) { return trail.length; }
    function price() public view returns (uint256) { return trail.length * BASE; }

    function buy() external payable {
        uint256 p = price();
        require(msg.value >= p, "underpaid");
        address holder = ownerOf(1);
        uint256 refund = paid;
        paid = p;
        trail.push(Step(msg.sender, p, uint64(block.number)));
        _sold(p);
        _move(holder, msg.sender, 1);
        if (refund > 0) _pay(holder, refund); // seller breaks even
        _pay(vault, p - refund); // the increment funds the Vault
        if (msg.value > p) _pay(msg.sender, msg.value - p);
    }

    function defaultRender(uint256) public view override returns (string memory) {
        string memory g = string(abi.encodePacked("held ", Meta.str(trail.length), "x"));
        return Meta.uri("Lineage", "history has a weight",
            Meta.plate(g, "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Lineage. price = generation x 0.01 ETH. the seller is refunded their cost; the increment funds the Vault; every owner is engraved.";
    }
}
