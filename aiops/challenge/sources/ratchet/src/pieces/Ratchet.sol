// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Ratchet - the price only ever rises.
/// To take it, pay more than the last price. The seller keeps the gain. No fee.
contract Ratchet is Collectible {
    uint256 public last; // last price paid; the next buyer must exceed it

    constructor(address steward_, IArt art_, uint256 start) Collectible("Ratchet", "RTCH", steward_, art_) {
        last = start;
        _mint(steward_, 1);
    }

    function buy() external payable {
        require(msg.value > last, "must exceed");
        address holder = ownerOf(1);
        last = msg.value;
        _sold(msg.value);
        _move(holder, msg.sender, 1);
        _pay(holder, msg.value); // conviction rewarded: the seller keeps the gain
    }

    function defaultRender(uint256) public pure override returns (string memory) {
        return Meta.uri("Ratchet", "never anything but up",
            Meta.plate("Ratchet", "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Ratchet. the price only rises. to take it, pay more than the last; the seller keeps the gain.";
    }
}
