// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Ask - the price is the tableau.
/// The holder sets a number in [0.01, 999] ETH; anyone buys at it and writes the
/// next number. The piece's own face is that number.
contract Ask is Collectible {
    uint256 public constant MIN = 0.01 ether;
    uint256 public constant MAX = 999 ether;
    uint256 public price;

    constructor(address steward_, IArt art_, uint256 startPrice) Collectible("Ask", "ASK", steward_, art_) {
        require(startPrice >= MIN && startPrice <= MAX, "bounds");
        price = startPrice;
        _mint(steward_, 1);
    }

    function setPrice(uint256 p) external {
        require(msg.sender == ownerOf(1), "not holder");
        require(p >= MIN && p <= MAX, "bounds");
        price = p;
    }

    function buy(uint256 newPrice) external payable {
        uint256 p = price;
        require(msg.value >= p, "underpaid");
        require(newPrice >= MIN && newPrice <= MAX, "bounds");
        address holder = ownerOf(1);
        price = newPrice;
        _sold(p);
        _move(holder, msg.sender, 1);
        _pay(holder, p);
        if (msg.value > p) _pay(msg.sender, msg.value - p);
    }

    function defaultRender(uint256) public view override returns (string memory) {
        return Meta.uri("Ask", "the price is the tableau",
            Meta.plate(Meta.eth(price, 2), "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Ask. the holder sets a price in [0.01, 999] ETH; anyone buys at it and sets the next. the number is the work.";
    }
}
