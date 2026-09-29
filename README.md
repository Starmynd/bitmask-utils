# bitmask-utils

Classic bit-twiddling helpers for Python ints. Pure standard library,
works with arbitrary-precision values.

## API

```python
from bitmask_utils import (set_bit, clear_bit, toggle_bit, test_bit,
                           popcount, submasks, k_subsets, to_bits,
                           encode_flags, decode_flags)

set_bit(0b0100, 0)        # 0b0101
clear_bit(0b0101, 2)      # 0b0001
toggle_bit(0b0001, 3)     # 0b1001
test_bit(0b1001, 3)       # True

popcount(0b1010)          # 2  (Kernighan trick, no bin().count)
submasks(0b1010)          # [0b1010, 0b1000, 0b0010, 0b0000]
k_subsets(4, 2)           # [[0,1], [0,2], [0,3], [1,2], [1,3], [2,3]]
to_bits(0b0101, 6)        # "000101"

flags = ("read", "write", "exec")
mask = encode_flags(flags, ["read", "exec"])   # 0b101
decode_flags(flags, mask)                      # ["read", "exec"]
```

- `popcount` clears the lowest set bit each step (`n &= n - 1`).
- `submasks` walks `(sub - 1) & mask`, descending, including 0 and the
  mask itself.
- `k_subsets` uses Gosper's hack; `n` is capped at 62 (documented).
- `encode_flags` / `decode_flags` map names to bits by list index and
  raise `ValueError` on unknown names / out-of-range masks.

## CLI

```console
$ bitmask-utils popcount 0xff
8

$ bitmask-utils bits 42 --width 8
00101010

$ bitmask-utils submasks 10
1010
1000
0010
0000

$ bitmask-utils ksubsets 4 2
0 1
0 2
...
```

Integer arguments accept `0x`/`0b` prefixes (`int(s, 0)`).

## Testing

```console
$ python3 bitmask_utils.py --test
selftest: failures=0
```

Covers each bit operation, popcount on wide values, the binomial
identity over submask popcounts, k-subset counts and membership, bit
formatting and the flag codec including error paths.

## License

MIT
