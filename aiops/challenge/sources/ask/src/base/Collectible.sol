// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "./ERC721.sol";
import {ICollectible} from "../Interfaces.sol";

interface IArt {
    function rendering(uint256 id) external view returns (string memory);
    function allPieces() external view returns (address[] memory);
}

/// @notice Common ground for every piece of the collection.
///
/// - the image is delegated to `Art` (which falls back to this piece's own
///   `defaultRender`), so the community can dress the collection later; `art` is
///   fixed at construction - no piece can ever be re-pointed;
/// - `beacon` is a strictly separate bag of ETH the steward may top up and pull back
///   for discovery - it can never touch a sale, a fee, or a holder's funds;
/// - `volume` is the cumulative ETH that has moved through the piece; Art sums it
///   across the ring to gate the community's power.
abstract contract Collectible is ERC721, ICollectible {
    address public immutable steward; // the deployer (0xflorent) - beacon only
    IArt public immutable art;

    uint256 public volume; // cumulative sales (ICollectible)
    uint256 public beaconBalance; // discovery bait, segregated
    uint256 public lifeBalance; // fed by Proof of Life's heartbeat, never withdrawable

    constructor(string memory n, string memory s, address steward_, IArt art_) ERC721(n, s) {
        steward = steward_;
        art = art_;
    }

    modifier onlySteward() { require(msg.sender == steward, "not steward"); _; }

    function tokenURI(uint256 id) public view override returns (string memory) {
        ownerOf(id); // reverts if not minted
        return art.rendering(id);
    }

    // --- the piece's own permanent look (used until the community adopts art) ---
    function defaultRender(uint256 id) public view virtual returns (string memory);

    // --- the on-chain readme, read by scanners and humans ---
    function rules() external view virtual returns (string memory);

    // --- beacon: discovery bait the steward may add and reclaim, nothing else ---
    function seedBeacon() external payable onlySteward { beaconBalance += msg.value; }

    function pullBeacon(uint256 amount) external onlySteward {
        require(amount <= beaconBalance, "over beacon");
        beaconBalance -= amount;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send");
    }

    /// anyone (Proof of Life's heartbeat) may add permanent, non-withdrawable life
    function pulse() external payable { lifeBalance += msg.value; }

    // --- internal: record a sale toward the collection's proven volume ---
    function _sold(uint256 amount) internal { volume += amount; }

    function _pay(address to, uint256 amount) internal {
        (bool ok,) = to.call{value: amount}("");
        require(ok, "pay");
    }
}
