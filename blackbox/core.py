"""Guess the layout of a file made of fixed-size records. Standard library only.

Everything here is a heuristic. analyse() returns its guesses with a confidence
and the reasons, never a claim that the layout is right.
"""
import math, struct, time

MAGIC = [(b"\x89PNG\r\n\x1a\n", "PNG image"), (b"\xff\xd8\xff", "JPEG image"), (b"GIF8", "GIF image"),
         (b"%PDF", "PDF document"), (b"PK\x03\x04", "ZIP container (also docx, xlsx, jar, apk)"),
         (b"\x1f\x8b", "gzip data"), (b"SQLite format 3\x00", "SQLite database"), (b"\x7fELF", "ELF program"),
         (b"RIFF", "RIFF container (wav, avi, webp)"), (b"MZ", "Windows program (exe, dll)"),
         (b"BM", "BMP image"), (b"OggS", "Ogg media"), (b"ID3", "MP3 audio")]


def entropy(b):
    if not b: return 0.0
    c = [0] * 256
    for x in b: c[x] += 1
    n = len(b)
    return -sum(k / n * math.log2(k / n) for k in c if k)


def known_format(data):
    for m, name in MAGIC:
        if data.startswith(m): return name
    return None


def _score(data, H, R, n):
    """How regular are the columns? Low byte entropy per column plus similar neighbours (0..1)."""
    n = min(n, 2000)
    if n < 4: return 0.0
    ent = 0.0; same = 0
    for c in range(R):
        col = data[H + c:H + n * R:R][:n]
        ent += entropy(col)
        for i in range(1, len(col)):
            if abs(col[i] - col[i - 1]) <= 2: same += 1
    cap = math.log2(min(n, 256))
    return 0.7 * (1 - ent / R / cap) + 0.3 * same / (R * (n - 1))


