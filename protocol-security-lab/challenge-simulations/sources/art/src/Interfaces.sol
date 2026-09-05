// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// A community-adopted renderer. Receives the piece's address so it may read the
/// piece's live state and return a static image OR a state-reactive one (Tug, Ask).
interface IRenderer {
    function render(address piece, uint256 id) external view returns (string memory uri);
}

/// Every piece of the collection exposes these to Art.
interface ICollectible {
    /// cumulative ETH that has ever changed hands through this piece (primary + secondary).
    function volume() external view returns (uint256);
    /// the piece's own honest rendering, used until the community adopts an Art renderer
    /// (Ask -> its price, Tug -> its colour, the rest -> their word).
    function defaultRender(uint256 id) external view returns (string memory uri);
}

/// Fork is the membership token: one endorsement weight per edition held.
interface IFork {
    function totalSupply() external view returns (uint256);
    function balanceOf(address holder) external view returns (uint256);
}
