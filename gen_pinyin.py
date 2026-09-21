#!/usr/bin/env python3
"""Generate pinyin_data.js from opencc-pinyin/pinyin.txt for the 8105 規範字."""
import json, os, sys

script_dir = os.path.dirname(os.path.abspath(__file__))
pinyin_txt = os.path.join(script_dir, "../opencc-pinyin/pinyin.txt")
chars_json = sys.argv[1] if len(sys.argv) > 1 else "/tmp/chars.json"
out_path   = os.path.join(script_dir, "pinyin_data.js")

with open(chars_json, encoding="utf-8") as f:
    chars = json.load(f)

lookup = {}
with open(pinyin_txt, encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 2:
            lookup[parts[0]] = parts[1].split(" ")

out = {}
missing = []
for c in chars:
    if c in lookup:
        out[c] = lookup[c]
    else:
        missing.append(c)

if missing:
    print(f"WARNING: {len(missing)} chars not found in pinyin.txt:", "".join(missing[:20]), file=sys.stderr)

with open(out_path, "w", encoding="utf-8") as f:
    f.write("window.PINYIN=")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";")

print(f"Generated {out_path}: {len(out)} entries, {os.path.getsize(out_path)} bytes")
