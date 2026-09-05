// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Fork - an edition that keeps detaching.
/// Each purchase mints one new numbered edition; the price rises x1.1 each time and
/// funds the Vault. It never pays earlier holders - no pump. Fork is also the
/// collection's membership: one endorsement weight per edition in Art's governance.
contract Fork is Collectible {
    address public immutable vault;
    uint256 public price; // next mint price
    uint256 public minted; // editions so far

    constructor(address steward_, IArt art_, address vault_, uint256 start) Collectible("Fork", "FORK", steward_, art_) {
        vault = vault_;
        price = start;
    }

    function mint() external payable returns (uint256 id) {
        uint256 p = price;
        require(msg.value >= p, "underpaid");
        id = ++minted;
        _mint(msg.sender, id);
        price = p * 11 / 10; // x1.1
        _sold(p);
        _pay(vault, p);
        if (msg.value > p) _pay(msg.sender, msg.value - p);
    }

    function totalSupply() external view returns (uint256) { return minted; }

    function defaultRender(uint256 id) public pure override returns (string memory) {
        string memory no = string(abi.encodePacked("No. ", Meta.str(id)));
        return Meta.uri(string(abi.encodePacked("Fork ", no)),
            "an edition that keeps detaching", Meta.plate(no, "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Fork. each purchase mints one new numbered edition; price rises x1.1 to the Vault. holding Fork is a vote on the collection's face.";
    }
}
