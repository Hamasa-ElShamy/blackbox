"""Measure BlackBox on randomly built layouts. Truth is known because we build the files."""
import random, struct, sys
sys.path.insert(0, ".")
from blackbox import core

TYPES = {  # name: (struct code, size, generator)
    "u8": ("B", 1, lambda i, rnd: rnd.choice([0, 1, 2, 4, 8])),
    "u16": ("H", 2, lambda i, rnd: rnd.randint(0, 3000)),
    "u32": ("I", 4, lambda i, rnd: rnd.randint(0, 5_000_000)),
    "f32": ("f", 4, lambda i, rnd: round(rnd.uniform(-50, 150), 3)),
    "f64": ("d", 8, lambda i, rnd: rnd.uniform(-180, 180)),
    "time": ("I", 4, lambda i, rnd: 1_700_000_000 + i * rnd.choice([30, 60])),
    "text": ("8s", 8, lambda i, rnd: rnd.choice([b"alpha", b"beta", b"gamma01", b"delta"])),
}
KIND = {"u8": "uint8", "u16": "uint16", "u32": "uint32", "f32": "float32", "f64": "float64", "time": "timestamp", "text": "text"}


def one(seed):
    rnd = random.Random(seed)
    names = [rnd.choice(list(TYPES)) for _ in range(rnd.randint(3, 7))]
    end = rnd.choice("<>"); hdr = rnd.choice([0, 0, 8, 16]); n = rnd.choice([100, 300, 1000])
    fmt = end + "".join(TYPES[t][0] for t in names)
    body = b"".join(struct.pack(fmt, *[TYPES[t][2](i, rnd) for t in names]) for i in range(n))
    data = bytes(rnd.choice(b"HDR_ABCDEFGHIJK") for _ in range(hdr)) + body
    r = core.analyse(data)
    R = struct.calcsize(fmt)
    lay_ok = bool(r["layout"]) and r["layout"]["record_size"] == R and r["layout"]["header_size"] == hdr
    got = [f["kind"] for f in r["fields"]]
    # compare field-by-field only when the layout was right
    want, off = [], 0
    for t in names:
        want.append((off, KIND[t])); off += TYPES[t][1]
    gotl = {(f["off"], f["kind"]) for f in r["fields"]} if r["layout"] else set()
    fields_ok = sum(1 for w in want if w in gotl)
    return lay_ok, fields_ok, len(want), end, names


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    res = [one(s) for s in range(N)]
    lay = sum(r[0] for r in res); fo = sum(r[1] for r in res if r[0]); ft = sum(r[2] for r in res if r[0])
    print(f"files: {N}; layout (header size + record size) exactly right: {lay}/{N}")
    print(f"fields exactly right (offset and type), among files with right layout: {fo}/{ft} = {fo/ft:.0%}")
    bad = [(s, r[4]) for s, r in enumerate(res) if not r[0]][:5]
    print("first layout misses (seed, field types):", bad)