def find_layout(data):
    """Return (header_size, record_size, records, score, notes) or None."""
    L = len(data)
    best = None
    for R in range(2, 513):
        for H in range(0, min(129, L // 4)):
            if (L - H) % R: continue
            n = (L - H) // R
            if n < 4: continue
            s = _score(data, H, R, n)
            # a bigger multiple of the true size scores the same; prefer the smallest that is nearly as good
            cand = (s, -R, H)
            if best is None or s > best[0] + 0.02 or (abs(s - best[0]) <= 0.02 and R < best[1]):
                best = (s, R, H, n)
    if not best or best[0] < 0.35: return None
    s, R, H, n = best
    return H, R, n, round(s, 3)


def _vals(data, H, R, n, off, w, fmt):
    k = min(n, 3000)
    return [struct.unpack_from(fmt, data, H + i * R + off)[0] for i in range(k)]


def _printable(b): return 32 <= b < 127


def _plausible_float(v):
    return math.isfinite(v) and (v == 0 or 1e-6 < abs(v) < 1e12)


def _smooth(v):
    ok = sum(abs(v[i + 1] - v[i]) <= 0.2 * max(abs(v[i]), 1e-9) for i in range(len(v) - 1))
    return _plausible_ok(v) and ok / max(1, len(v) - 1) > 0.9


def _plausible_ok(v): return sum(_plausible_float(x) for x in v) / len(v) >= 0.97


def _sorted_frac(v):
    return sum(v[i] <= v[i + 1] for i in range(len(v) - 1)) / max(1, len(v) - 1)


def infer_fields(data, H, R, n, endian=None):
    """Walk across the record and name each stretch. Returns (fields, endian, votes)."""
    k = min(n, 3000)
    cols = [[data[H + i * R + c] for i in range(k)] for c in range(R)]
    const = [len(set(c)) == 1 for c in cols]
    zero = [const[c] and cols[c][0] == 0 for c in range(R)]
    pfrac = [sum(_printable(b) for b in cols[c]) / k for c in range(R)]
    votes = {"<": 0, ">": 0}
    out, off = [], 0
    def get(w, ch, e):
        return [struct.unpack_from(e + ch, data, H + i * R + off)[0] for i in range(k)]
    while off < R:
        # 1. text: printable columns (constants allowed), then any zero padding
        j = off
        while j < R and pfrac[j] >= 0.8: j += 1
        if j - off >= 3 and not all(zero[off:j]):
            while j < R and zero[j]: j += 1
            out.append(dict(off=off, size=j - off, kind="text", note="printable text, zero padded")); off = j; continue
        done = False
        for w, ch, kind in ((4, "I", "timestamp"), (8, "d", "float64"), (4, "f", "float32")):
            if off + w > R or sum(not const[off + t] for t in range(w)) < 2: continue
            for e in ("<", ">"):
                lowc = {("float64", "<"): range(off, off + 3), ("float64", ">"): range(off + 5, off + 8), ("float32", "<"): [off], ("float32", ">"): [off + 3]}.get((kind, e))
                if lowc is not None and all(const[c] for c in lowc): continue
                v = get(w, ch, e)
                if kind == "timestamp":
                    good = sum(946684800 <= x <= 2208988800 for x in v) / k >= 0.95 and len(set(v)) > 1 and _sorted_frac(v) >= 0.9
                    if good:
                        d = [v[i + 1] - v[i] for i in range(k - 1)]
                        mode_share = max(d.count(x) for x in set(d)) / len(d)
                        if mode_share < 0.3 and off + 8 <= R:
                            alt = get(8, "d", e)
                            if _smooth(alt): good = False     # more likely the top half of a smooth decimal number
                elif kind == "float64":
                    good = sum(_plausible_float(x) for x in v) / k >= 0.97 and len(set(v)) > 1 and sum(x != 0 for x in v) / k > 0.5
                    if good:
                        hl = [struct.unpack_from(e + "f", data, H + i * R + off + (0 if e == "<" else 0))[0] for i in range(k)]
                        hh = [struct.unpack_from(e + "f", data, H + i * R + off + 4)[0] for i in range(k)]
                        if sum(_plausible_float(x) for x in hl) / k >= 0.97 and sum(_plausible_float(x) for x in hh) / k >= 0.97: good = False  # two float32 side by side
                else:
                    good = sum(_plausible_float(x) for x in v) / k >= 0.97 and len(set(v)) > 1 and sum(x != 0 for x in v) / k > 0.5
                if good:
                    votes[e] += 1
                    out.append(dict(off=off, size=w, kind=kind, endian=e, note="Unix time in seconds, steadily increasing" if kind == "timestamp" else "plausible decimal values"))
                    off += w; done = True; break
            if done: break
        if done: continue
        # whole numbers. Count the varying bytes plus the always-zero bytes beside them, then pick 1, 2 or 4 wide.
        zb = 0
        while off + zb < R and zero[off + zb] and zb < 3: zb += 1          # zero bytes first: big endian
        vr = 0
        while off + zb + vr < R and not const[off + zb + vr] and pfrac[off + zb + vr] < 0.8 and vr < 4: vr += 1
        za = 0
        while off + zb + vr + za < R and zero[off + zb + vr + za] and zb == 0 and za < 3: za += 1   # zero bytes after: little endian
        if vr == 0:
            # only constant bytes here
            j = off
            while j < R and const[j] and pfrac[j] < 0.8: j += 1
            if j == off: j = off + 1
            out.append(dict(off=off, size=j - off, kind="constant", note=f"constant bytes (first value {cols[off][0]:#04x})")); off = j; continue
        total = zb + vr + za
        width = 1 if total == 1 else (2 if total == 2 else 4)
        while width > R - off: width //= 2
        if width == 1: e = "<"
        elif zb: e = ">"
        elif za: e = "<"
        else:
            eb = entropy(bytes(cols[off])); el = entropy(bytes(cols[off + width - 1]))
            e = ">" if eb < el else "<"
        if width > 1: votes[e] += 1
        note = "single byte (flag, small number or code)" if width == 1 else ("whole number; the always-zero bytes mean the true width may be smaller" if (zb or za) else "whole number")
        out.append(dict(off=off, size=width, kind={1: "uint8", 2: "uint16", 4: "uint32"}[width], endian=e, note=note))
        off += width
    names = {}
    for f in out:
        base = {"constant": "pad", "text": "text", "timestamp": "time"}.get(f["kind"], f["kind"].replace("uint", "u").replace("float", "f"))
        names[base] = names.get(base, 0) + 1
        f["name"] = f"{base}_{names[base] - 1}"
    maj = ">" if votes[">"] > votes["<"] else "<"
    return out, maj, votes


STRUCT = {"float64": "d", "float32": "f", "timestamp": "I", "uint32": "I", "uint16": "H", "uint8": "B"}


def confidence(score, n, fields):
    typed = sum(f["size"] for f in fields if f["kind"] not in ("constant", "uint8"))
    tot = sum(f["size"] for f in fields) or 1
    c = score * 0.6 + min(n, 200) / 200 * 0.2 + typed / tot * 0.2
    return "high" if c > 0.8 and n >= 20 else ("medium" if c > 0.55 else "low")


def analyse(data, name="file"):
    r = {"name": name, "size": len(data), "known_format": known_format(data),
         "entropy": round(entropy(data[:65536]), 2), "layout": None, "fields": [], "limits": []}
    if r["known_format"]:
        r["limits"].append(f"Looks like a known format: {r['known_format']}. Use a tool made for it; BlackBox only guesses fixed-size record files.")
        return r
    if r["entropy"] > 7.5:
        r["limits"].append(f"Entropy {r['entropy']} of 8: the bytes look compressed or encrypted, so no layout can be guessed.")
        return r
    if len(set(data)) <= 2 or r['entropy'] < 0.3:
        r['limits'].append('Almost every byte is the same (empty or zero-filled). Nothing to learn from it.')
        return r
    lay = find_layout(data)
    if not lay:
        r["limits"].append("No repeating record size found. The file may be variable-length, text, or not record-based.")
        return r
    H, R, n, s = lay
    fields, endian, votes = infer_fields(data, H, R, n)
    r["layout"] = dict(header_size=H, record_size=R, records=n, regularity=s, endian=endian)
    r["header_hex"] = data[:H].hex()
    r["fields"] = fields
    r["confidence"] = confidence(s, n, fields)
    if H == 0: r["limits"].append("Header size 0 was chosen. A header whose size is a multiple of the record size looks like a few extra records at the start; check the first rows.")
    r["limits"].append("These are guesses from patterns, not knowledge of the format. Check a few rows against the real thing.")
    if n < 20: r["limits"].append(f"Only {n} records: a small sample makes every guess weaker.")
    return r
