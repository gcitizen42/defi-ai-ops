// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Proof of Life. The heart of the collection.
/// Anyone may seize it with a deliberately heavy beat() (about 0.001 ETH) whose cost
/// is not wasted: it pulses life through all ten pieces (a heartbeat, and dust into
/// each piece's non-withdrawable life-fund). Nothing to defend, so no bot can hold it
/// forever; it records who held it longest.
contract ProofOfLife is Collectible {
    uint256 public constant COST = 0.001 ether;
    uint256 public heldSince;
    uint256 public record; // longest tenure, seconds
    address public recordHolder;

    event Heartbeat(address indexed by, uint256 value);

    constructor(address steward_, IArt art_) Collectible("Proof of Life", "LIFE", steward_, art_) {
        _mint(steward_, 1);
        heldSince = block.timestamp;
    }

    function beat() external payable {
        require(msg.value >= COST, "heartbeat cost");
        address prev = ownerOf(1);
        uint256 tenure = block.timestamp - heldSince;
        if (tenure > record) { record = tenure; recordHolder = prev; }
        _move(prev, msg.sender, 1);
        heldSince = block.timestamp;

        // the pulse: spread life across the ring, none of it reclaimable by anyone
        address[] memory ring = art.allPieces();
        uint256 n = ring.length;
        if (n > 0) {
            uint256 share = msg.value / n;
            for (uint256 i; i < n; ++i) {
                (bool ok,) = ring[i].call{value: share}(abi.encodeWithSignature("pulse()"));
                ok; // best-effort: the collection breathes
            }
        }
        emit Heartbeat(msg.sender, msg.value);
    }

    function age() public view returns (uint256) { return block.timestamp - heldSince; }

    function defaultRender(uint256) public view override returns (string memory) {
        string memory a = string(abi.encodePacked("alive ", Meta.str(age() / 1 days), "d"));
        return Meta.uri("Proof of Life", "the heart, it beats or it passes",
            Meta.plate(a, "#faf8f3", "#141210"));
    }

    function rules() external pure override returns (string memory) {
        return "Proof of Life. anyone may seize it with a heavy beat() that pulses life through all ten. it records who held it longest.";
    }
}
