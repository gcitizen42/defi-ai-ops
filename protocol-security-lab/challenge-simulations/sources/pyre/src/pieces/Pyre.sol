// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Pyre - the same ratchet, but the seller only ever breaks even.
/// You pay more than the holder paid; they get their money back; the premium burns.
/// You can never profit from holding it - only pay to hold it, and recoup your cost.
contract Pyre is Collectible {
    address payable public constant ASH = payable(0x000000000000000000000000000000000000dEaD);
    uint256 public cost; // what the current holder paid

    constructor(address steward_, IArt art_, uint256 start) Collectible("Pyre", "PYRE", steward_, art_) {
        cost = start;
        _mint(steward_, 1);
    }

    function buy() external payable {
        uint256 c = cost;
        require(msg.value > c, "must exceed");
        address holder = ownerOf(1);
        cost = msg.value;
        _sold(msg.value);
        _move(holder, msg.sender, 1);
        _pay(holder, c); // break-even
        _pay(ASH, msg.value - c); // the premium burns
    }

    function defaultRender(uint256) public pure override returns (string memory) {
        return Meta.uri("Pyre", "the premium burns",
            Meta.plate("Pyre", "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Pyre. to take it, pay more than the holder paid. they break even; the surplus is burned. holding never profits.";
    }
}
