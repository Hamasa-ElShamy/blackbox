# blackbox build notes (internal, not for repo)
State: core.py written (layout finder works: sensor.bin R=24 H=4 correct, gps.bin R=20 H=0 correct). Field inference still wrong in demo/mk.py samples:
- sensor: ts(u32)+f32 get read as float64 at off 4. Fix: before accepting float64, if both 4-byte halves are plausible float32, prefer two float32.
- gps (BE float64 lat/lon): high word looks like an increasing BE timestamp. Fix idea: require smoothness (mean |dv|/|v| < ~0.2) for float64 over timestamp; or check float64 BE/LE before timestamp when value smooth.
- TODO: generator (reader.py output), cli, tests, hex-map demo page (Pyodide, JS map from analysis JSON), 60 s demo video via playwright + ffmpeg, README (EN), site AR/EN, DESIGN.md, repo create, Pages, real-file test (/var/log/wtmp, /var/log/lastlog).
- Not yet created on GitHub. Nothing pushed.
