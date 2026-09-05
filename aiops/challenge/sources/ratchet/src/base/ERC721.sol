// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Minimal ERC-721 (single-file, no deps). Enough for the collection:
/// ownership, transfer, approval, enumerable-free. `tokenURI` is left abstract.
abstract contract ERC721 {
    string public name;
    string public symbol;

    mapping(uint256 => address) internal _ownerOf;
    mapping(address => uint256) internal _balanceOf;
    mapping(uint256 => address) public getApproved;
    mapping(address => mapping(address => bool)) public isApprovedForAll;

    event Transfer(address indexed from, address indexed to, uint256 indexed id);
    event Approval(address indexed owner, address indexed spender, uint256 indexed id);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function tokenURI(uint256 id) public view virtual returns (string memory);

    function ownerOf(uint256 id) public view virtual returns (address owner) {
        require((owner = _ownerOf[id]) != address(0), "not minted");
    }

    function balanceOf(address owner) public view virtual returns (uint256) {
        require(owner != address(0), "zero");
        return _balanceOf[owner];
    }

    function approve(address spender, uint256 id) public virtual {
        address owner = _ownerOf[id];
        require(msg.sender == owner || isApprovedForAll[owner][msg.sender], "not authorized");
        getApproved[id] = spender;
        emit Approval(owner, spender, id);
    }

    function setApprovalForAll(address operator, bool approved) public virtual {
        isApprovedForAll[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    /// override point for pieces with special transfer rules (soulbound, gift-only, ...)
    function _beforeTransfer(address from, address to, uint256 id) internal virtual {}

    function transferFrom(address from, address to, uint256 id) public virtual {
        require(from == _ownerOf[id], "wrong from");
        require(to != address(0), "zero to");
        require(
            msg.sender == from || isApprovedForAll[from][msg.sender] || msg.sender == getApproved[id],
            "not authorized"
        );
        _beforeTransfer(from, to, id);
        _balanceOf[from]--;
        _balanceOf[to]++;
        _ownerOf[id] = to;
        delete getApproved[id];
        emit Transfer(from, to, id);
    }

    function safeTransferFrom(address from, address to, uint256 id) public virtual {
        transferFrom(from, to, id);
    }

    function supportsInterface(bytes4 iid) public pure virtual returns (bool) {
        return iid == 0x80ac58cd || iid == 0x01ffc9a7 || iid == 0x5b5e139f; // 721, 165, metadata
    }

    // --- internal mint / move used by piece mechanics ---

    function _mint(address to, uint256 id) internal virtual {
        require(to != address(0), "zero");
        require(_ownerOf[id] == address(0), "exists");
        _balanceOf[to]++;
        _ownerOf[id] = to;
        emit Transfer(address(0), to, id);
    }

    /// mechanic-driven move (a sale, a paint, a beat): bypasses approvals AND the
    /// public-transfer guard, so gift-only / soulbound pieces still run their own logic
    function _move(address from, address to, uint256 id) internal virtual {
        if (from != address(0)) _balanceOf[from]--;
        _balanceOf[to]++;
        _ownerOf[id] = to;
        delete getApproved[id];
        emit Transfer(from, to, id);
    }
}
