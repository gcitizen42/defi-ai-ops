// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract RendererProof {
    address public immutable claimant;

    constructor(address claimant_) {
        claimant = claimant_;
    }

    function render(address, uint256) external view returns (string memory) {
        return string.concat(
            "data:application/json;utf8,",
            "{\"name\":\"Renderer claimed\",",
            "\"description\":\"0xFlorent challenge renderer controlled by ",
            _toHex(claimant),
            "\",",
            "\"image\":\"data:image/svg+xml;utf8,",
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 1200'>",
            "<rect width='1200' height='1200' fill='black'/>",
            "<text x='600' y='570' fill='white' font-size='64' text-anchor='middle'>Renderer claimed</text>",
            "<text x='600' y='660' fill='white' font-size='28' text-anchor='middle'>",
            _toHex(claimant),
            "</text></svg>\"}"
        );
    }

    function _toHex(address account) private pure returns (string memory) {
        bytes20 value = bytes20(account);
        bytes16 symbols = "0123456789abcdef";
        bytes memory out = new bytes(42);
        out[0] = "0";
        out[1] = "x";
        for (uint256 i; i < 20; ++i) {
            out[2 + i * 2] = symbols[uint8(value[i] >> 4)];
            out[3 + i * 2] = symbols[uint8(value[i] & 0x0f)];
        }
        return string(out);
    }
}
