#!/usr/bin/env python3
"""Super Taiwanese Baseball League (Super A'Can) English build.

The game's own text routine draws Big5 characters (16 px) and ASCII (8 px) from the same string,
so every string is rewritten in place as ASCII: one Chinese character = two letters = same width.
The ASCII font gains U V u v ! ? & " (the original set has no U or V). Player names are reached
through pointers and are rewritten into free space.

Reads `Super Taiwanese Baseball League (Taiwan).bin` next to this project's README; writes
build/Super Taiwanese Baseball League (EN).bin + .ips.
"""
import json, re, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM_IN = ROOT / "Super Taiwanese Baseball League (Taiwan).bin"
OUT_BIN = ROOT / "build" / "Super Taiwanese Baseball League (EN).bin"
OUT_IPS = ROOT / "build" / "Super Taiwanese Baseball League (EN).ips"

ASCII_TABLE, ASCII_GLYPHS, ASCII_COUNT = 0x1FFA22, 0x1FFAB2, 72
FREE, FREE_END = 0x07D100, 0x07F19B           # all zeros in the original
NAMES = (0x1EB000, 0x1EF000)                  # roster name area (records point into it)
BIG5_COUNT, BIG5_TABLE, BIG5_GLYPHS = 0x1F1100, 0x1F1102, 0x1F17DE   # sorted codes + 16x16 glyphs
ROM_SIZE, BIG5_NEW = 0x300000, 0x200000       # the Big5 font moves to the new third megabyte
# Strings drawn by routines that take 2 bytes per character (e.g. the title menu draws each
# character as its own sprite): their English is stored as 16x16 glyphs of two letters each.
PAIR_STRINGS = {0x01B12A, 0x01B132, 0x01B13A}

# New 8x16 glyphs in the font's style (rows 0-15, '#' = ink)
NEW = {
    "U": ["", "", "", ".##...##", ".##...##", ".##...##", ".##...##", ".##...##", ".##...##", ".##...##", "..##.##.", "...###..", "", "", "", ""],
    "V": ["", "", "", ".##...##", ".##...##", ".##...##", ".##...##", "..##.##.", "..##.##.", "..##.##.", "...###..", "....#...", "", "", "", ""],
    "u": ["", "", "", "", "", "", ".##...##", ".##...##", ".##...##", ".##...##", ".##..###", "..###.##", "", "", "", ""],
    "v": ["", "", "", "", "", "", ".##...##", ".##...##", "..##.##.", "..##.##.", "...###..", "....#...", "", "", "", ""],
    "!": ["", "", "", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "........", "...##...", "...##...", "", "", "", ""],
    "?": ["", "", "", "..####..", ".##..##.", ".....##.", "....##..", "...##...", "...##...", "........", "...##...", "...##...", "", "", "", ""],
    "&": ["", "", "", "..###...", ".##.##..", ".##.##..", "..###...", ".###.##.", "##.###..", "##..##..", "##.####.", ".###..##", "", "", "", ""],
    '"': ["", "", "", ".##.##..", ".##.##..", ".#..#...", "", "", "", "", "", "", "", "", "", ""],
}


def swap16(b):
    b = bytearray(b); b[0::2], b[1::2] = b[1::2], b[0::2]; return b


def cstr(rom, a):
    j = a
    while rom[j]:
        j += 1
    return bytes(rom[a:j])


