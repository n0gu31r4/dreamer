#!/usr/bin/env python
"""Live smoke test for the local SDXL provider. NOT part of the gate.

Runs one sprite through the full loop against a *local* ComfyUI server (SDXL
base + Pixel Art XL LoRA + rembg) — free, no API key, no money. You must have
the server up first:

    ~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188

Then, from the workspace root:

    uv run --package asset-pipeline python packages/asset-pipeline/scripts/smoke_local.py [OUT_DIR]

It runs one sprite (generate -> postprocess -> checks -> stub vision judge),
writes the PNG plus its Godot `.import` sidecar into OUT_DIR (default:
./_smoke_out), and prints the provenance ledger. Uses the same goblin spec as
smoke_live.py so you can eyeball local_sd vs gpt-image on identical input.

Remember: the sidecar sets lossless/no-mipmaps/detect-3d-off, but crisp scaling
also needs the project setting below set once in the consuming Godot project.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from asset_pipeline.godot_import import FILTER_PROJECT_SETTING, write_import_file
from asset_pipeline.manifest import AssetSpec
from asset_pipeline.pipeline import run_asset
from asset_pipeline.providers.local_sd import LocalSDProvider
from asset_pipeline.qa import StubJudge
from asset_pipeline.style_bible import StyleBible

HOST, PORT = "127.0.0.1", 8188

# DawnBringer 16 — a classic, versatile 16-color pixel-art palette (greens,
# browns, greys, skin, red, dark outline). A 6-color palette is too small to
# hold a detailed character; 16 keeps the "limited palette" look while letting
# a sprite actually read. See the package README note on size + palette.
DB16 = (
    "#140C1C", "#442434", "#30346D", "#4E4A4E", "#854C30", "#346524",
    "#D04648", "#757161", "#597DCE", "#D27D2C", "#8595A1", "#6DAA2C",
    "#D2AA99", "#6DC2CA", "#DAD45E", "#DEEED6",
)

BIBLE = StyleBible(
    name="smoke",
    version=1,
    palette=DB16,
    grid=16,
    background="transparent",
    prompt_fragments={
        "base": "pixel art, crisp pixels, no anti-aliasing, limited palette",
        "sprite": "single character, full body, centered, front-facing",
    },
)

# 96x96: a detailed-sprite size that actually holds a character. At 32x32 the
# cut-out subject fills ~15px and reads as a blob — too small for a hero sprite.
SPEC = AssetSpec(
    id="smoke_goblin_local",
    category="sprite",
    size=(96, 96),
    description="a small friendly green goblin with a wooden club",
)


def _server_up() -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/system_stats", timeout=3):
            return True
    except OSError:
        return False


def main(argv: list[str]) -> int:
    if not _server_up():
        print(f"No ComfyUI server at http://{HOST}:{PORT}. Launch it first:")
        print("  ~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188")
        return 2

    out_dir = Path(argv[1]) if len(argv) > 1 else Path("_smoke_out")

    print(f"Generating {SPEC.id!r} via local SDXL + Pixel Art XL into {out_dir}/ ...")
    status, provenance = run_asset(
        SPEC, BIBLE, LocalSDProvider(host=HOST, port=PORT), StubJudge(), out_dir
    )

    print(f"\nstatus: {status}")
    print(json.dumps(provenance, indent=2))

    if status == "passed":
        png = Path(provenance["file"])
        sidecar = write_import_file(png)
        print(f"\nwrote {png} and {sidecar.name}")
        setting, value = FILTER_PROJECT_SETTING
        print(
            f"reminder: in the Godot project set `{setting} = {value}` (Nearest) "
            "for crisp scaling — the sidecar can't carry filtering."
        )
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
