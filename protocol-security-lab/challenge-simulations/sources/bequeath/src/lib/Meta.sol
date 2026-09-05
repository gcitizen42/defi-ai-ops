// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Tiny on-chain rendering helpers. Everything is a `utf8` data URI - no
/// base64, no libraries - so the primary render of every piece is plain, permanent
/// and legible in the bytecode itself. SVG uses single quotes so it nests inside
/// the JSON's double quotes without escaping.
library Meta {
    /// unsigned integer -> decimal string
    function str(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 n = v;
        uint256 len;
        while (n != 0) { len++; n /= 10; }
        bytes memory b = new bytes(len);
        while (v != 0) { b[--len] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }

    /// wei -> "12.34" ETH string, trimmed to `decimals` places
    function eth(uint256 wei_, uint256 decimals) internal pure returns (string memory) {
        uint256 whole = wei_ / 1e18;
        uint256 frac = (wei_ % 1e18) / (10 ** (18 - decimals));
        bytes memory f = bytes(str(frac));
        // left-pad the fraction to `decimals` digits
        bytes memory pad = new bytes(decimals);
        for (uint256 i; i < decimals; ++i) pad[i] = "0";
        for (uint256 i; i < f.length; ++i) pad[decimals - f.length + i] = f[i];
        return string(abi.encodePacked(str(whole), ".", pad));
    }

    /// #rrggbb from a packed uint24
    function color(uint24 c) internal pure returns (string memory) {
        bytes16 hexd = "0123456789abcdef";
        bytes memory s = new bytes(7);
        s[0] = "#";
        for (uint256 i; i < 6; ++i) s[6 - i] = hexd[(uint256(c) >> (4 * i)) & 0xf];
        return string(s);
    }

    /// wrap an <svg> body into a full data URI with name + description
    function uri(string memory name, string memory desc, string memory svg)
        internal pure returns (string memory)
    {
        return string(abi.encodePacked(
            "data:application/json;utf8,",
            '{"name":"', name, '","description":"', desc,
            '","image":"data:image/svg+xml;utf8,', svg, '"}'
        ));
    }

    /// the primary look: one thing, centred, on a ground. `main` is the word / number,
    /// `bg` the ground, `fg` the ink. No ornament - the word carries it.
    function plate(string memory main, string memory bg, string memory fg)
        internal pure returns (string memory)
    {
        return string(abi.encodePacked(
            "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='600' viewBox='0 0 600 600'>",
            "<rect width='600' height='600' fill='", bg, "'/>",
            "<text x='300' y='318' text-anchor='middle' ",
            "font-family='Didot, \"Bodoni MT\", \"Hoefler Text\", Georgia, serif' ",
            "font-size='72' fill='", fg, "'>", main, "</text></svg>"
        ));
    }

    /// a full field of one colour - Tug's primary look
    function field(string memory hexColor) internal pure returns (string memory) {
        return string(abi.encodePacked(
            "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='600'>",
            "<rect width='600' height='600' fill='", hexColor, "'/></svg>"
        ));
    }
}
