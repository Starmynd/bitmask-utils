#!/usr/bin/env python3
"""bitmask-utils - classic bit-twiddling helpers.

Pure standard library, arbitrary-precision Python ints. Covers the
everyday operations (set/clear/toggle/test), population count via the
Kernighan trick, submask and fixed-size-k-subset enumeration, bit
string formatting and a small name<->mask codec for named flags.

CLI subcommands demonstrate the main operations on small inputs.
"""

from __future__ import annotations

import argparse
import sys


def set_bit(mask: int, i: int) -> int:
    """Return mask with bit i set to 1."""
    return mask | (1 << i)


def clear_bit(mask: int, i: int) -> int:
    """Return mask with bit i set to 0."""
    return mask & ~(1 << i)


def toggle_bit(mask: int, i: int) -> int:
    """Return mask with bit i flipped."""
    return mask ^ (1 << i)


def test_bit(mask: int, i: int) -> bool:
    """True if bit i of mask is 1."""
    return bool(mask & (1 << i))


def popcount(n: int) -> int:
    """Number of set bits (Kernighan: clears the lowest set bit per step)."""
    if n < 0:
        raise ValueError("popcount requires a non-negative integer")
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


def submasks(mask: int) -> list[int]:
    """All submasks of mask, including 0 and mask itself, descending."""
    if mask < 0:
        raise ValueError("submasks requires a non-negative integer")
    out = []
    sub = mask
    while True:
        out.append(sub)
        if sub == 0:
            break
        sub = (sub - 1) & mask
    return out


def k_subsets(n: int, k: int) -> list[list[int]]:
    """All k-element subsets of {0..n-1} as sorted index lists (Gosper)."""
    if not 0 <= k <= n:
        raise ValueError("need 0 <= k <= n")
    out = []
    if n > 62:
        raise ValueError("Gosper enumeration supports n <= 62")
    mask = (1 << k) - 1
    limit = 1 << n
    while mask < limit:
        out.append([i for i in range(n) if test_bit(mask, i)])
        if mask == 0:
            break
        c = mask & -mask
        r = mask + c
        mask = (((r ^ mask) >> 2) // c) | r
    return out


def to_bits(n: int, width: int = 0) -> str:
    """Binary string, optionally zero-padded to `width` digits."""
    if n < 0:
        raise ValueError("to_bits requires a non-negative integer")
    s = bin(n)[2:]
    return s.zfill(width) if width else s


def encode_flags(names: list[str] | tuple[str, ...],
                 selected: list[str] | tuple[str, ...]) -> int:
    """Pack selected names into a bit mask (index in `names` == bit)."""
    lookup = {name: i for i, name in enumerate(names)}
    unknown = [s for s in selected if s not in lookup]
    if unknown:
        raise ValueError(f"unknown flags: {', '.join(sorted(unknown))}")
    mask = 0
    for s in selected:
        mask = set_bit(mask, lookup[s])
    return mask


def decode_flags(names: list[str] | tuple[str, ...], mask: int) -> list[str]:
    """Unpack a bit mask back into the selected names, in `names` order."""
    if mask < 0:
        raise ValueError("mask must be non-negative")
    if mask >> len(names):
        raise ValueError("mask has bits outside the flag set")
    return [name for i, name in enumerate(names) if test_bit(mask, i)]


def _selftest() -> int:
    failed = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed
        print(("PASS " if cond else "FAIL ") + label)
        if not cond:
            failed += 1

    m = 0b0100
    m = set_bit(m, 0)
    check(m == 0b0101, "set_bit")
    m = clear_bit(m, 2)
    check(m == 0b0001, "clear_bit")
    m = toggle_bit(m, 3)
    check(m == 0b1001, "toggle_bit")
    check(test_bit(m, 3) and not test_bit(m, 2), "test_bit")

    check(popcount(0) == 0, "popcount 0")
    check(popcount(0b1010) == 2, "popcount 0b1010")
    check(popcount((1 << 70) - 1) == 70, "popcount 70 ones")

    sm = submasks(0b1010)
    check(sm == [0b1010, 0b1000, 0b0010, 0b0000] and len(sm) == 4,
          f"submasks(0b1010) -> 4 values (got {[bin(x) for x in sm]})")
    check(sum(popcount(x) for x in submasks(0b111)) == 1 * 3 + 2 * 3 + 3,
          "submask popcount sum (binomial identity)")

    ks = k_subsets(4, 2)
    check(len(ks) == 6, f"k_subsets(4,2) -> 6 (got {len(ks)})")
    check([0, 1] in ks and [2, 3] in ks, "k_subsets members look right")
    check(k_subsets(5, 0) == [[]] and k_subsets(3, 3) == [[0, 1, 2]],
          "k_subsets edge sizes")

    check(to_bits(0b0101, 6) == "000101", "to_bits zero pad")
    check(to_bits(0) == "0" and to_bits(2) == "10", "to_bits plain")

    names = ("read", "write", "exec")
    mask = encode_flags(names, ["read", "exec"])
    check(mask == 0b101, "encode_flags")
    check(decode_flags(names, mask) == ["read", "exec"], "decode_flags")
    try:
        encode_flags(names, ["delete"])
        check(False, "unknown flag raises")
    except ValueError:
        check(True, "unknown flag raises")

    print(f"selftest: failures={failed}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--test" in argv:
        return _selftest()

    ap = argparse.ArgumentParser(prog="bitmask-utils",
                                 description="Classic bit-twiddling helpers.")
    sub = ap.add_subparsers(dest="cmd")

    p_pop = sub.add_parser("popcount", help="count set bits")
    p_pop.add_argument("n", type=lambda s: int(s, 0))

    p_bits = sub.add_parser("bits", help="format as binary")
    p_bits.add_argument("n", type=lambda s: int(s, 0))
    p_bits.add_argument("--width", type=int, default=0)

    p_sub = sub.add_parser("submasks", help="enumerate submasks")
    p_sub.add_argument("n", type=lambda s: int(s, 0))

    p_k = sub.add_parser("ksubsets", help="enumerate k-subsets of 0..n-1")
    p_k.add_argument("n", type=int)
    p_k.add_argument("k", type=int)

    args = ap.parse_args(argv)
    if args.cmd == "popcount":
        print(popcount(args.n))
    elif args.cmd == "bits":
        print(to_bits(args.n, args.width))
    elif args.cmd == "submasks":
        for x in submasks(args.n):
            print(to_bits(x, args.n.bit_length() or 1))
    elif args.cmd == "ksubsets":
        for subset in k_subsets(args.n, args.k):
            print(" ".join(map(str, subset)))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
