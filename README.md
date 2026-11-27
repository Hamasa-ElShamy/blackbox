# BlackBox

[![tests](https://github.com/mohamed-elshamy-ai/blackbox/actions/workflows/tests.yml/badge.svg)](https://github.com/mohamed-elshamy-ai/blackbox/actions/workflows/tests.yml)

Guess the layout of an unknown binary data file, and get a Python reader for it. You give it a file made of fixed-size records (a sensor log, a save file, an old database dump). It guesses the header size, the record size and what each field holds (Unix time, decimal number, whole number, text), shows a colour map of every byte, and writes a small standalone Python script that reads the file into CSV.

**Try it in your browser, nothing is uploaded:** https://mohamed-elshamy-ai.github.io/blackbox/ (loads Python via Pyodide, about 10 MB the first time, from jsDelivr).

It is a guessing tool. Every result is a hypothesis from patterns, not knowledge of the format.

## Worked example

The sample files are made by [`demo/mk.py`](demo/mk.py), so the true layout is known. They are not files from the wild. Sensor log: a 4-byte header `SNS1`, then 300 records of `uint32 time, float32 temperature, float32 humidity, uint16 id, uint8 flags, 1 pad byte, 8-byte room name`.

```
$ blackbox demo/sensor.bin --reader reader.py
FILE: demo/sensor.bin  (7204 bytes, entropy 5.64/8)
LAYOUT GUESS (high confidence): header 4 bytes, then 300 records of 24 bytes (regularity 0.69)
 offset size  type       byte order note
      0    4  timestamp  little     Unix time in seconds, steadily increasing
      4    4  float32    little     plausible decimal values
      8    4  float32    little     plausible decimal values
     12    2  uint16     little     whole number; the always-zero bytes mean the true width may be smaller
     14    2  uint16     little     whole number; the always-zero bytes mean the true width may be smaller
     16    8  text       -          printable text, zero padded
$ python3 reader.py demo/sensor.bin
time_0,f32_0,f32_1,u16_0,u16_1,text_0
1700000060,20.67182159423828,56.948673248291016,3,1,room1
1700000120,22.477174758911133,48.98982238769531,12,1,room1
```

Header size, record size, and every field boundary are right. One miss: the `uint8` flags byte and the pad byte after it are reported as one `uint16`, because a byte that is always zero next to a varying byte looks like the top of a number. The GPS sample (big-endian `float64` latitude and longitude, two `uint16`) comes out exactly right ([`demo/gps-output.txt`](demo/gps-output.txt)).

## Install and use

```
git clone https://github.com/mohamed-elshamy-ai/blackbox && cd blackbox
pip install .
blackbox some.bin                       # print the guess
blackbox some.bin --reader reader.py    # also write a Python reader
blackbox some.bin --json                # machine-readable
```

Standard library only, Python 3.9 or newer. At most the first 8 MB are analysed (`--max-mb`).

| System | Status |
|---|---|
| Linux | Tested (Python 3.10). |
| Windows / macOS | Should work (pure Python), not tested. |

## How it works

1. Refuse early: known formats (PNG, ZIP, PDF, ELF and a few more, by magic bytes), compressed or encrypted data (entropy above 7.5 of 8), and files with almost no variation.
2. Layout: for every record size from 2 to 512 and header size up to 128 where the file length divides evenly, score how regular the byte columns are (low entropy per column, similar neighbours). Take the smallest size that scores nearly as well as the best.
3. Fields: walk across one record and try, in order: text, Unix time (steadily increasing, 2000 to 2040), 64-bit and 32-bit decimals (plausible magnitudes, not two 32-bit numbers side by side), then whole numbers of 1, 2 or 4 bytes using always-zero bytes as the hint. Both byte orders are tried.
4. Write a reader with `struct`.

No AI model. Each decision is a rule you can read in [`blackbox/core.py`](blackbox/core.py).

## Measured accuracy, and its limits

[`demo/bench.py`](demo/bench.py) builds random layouts (3 to 7 fields, random types and byte order, header 0 to 16 bytes, 100 to 1000 records) so the truth is known, then checks the guess. Output in [`demo/bench-output.txt`](demo/bench-output.txt):

- Header size and record size exactly right: **30 of 60 files**.
- Field offset and type exactly right, counted only in files where the layout was right: **80 of 173 fields (46%)**.

That test is harsh on purpose: numbers are uniformly random, so there is little pattern to find, and very short records (for example 6 bytes) are often missed. Real files with smoother data usually do better, but I have not measured that on real third-party files, so I do not claim it. Run on `/var/log/lastlog` (a real file, almost all zero bytes) it correctly says there is nothing to learn.

## Limitations

- Fixed-size records only. No variable-length fields, pointers or bit fields.
- Signed and unsigned are not told apart. A small whole number can be reported wider than it is. A timestamp can be taken for a decimal number and the reverse.
- A text header whose size is a multiple of the record size looks like a few extra records (the tool notes when it picked header size 0).
- Unusual encodings (BCD, packed dates, 24-bit values, 128-bit values) are not understood.
- It cannot tell you what a field means, only its likely type.

## Related tools

[Kaitai Struct](https://kaitai.io/) and [ImHex](https://imhex.werwolv.net/) are for when you already know or are working out the format by hand; they are far more capable. [binwalk](https://github.com/ReFirmLabs/binwalk) finds known files and compression inside firmware. BlackBox covers one narrow job: a first guess at a fixed-record layout, quickly, with a reader you can edit.

## Tests

`pytest`: 7 tests (layout and field types on two known layouts, generated reader round trip, refusal of known formats, random data and zero files, command line).

## License

MIT.