def main():
    rom = bytearray(swap16(ROM_IN.read_bytes()))
    rom += bytes(ROM_SIZE - len(rom))
    free = FREE

    # 1. ASCII font: copy table + glyphs, append the new characters, repoint the 4 lookups
    codes = list(struct.unpack_from(">%dH" % ASCII_COUNT, rom, ASCII_TABLE))
    glyphs = bytearray(rom[ASCII_GLYPHS:ASCII_GLYPHS + 16 * ASCII_COUNT])
    for ch, rows in NEW.items():
        assert ord(ch) not in codes
        codes.append(ord(ch))
        glyphs += bytes(int(r.ljust(8, ".").replace("#", "1").replace(".", "0"), 2) if r else 0 for r in rows)
    table_at, glyph_at = free, free + 2 * len(codes)
    struct.pack_into(">%dH" % len(codes), rom, table_at, *codes)
    rom[glyph_at:glyph_at + len(glyphs)] = glyphs
    free = (glyph_at + len(glyphs) + 15) & ~15
    for site in [m.start() for m in re.finditer(re.escape(struct.pack(">I", ASCII_TABLE)), bytes(rom[:0x100000]))]:
        assert rom[site - 6:site - 2] == bytes.fromhex("48780048") and rom[site - 2:site] == bytes.fromhex("2f3c")
        struct.pack_into(">H", rom, site - 4, len(codes))
        struct.pack_into(">I", rom, site, table_at)
    sites = [m.start() for m in re.finditer(re.escape(struct.pack(">I", ASCII_GLYPHS)), bytes(rom[:0x100000]))]
    assert len(sites) == 4
    for site in sites:
        struct.pack_into(">I", rom, site, glyph_at)
    allowed = {chr(c) for c in codes}
    print(f"Font: {len(codes)} ASCII glyphs (+{len(NEW)}) at ${table_at:06X}")

    def check(s, where):
        bad = set(s) - allowed
        assert not bad, f"{where}: no glyph for {bad}"

    # 1b. two-letter 16x16 glyphs (left half, right half = two 8x16 letters) appended to the Big5 font
    bcount = struct.unpack_from(">H", rom, BIG5_COUNT)[0]
    bcodes = list(struct.unpack_from(">%dH" % bcount, rom, BIG5_TABLE))
    bglyphs = bytearray(rom[BIG5_GLYPHS:BIG5_GLYPHS + 32 * bcount])
    letter = {chr(c): bytes(glyphs[16 * i:16 * i + 16]) for i, c in enumerate(codes)}
    pair_code = {}

    def pair(two):
        if two not in pair_code:
            k = len(pair_code)
            code = 0xF940 + (k // 0xBE) * 0x100 + k % 0xBE   # after the last code ($F8CA), bytes $40-$FD
            pair_code[two] = code
            bcodes.append(code)
            bglyphs.extend(letter[two[0]] + letter[two[1]])
        return pair_code[two]

    # 2. strings, in place
    S = json.loads((ROOT / "notes" / "strings_en.json").read_text(encoding="utf-8"))
    for key, en in S.items():
        if key.startswith("_"):
            continue
        a = int(key, 16)
        old = cstr(rom, a)
        assert any(b >= 0x81 for b in old), f"{key}: not a Big5 string"
        assert len(en) <= len(old), f"{key}: {en!r} longer than {len(old)} bytes"
        check(en, key)
        if a in PAIR_STRINGS:
            en = en.ljust(len(old))
            assert len(old) % 2 == 0
            rom[a:a + len(old)] = b"".join(struct.pack(">H", pair(en[i:i + 2])) for i in range(0, len(en), 2))
        else:
            rom[a:a + len(old)] = en.ljust(len(old)).encode()
    print(f"Strings: {sum(1 for k in S if not k.startswith('_'))} in place")

    # 3. player names: every record pointer into the name area -> new English string
    N = json.loads((ROOT / "notes" / "names_en.json").read_text(encoding="utf-8"))
    refs = {}
    for k in range(0x1E0000, 0x1F0000, 2):
        p = struct.unpack_from(">I", rom, k)[0]
        if NAMES[0] <= p < NAMES[1]:
            try:
                zh = cstr(rom, p).decode("big5")
            except UnicodeDecodeError:
                continue
            if zh in N:
                refs.setdefault(p, []).append(k)
    new_at = {}
    for p in sorted(refs):
        en = N[cstr(rom, p).decode("big5")]
        assert len(en) <= 8, en
        check(en, en)
        if en not in new_at:
            new_at[en] = free
            rom[free:free + len(en) + 1] = en.encode() + b"\0"
            free = (free + len(en) + 2) & ~1
        for k in refs[p]:
            struct.pack_into(">I", rom, k, new_at[en])
    assert free <= FREE_END, hex(free)
    missing = sorted({z for z in N if not z.startswith("_")} - {cstr(rom, p).decode("big5") for p in refs})
    print(f"Names: {len(refs)} name strings, {sum(len(v) for v in refs.values())} pointers, free space used to ${free:06X}")
    if missing:
        print("  (not found in records:", " ".join(missing), ")")

    # 4. Big5 font copy with the pair glyphs, at $200000; repoint count / table / glyph references
    assert bcodes == sorted(bcodes)
    at = BIG5_NEW
    struct.pack_into(">H", rom, at, len(bcodes))
    struct.pack_into(">%dH" % len(bcodes), rom, at + 2, *bcodes)
    g_at = at + 2 + 2 * len(bcodes)
    rom[g_at:g_at + len(bglyphs)] = bglyphs
    for old, new in ((BIG5_COUNT, at), (BIG5_TABLE, at + 2), (BIG5_GLYPHS, g_at)):
        sites = [m.start() for m in re.finditer(re.escape(struct.pack(">I", old)), bytes(rom[:0x100000]))]
        assert sites, hex(old)
        for site in sites:
            struct.pack_into(">I", rom, site, new)
    print(f"Big5 font: {bcount} + {len(pair_code)} two-letter glyphs at ${at:06X}")

    OUT_BIN.parent.mkdir(exist_ok=True)
    OUT_BIN.write_bytes(bytes(swap16(rom)))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from create_ips import create_ips_patch
    create_ips_patch(str(ROM_IN), str(OUT_BIN), str(OUT_IPS))


if __name__ == "__main__":
    main()
