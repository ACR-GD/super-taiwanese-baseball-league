# Super Taiwanese Baseball League (超級中華職棒聯盟, Super A'Can) — English Translation

## How to Play

| Patch | Apply to | Result |
|---|---|---|
| `build/Super Taiwanese Baseball League (EN).ips` | `Super Taiwanese Baseball League (Taiwan).bin` / MAME `staiwbbl` (2,097,152 bytes, CRC32 `ccf6829b`, SHA-1 `17a413803d8749fbe9643ca56d703afd64569b9f`) | 3,145,728 bytes |

The patch grows the ROM to 3 MB: the game's 16×16 font moves to the third megabyte (`$200000`).

- **Repo emulator:** open the patched file.
- **MAME:** load it as a loose cartridge, byte-swapped as usual for loose files:
  `mame supracan -cart "Super Taiwanese Baseball League (EN).bin"`. The `staiwbbl` software-list entry
  is 2 MB, so MAME would cut the file.

## Status

In English: the title menu, every text string (menus, options, controls help, game results,
leaderboards, standings, stat labels, staff credits), all 263 player names, team abbreviations,
stadiums. Names are given-name initials + Wade-Giles surname for Taiwanese players ("PS Cheng"),
English names for foreign players; some Japanese guest-team names are best guesses.

Still Chinese (pre-drawn graphics, not text): the title logo, the scoreboard's team mascot
characters and inning, the 投手 / 球 tags in the batter/pitcher panels and the 今日成績 box title.
Tested in the repo emulator: title menu and the attract-mode game (the emulator does not register
menu input for this game, so deeper screens were not reached).

## Build

Put your own dump next to this README, then `python3 tools/build_en.py` (Python 3 only).

- `notes/strings_en.json`: in-place English for each Big5 string (address → English). One Chinese
  character is 2 bytes = two 8-pixel letters, so the width on screen stays the same.
- `notes/names_en.json`: player names (Big5 → English, ≤ 8 characters).

Only `tools/build_en.py` and `tools/create_ips.py` are used; the other scripts and files in this
folder are from an earlier attempt.

## ROM notes (68k addresses)

- Strings are NUL-terminated Big5 + ASCII; the game's dispatcher (`$4951A`) draws Big5 codes from a
  sorted 878-code table (count `$1F1100`, codes `$1F1102`, 16×16 glyphs `$1F17DE`: left 8×16 half then
  right half) and ASCII from a 72-character 8×16 font (`$1FFA22` / `$1FFAB2`, no U or V).
- The build copies the ASCII font to `$7D100` with U V u v ! ? & " added and repoints its four
  lookups; it copies the Big5 font to `$200000` and appends "two-letter" 16×16 glyphs for strings drawn
  two bytes at a time (the title menu draws each character as a separate sprite, `$49E1E`).
- Player names are reached through pointers in 46-byte player records; the English names live in the
  free area after the ASCII font.

## License

The tools, fonts and patch are MIT-licensed (see `LICENSE`). The game itself is not included;
you need your own dump.
