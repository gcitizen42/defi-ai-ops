// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "./base/Collectible.sol";
import {Meta} from "./lib/Meta.sol";

/// @title Verb - the index of the ten.
/// It holds the ring of every piece, so finding one leads to them all. Anyone may
/// echo() once a day to keep the collection warm in the scanners and leave their mark
/// as a witness - the collection's lightest, freest heartbeat.
contract Verb is Collectible {
    address[] public pieces;
    uint256 public constant ECHO_EVERY = 1 days;
    uint256 public lastEcho;
    address[] public witnesses;

    event Heartbeat(address indexed witness);

    constructor(address steward_, IArt art_, address[] memory pieces_) Collectible("Verb", "VERB", steward_, art_) {
        pieces = pieces_;
        _mint(steward_, 1);
    }

    function allPieces() external view returns (address[] memory) {
        return pieces;
    }

    function echo() external {
        require(block.timestamp >= lastEcho + ECHO_EVERY, "too soon");
        lastEcho = block.timestamp;
        witnesses.push(msg.sender);
        emit Heartbeat(msg.sender);
    }

    function witnessCount() external view returns (uint256) {
        return witnesses.length;
    }

    function defaultRender(uint256) public pure override returns (string memory) {
        return Meta.uri("Verb", "the map of the ten",
            Meta.plate("Verb", "#171512", "#f2ede2"));
    }

    function rules() external pure override returns (string memory) {
        return "Verb. the index of the ten: find one and you find them all. anyone may echo() once a day to keep it warm and be recorded as a witness.";
    }
}
