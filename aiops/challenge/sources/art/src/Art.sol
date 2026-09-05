// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IRenderer, ICollectible, IFork} from "./Interfaces.sol";

/// @title Art
/// @notice The face of the collection is decided by the collection itself.
///
/// Until the market proves the work, every piece renders itself (a word, a price,
/// a colour). Anyone may propose a renderer; Fork holders endorse it. A proposal
/// becomes the collection's face once it is backed by more than half of the Fork
/// editions AND the collection has sold at least SET_GATE. The community can keep
/// replacing it the same way, or seal it forever once sales reach SEAL_GATE and a
/// two-thirds supermajority backs the standing renderer.
///
/// Sealing freezes *which* renderer is authoritative, not its output: a renderer
/// that reads a piece's live state (Tug's colour, Ask's price) keeps moving forever.
/// The call is view-only and always falls back to a piece's own render, so an ugly
/// or broken renderer can never break, drain, or freeze anything.
///
/// Art is deployed first (so every piece can hold its address immutably) and learns
/// the ring through a single, steward-only, one-time `init` - the collection's only
/// genesis mutation; after it, nothing about the ring can change.
contract Art {
    address public immutable steward;
    IFork public fork;
    address[] public pieces; // the ring, summed for volume()
    bool public inited;

    address public renderer; // address(0) => every piece renders itself
    bool public frozen; // once true, the face is frozen

    uint256 public constant SET_GATE = 10 ether; // sales before a face may be set
    uint256 public constant SEAL_GATE = 100 ether; // sales before it may be sealed

    // candidate => endorser => endorsed?  (weight is read live from Fork balances)
    mapping(address => mapping(address => bool)) public endorsed;
    mapping(address => address[]) private _endorsers;

    event Proposed(address indexed candidate, address indexed by);
    event Endorsed(address indexed candidate, address indexed by, uint256 weight);
    event Adopted(address indexed renderer, uint256 support, uint256 supply);
    event Sealed(address indexed renderer);

    constructor(address steward_) {
        steward = steward_;
    }

    function init(IFork fork_, address[] calldata pieces_) external {
        require(msg.sender == steward && !inited, "init");
        fork = fork_;
        pieces = pieces_;
        inited = true;
    }

    function allPieces() external view returns (address[] memory) {
        return pieces;
    }

    function rules() external pure returns (string memory) {
        return "Art. the collection's face, chosen by the collection. anyone proposes a renderer; Fork holders endorse it; adopted past ten ETH of sales, sealed past a hundred. until then, each piece renders itself.";
    }

    // --- the smart quorum: the collection's own sales ---

    function volume() public view returns (uint256 v) {
        address[] memory p = pieces;
        for (uint256 i; i < p.length; ++i) v += ICollectible(p[i]).volume();
    }

    function support(address candidate) public view returns (uint256 s) {
        address[] memory e = _endorsers[candidate];
        for (uint256 i; i < e.length; ++i) s += fork.balanceOf(e[i]);
    }

    // --- governance: propose, endorse, seal ---

    function propose(address candidate) external {
        require(candidate != address(0) && candidate != renderer, "bad candidate");
        emit Proposed(candidate, msg.sender);
    }

    function endorse(address candidate) external {
        require(!frozen, "sealed");
        require(!endorsed[candidate][msg.sender], "already");
        uint256 w = fork.balanceOf(msg.sender);
        require(w > 0, "not a member");

        endorsed[candidate][msg.sender] = true;
        _endorsers[candidate].push(msg.sender);
        emit Endorsed(candidate, msg.sender, w);

        uint256 supply = fork.totalSupply();
        uint256 s = support(candidate);
        if (supply > 0 && s * 2 > supply && volume() >= SET_GATE) {
            renderer = candidate;
            emit Adopted(candidate, s, supply);
        }
    }

    function seal() external {
        require(!frozen, "sealed");
        require(renderer != address(0), "no face");
        require(volume() >= SEAL_GATE, "not proven");
        require(support(renderer) * 3 >= fork.totalSupply() * 2, "no supermajority");
        frozen = true;
        emit Sealed(renderer);
    }

    // --- rendering (called by each piece's tokenURI) ---

    function rendering(uint256 id) external view returns (string memory) {
        address piece = msg.sender;
        address r = renderer;
        if (r == address(0)) return ICollectible(piece).defaultRender(id);
        try IRenderer(r).render(piece, id) returns (string memory uri) {
            return uri;
        } catch {
            return ICollectible(piece).defaultRender(id);
        }
    }
}
