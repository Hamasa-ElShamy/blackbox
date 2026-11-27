# Changelog

## 0.3 (unreleased)

- Signed whole numbers: 16 and 32 bit fields whose top byte is mostly 0x00 or 0xFF are reported as `int16` / `int32`, and the generated reader uses the signed struct code. Accelerometer-style test layout: 0 of 20 fields right before, 20 of 20 after.
- Fields next to each other: a busy byte followed by a quiet one now splits a run into 16-bit fields instead of one 32-bit field.
- Decimal check: a 64-bit decimal is rejected when two of its three lowest bytes never change (two other numbers side by side looked like one decimal).
- Honest numbers: realistic layouts 77 to 101 of 155 fields right (50% to 65%). On 60 new random layouts 113 to 126 of 269 (42% to 47%). Layout detection did not change (29 of 30, and 56 of 60 on the new seeds).
- Repo: compiled Python files were committed by mistake. Removed them and added `.gitignore`.
- Two new tests for signed and unsigned values.

## 0.2

- Faster, more accurate record-size search (30 of 60 to 53 of 60 layouts), clean file errors, realistic-layout benchmark.
