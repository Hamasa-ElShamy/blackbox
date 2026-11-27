import argparse, json, sys
from . import core, gen


def render(r):
    L = [f"FILE: {r['name']}  ({r['size']} bytes, entropy {r['entropy']}/8)"]
    if r["layout"]:
        y = r["layout"]
        L.append(f"LAYOUT GUESS ({r['confidence']} confidence): header {y['header_size']} bytes, then {y['records']} records of {y['record_size']} bytes (regularity {y['regularity']})")
        L.append(f"{'offset':>7} {'size':>4}  {'type':<10} {'byte order':<10} note")
        order = {"<": "little", ">": "big"}
        for f in r["fields"]:
            L.append(f"{f['off']:>7} {f['size']:>4}  {f['kind']:<10} {order.get(f.get('endian'), '-'):<10} {f['note']}")
    for l in r["limits"]: L.append("NOTE: " + l)
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="blackbox", description="Guess the layout of an unknown fixed-record binary file and write a Python reader for it.")
    ap.add_argument("file"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--reader", metavar="OUT.py", help="write a generated Python reader to this file")
    ap.add_argument("--max-mb", type=float, default=8, help="analyse at most this much of the file (default 8)")
    o = ap.parse_args(argv)
    try:
        with open(o.file, "rb") as fh: data = fh.read(int(o.max_mb * 1e6))
    except OSError as e: sys.exit(f"blackbox: cannot read '{o.file}': {e.strerror or e}")
    r = core.analyse(data, o.file)
    if o.json: print(json.dumps(r, indent=1)); return
    print(render(r))
    if o.reader:
        if not r["layout"]: sys.exit("no layout found, nothing to write")
        try: open(o.reader, "w").write(gen.reader_source(r, o.file))
        except OSError as e: sys.exit(f"blackbox: cannot write '{o.reader}': {e.strerror or e}")
        print(f"wrote {o.reader}")


if __name__ == "__main__":
    main()
