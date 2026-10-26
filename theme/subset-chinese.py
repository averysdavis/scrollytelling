"""Cut the Chinese fonts down to the characters the stories use.

Source Han Serif SC and TC are 24 MB each, far too much to send to
readers, so this writes a WOFF2 of each holding only the Chinese
characters found in the site's .qmd files. It runs before every render (pre-render in _quarto.yml), so
new Chinese text is picked up automatically.

Needs fontTools with brotli (pipx install fonttools; pipx inject
fonttools brotli). Without it the last subset is kept and the render
carries on, so commit the theme/fonts/zh-*-subset.woff2 files.
"""

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "theme/fonts"
# Simplified is the default; text tagged lang="zh-Hant" uses Traditional
SUBSETS = {
    FONTS / "SourceHanSerifSC-Regular.otf": FONTS / "zh-sc-subset.woff2",
    FONTS / "SourceHanSerifTC-Regular.otf": FONTS / "zh-tc-subset.woff2",
}

# Keep in step with the unicode-range of the @font-faces in site-theme.css
RANGES = [
    (0x00B7, 0x00B7),  # middle dot
    (0x2014, 0x2026),  # em dash, curly quotes, ellipsis
    (0x2E80, 0x9FFF),  # radicals, CJK punctuation, kana, unified ideographs
    (0xF900, 0xFAFF),  # compatibility ideographs
    (0xFE30, 0xFE4F),  # vertical forms
    (0xFF00, 0xFFEF),  # full-width punctuation and forms
    (0x20000, 0x2FA1F),  # extension ideographs
]


def wanted(ch):
    return any(lo <= ord(ch) <= hi for lo, hi in RANGES)


chars = set()
for qmd in ROOT.rglob("*.qmd"):
    if "_site" in qmd.parts or "_extensions" in qmd.parts:
        continue
    chars.update(ch for ch in qmd.read_text(encoding="utf-8") if wanted(ch))

pyftsubset = shutil.which("pyftsubset")
if pyftsubset is None:
    print("subset-chinese: pyftsubset not found, keeping the existing subset", file=sys.stderr)
    sys.exit(0)

unicodes = ",".join(f"U+{ord(ch):04X}" for ch in sorted(chars)) or "U+3000"
for source, output in SUBSETS.items():
    subprocess.run(
        [
            pyftsubset,
            str(source),
            f"--unicodes={unicodes}",
            "--layout-features=*",
            "--flavor=woff2",
            f"--output-file={output}",
        ],
        check=True,
    )
    print(f"subset-chinese: {output.name}, {len(chars)} characters, {output.stat().st_size // 1024} KB")
