import os, struct, subprocess, sys, random, importlib.util
from blackbox import core, gen

random.seed(7)


def sensor(n=300):
    t, rec = 1700000000, []
    for _ in range(n):
        t += 60
        rec.append(struct.pack("<IffHBx8s", t, 20 + random.random() * 5, 40 + random.random() * 20, random.choice([3, 7, 12]), random.choice([0, 1, 4]), b"room%d" % random.randint(1, 3)))
    return b"SNS1" + b"".join(rec)


def gps(n=500):
    lat, lon, rec = 30.0, 31.0, []
    for _ in range(n):
        lat += random.random() * 1e-3; lon += random.random() * 1e-3
        rec.append(struct.pack(">ddHH", lat, lon, random.randint(0, 120), random.randint(0, 359)))
    return b"".join(rec)


def kinds(r): return [(f["off"], f["size"], f["kind"]) for f in r["fields"]]


def test_sensor_layout_and_types():
    r = core.analyse(sensor())
    assert (r["layout"]["header_size"], r["layout"]["record_size"], r["layout"]["records"]) == (4, 24, 300)
    k = kinds(r)
    assert k[0] == (0, 4, "timestamp") and (4, 4, "float32") in k and (8, 4, "float32") in k and (16, 8, "text") in k


def test_gps_big_endian_doubles():
    r = core.analyse(gps())
    assert (r["layout"]["header_size"], r["layout"]["record_size"]) == (0, 20)
    assert kinds(r)[:2] == [(0, 8, "float64"), (8, 8, "float64")] and r["fields"][0]["endian"] == ">"


def test_generated_reader_round_trips(tmp_path):
    data = sensor(); p = tmp_path / "s.bin"; p.write_bytes(data)
    r = core.analyse(data, str(p)); src = tmp_path / "reader.py"; src.write_text(gen.reader_source(r, "s.bin"))
    spec = importlib.util.spec_from_file_location("reader", src); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    rows = list(m.read(str(p)))
    assert len(rows) == 300 and rows[0]["time_0"] == 1700000060 and rows[0]["text_0"].startswith("room")


def test_known_format_is_refused():
    r = core.analyse(b"\x89PNG\r\n\x1a\n" + os.urandom(500))
    assert r["layout"] is None and "PNG" in r["limits"][0]


def test_random_data_is_refused():
    assert core.analyse(os.urandom(20000))["layout"] is None


def test_zero_file_is_refused():
    r = core.analyse(bytes(5000)); assert r["layout"] is None and "zero" in r["limits"][0]


def test_cli_runs(tmp_path):
    p = tmp_path / "s.bin"; p.write_bytes(sensor())
    out = subprocess.run([sys.executable, "-m", "blackbox.cli", str(p)], capture_output=True, text=True).stdout
    assert "LAYOUT GUESS" in out and "timestamp" in out
