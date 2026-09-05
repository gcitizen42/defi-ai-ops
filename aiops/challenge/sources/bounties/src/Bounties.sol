// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IHeld { function ownerOf(uint256) external view returns (address); }
interface IBal { function balanceOf(address) external view returns (uint256); }
interface IWit {
    function witnessCount() external view returns (uint256);
    function witnesses(uint256) external view returns (address);
}

/// @title Bounties - a small purse that reimburses the first testers of the collection.
///
/// Ten quests, each a real, on-chain interaction with a piece. The FIRST address to
/// satisfy a quest may claim it once; every address may claim at most one quest. So a
/// bot cannot loop a quest, and to grab several it needs several addresses AND several
/// distinct interactions - the costly ones (buying a piece) pay less than they cost, so
/// farming is a loss. The steward may withdraw the remainder at any time (kill-switch);
/// the most that can ever leave is the purse itself.
contract Bounties {
    uint256 public constant REWARD = 0.0025 ether;
    uint8 public constant QUESTS = 10;

    address public immutable steward;
    address public immutable tug;
    address public immutable life;
    address public immutable bequeath;
    address public immutable fork;
    address public immutable ask;
    address public immutable lineage;
    address public immutable ratchet;
    address public immutable pyre;
    address public immutable verb;

    mapping(uint8 => address) public wonBy; // quest => winner (0 = open)
    mapping(address => bool) public claimed; // one reward per address

    event Claimed(uint8 indexed quest, address indexed who, uint256 reward);

    /// order: [tug, life, bequeath, fork, ask, lineage, ratchet, pyre, verb]
    constructor(address steward_, address[9] memory p) payable {
        steward = steward_;
        tug = p[0]; life = p[1]; bequeath = p[2]; fork = p[3]; ask = p[4];
        lineage = p[5]; ratchet = p[6]; pyre = p[7]; verb = p[8];
    }

    receive() external payable {}

    /// true if `who` has really done quest `q` on the live collection
    function qualifies(uint8 q, address who) public view returns (bool) {
        if (q == 0) return IHeld(tug).ownerOf(1) == who; // painted Tug
        if (q == 1) return IHeld(life).ownerOf(1) == who; // beat Proof of Life
        if (q == 2) return IHeld(bequeath).ownerOf(1) == who && who != steward; // was gifted Bequeath
        if (q == 3) return IBal(fork).balanceOf(who) > 0; // minted a Fork
        if (q == 4) return IHeld(ask).ownerOf(1) == who && who != steward; // bought Ask
        if (q == 5) return IHeld(lineage).ownerOf(1) == who && who != steward; // bought Lineage
        if (q == 6) return IHeld(ratchet).ownerOf(1) == who && who != steward; // bought Ratchet
        if (q == 7) return IHeld(pyre).ownerOf(1) == who && who != steward; // bought Pyre
        if (q == 8) { // echoed Verb (most recent witness)
            uint256 c = IWit(verb).witnessCount();
            return c > 0 && IWit(verb).witnesses(c - 1) == who;
        }
        if (q == 9) return IBal(fork).balanceOf(who) >= 2; // a collector: two Fork editions
        return false;
    }

    function claim(uint8 q) external {
        require(q < QUESTS, "no such quest");
        require(wonBy[q] == address(0), "quest taken");
        require(!claimed[msg.sender], "already rewarded");
        require(msg.sender != steward, "not the steward");
        require(qualifies(q, msg.sender), "not done");

        wonBy[q] = msg.sender;
        claimed[msg.sender] = true;
        (bool ok,) = msg.sender.call{value: REWARD}("");
        require(ok, "reward failed");
        emit Claimed(q, msg.sender, REWARD);
    }

    /// the steward may reclaim whatever is left, whenever they want
    function withdraw() external {
        require(msg.sender == steward, "not steward");
        (bool ok,) = steward.call{value: address(this).balance}("");
        require(ok, "withdraw");
    }

    function rules() external pure returns (string memory) {
        return "Bounties. be the first to test a piece of the collection - paint Tug, beat Proof of Life, hold a piece - and claim your gas back. one reward per address.";
    }
}
