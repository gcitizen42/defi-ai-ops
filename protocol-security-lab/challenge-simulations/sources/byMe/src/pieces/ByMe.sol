// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title By Me - the price is a countdown.
/// A ten-year descending auction from 1,000,000 ETH to a 0.01 ETH floor. Nobody owns
/// it until someone buys and stops the clock; then it is an ordinary, transferable
/// work. Because it starts unaffordable, it is also the collection's natural gate
/// against the creator assembling the set at launch. The sale is the steward's income.
contract ByMe is Collectible {
    uint256 public constant P0 = 1_000_000 ether;
    uint256 public constant FLOOR = 0.01 ether;
    uint256 public constant HALFLIFE = 11_866_678; // ~137d: 1e6 -> 0.01 over ten years
    uint256 public immutable start;
    bool public sold;

    constructor(address steward_, IArt art_) Collectible("By Me", "BYME", steward_, art_) {
        start = block.timestamp;
    }

    function price() public view returns (uint256) {
        if (sold) return 0;
        uint256 t = block.timestamp - start;
        uint256 full = t / HALFLIFE;
        if (full >= 27) return FLOOR;
        uint256 p = P0 >> full;
        uint256 nxt = p >> 1;
        p -= (p - nxt) * (t % HALFLIFE) / HALFLIFE; // linear between halvings
        return p < FLOOR ? FLOOR : p;
    }

    function buy() external payable {
        require(!sold, "sold");
        uint256 p = price();
        require(msg.value >= p, "underpaid");
        sold = true;
        _mint(msg.sender, 1);
        _sold(p);
        _pay(steward, p);
        if (msg.value > p) _pay(msg.sender, msg.value - p);
    }

    function defaultRender(uint256) public pure override returns (string memory) {
        return Meta.uri("By Me", "buy me / by me / bye me",
            Meta.plate("By Me", "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "By Me. a ten-year descending auction, 1,000,000 to 0.01 ETH. whoever buys stops the clock; then it is an ordinary work. the sale is the steward's.";
    }
}
