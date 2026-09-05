// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Bequeath - it cannot be bought, only given.
/// There is no price and no buy. The holder may only bequeath() it to someone else.
/// A gift you cannot hoard: if it is not passed on for six months, anyone may claim it.
contract Bequeath is Collectible {
    uint256 public constant WINDOW = 182 days;
    uint256 public lastMove;
    uint256 public generation;

    constructor(address steward_, IArt art_) Collectible("Bequeath", "BQTH", steward_, art_) {
        _mint(steward_, 1);
        lastMove = block.timestamp;
    }

    /// block ordinary transfers - the only way through is bequeath() / claim()
    function _beforeTransfer(address, address, uint256) internal pure override {
        revert("gift only");
    }

    function bequeath(address to) external {
        require(msg.sender == ownerOf(1), "not holder");
        require(to != address(0) && to != msg.sender, "bad recipient");
        _move(msg.sender, to, 1);
        lastMove = block.timestamp;
        generation++;
    }

    function claim() external {
        require(block.timestamp > lastMove + WINDOW, "still circulating");
        _move(ownerOf(1), msg.sender, 1);
        lastMove = block.timestamp;
        generation++;
    }

    function defaultRender(uint256) public view override returns (string memory) {
        string memory g = string(abi.encodePacked("given ", Meta.str(generation), "x"));
        return Meta.uri("Bequeath", "it is not sold, only given",
            Meta.plate(g, "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Bequeath. no price, no buy. the holder may only give it. unmoved for six months, anyone may claim it.";
    }
}
