// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Collectible, IArt} from "../base/Collectible.sol";
import {Meta} from "../lib/Meta.sol";

/// @title Tug - one colour, painted by the crowd.
/// Painting (gas only) pulls the colour one eighth toward yours and makes you its
/// holder. Every stroke is engraved forever - the colour, the painter, the block -
/// so Tug carries the complete history of the canvas. Its own face is the colour
/// itself, and it tints the whole collection.
contract Tug is Collectible {
    uint24 public color = 0x808080; // neutral grey

    struct Snap { uint24 color; address painter; uint64 blockNo; }
    Snap[] public snaps;

    event Painted(address indexed painter, uint24 color);

    constructor(address steward_, IArt art_) Collectible("Tug", "TUG", steward_, art_) {
        _mint(steward_, 1);
    }

    function paint(uint24 target) external {
        color = _pull(color, target);
        _move(ownerOf(1), msg.sender, 1); // the last painter holds it
        snaps.push(Snap(color, msg.sender, uint64(block.number))); // every stroke, forever
        emit Painted(msg.sender, color);
    }

    function _pull(uint24 c, uint24 t) internal pure returns (uint24 out) {
        for (uint256 i; i < 3; ++i) {
            uint256 shift = 8 * i;
            int256 cc = int256((uint256(c) >> shift) & 0xff);
            int256 tt = int256((uint256(t) >> shift) & 0xff);
            int256 nc = cc + (tt - cc) / 8; // one eighth toward the target channel
            out |= uint24(uint256(nc) << shift);
        }
    }

    function snapCount() external view returns (uint256) { return snaps.length; }

    function defaultRender(uint256) public view override returns (string memory) {
        return Meta.uri("Tug", "painted by the crowd", Meta.field(Meta.color(color)));
    }

    function rules() external pure override returns (string memory) {
        return "Tug. paint (gas only) pulls the colour one eighth toward yours and makes you its holder. every stroke is engraved forever.";
    }
}
