"""Six realistic record layouts written the way real programs write them (utmp, sensor logger, GPS track,
high-score file, network flow log, accelerometer). Values are random but drawn from realistic ranges.
Truth is known because we build the files. Each layout is built 5 times (different seeds and record counts)."""
import random, struct, sys
sys.path.insert(0, ".")
from blackbox import core

def utmp(r, n):
    out = b""
    for i in range(n):
        out += struct.pack("<hxxi32s4s32s256shhiii4i20s", 7, r.randint(100, 40000), b"pts/%d" % r.randint(0, 9), b"ts/%d" % (i % 9), r.choice([b"alice", b"bob", b"mohamed", b"root"]),
                           r.choice([b"192.168.1.%d" % r.randint(2, 99), b"10.0.0.%d" % r.randint(2, 99)]), 0, 0, r.randint(1, 5000), 1_700_000_000 + i * r.randint(60, 600), r.randint(0, 999999), 0, 0, 0, 0, b"")
    return out
def sensor(r, n):
    t = 1_700_000_000
    body = b""
    for i in range(n):
        t += 60; body += struct.pack("<IffHBB", t, 20 + r.gauss(0, 2), 45 + r.gauss(0, 8), r.randint(3300, 4200), r.choice([0, 1, 1, 3]), 0)
    return b"SENS\x01\x00\x00\x00" + struct.pack("<II", n, 60) + body
def gps(r, n):
    lat, lon, t = 30.5877, 31.5020, 1_700_000_000
    out = b""
    for i in range(n):
        lat += r.gauss(0, 0.0002); lon += r.gauss(0, 0.0002); t += 5
        out += struct.pack("<ddIf", lat, lon, t, abs(r.gauss(8, 3)))
    return out
def scores(r, n):
    return b"".join(struct.pack("<16sIHH", r.choice([b"ALI", b"SARA", b"MOHAMED", b"LAYLA", b"OMAR"]), r.randint(0, 99999), r.randint(1, 40), r.choice([0, 1, 2, 4])) for _ in range(n))
def flows(r, n):
    t = 1_700_000_000; out = b""
    for i in range(n):
        t += r.randint(0, 3)
        out += struct.pack(">IIIHHBBH", t, 0xC0A80000 + r.randint(2, 200), 0x08080000 + r.randint(0, 255), r.randint(1024, 65535), r.choice([80, 443, 53, 22]), r.choice([6, 17]), r.choice([2, 16, 18, 24]), r.randint(40, 1500))
    return out
def accel(r, n):
    return b"".join(struct.pack("<hhhH", int(r.gauss(0, 800)), int(r.gauss(0, 800)), int(r.gauss(-1000, 300)), r.randint(9, 11)) for _ in range(n))

# name: (builder, header size, record size, [(offset, kind)])
L = {
 "utmp (384-byte login records)": (utmp, 0, 384, [(0, "uint16"), (4, "uint32"), (8, "text"), (40, "text"), (44, "text"), (76, "text")]),
 "sensor logger (16-byte header)": (sensor, 16, 16, [(0, "timestamp"), (4, "float32"), (8, "float32"), (12, "uint16"), (14, "uint8")]),
 "GPS track": (gps, 0, 24, [(0, "float64"), (8, "float64"), (16, "timestamp"), (20, "float32")]),
 "high-score file": (scores, 0, 24, [(0, "text"), (16, "uint32"), (20, "uint16"), (22, "uint16")]),
 "network flow log (big endian)": (flows, 0, 20, [(0, "timestamp"), (4, "uint32"), (8, "uint32"), (12, "uint16"), (14, "uint16"), (16, "uint8"), (17, "uint8"), (18, "uint16")]),
 "accelerometer (signed values)": (accel, 0, 8, [(0, "int16"), (2, "int16"), (4, "int16"), (6, "uint16")]),
}

def run(verbose=True):
    tot_l = tot_ok = tot_f = tot_n = 0
    for name, (build, H, R, want) in L.items():
        lay = fo = 0
        for seed in range(5):
            r = random.Random(seed); data = build(r, [200, 500, 1000, 300, 800][seed])
            a = core.analyse(data)
            ok = bool(a["layout"]) and a["layout"]["record_size"] == R and a["layout"]["header_size"] == H
            lay += ok
            got = {(f["off"], f["kind"]) for f in a["fields"]} if ok else set()
            fo += sum(w in got for w in want)
        tot_l += lay; tot_ok += fo; tot_n += 5 * len(want)
        if verbose: print(f"{name:34s} layout right {lay}/5   fields right {fo}/{5 * len(want)}")
    print(f"TOTAL layout right {tot_l}/{5 * len(L)}; fields right {tot_ok}/{tot_n} ({tot_ok / tot_n:.0%}) (counted over all fields, wrong layout counts as wrong)")

if __name__ == "__main__":
    run()
