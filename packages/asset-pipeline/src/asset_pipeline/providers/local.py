"""Local-file provider: reads pre-made PNGs from a directory as if generated.

Makes the pipeline runnable end-to-end offline — for tests, for hand-drawn
assets, and for replaying previously generated files through new checks.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from . import GenerationRequest, GenerationResult, compile_prompt


class LocalFileProvider:
    name = "local"

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        path = self.directory / f"{request.spec.id}.png"
        if not path.exists():
            raise FileNotFoundError(
                f"local provider: no file for asset {request.spec.id!r} at {path}"
            )
        prompt = compile_prompt(request.spec, request.bible, request.feedback)
        return GenerationResult(
            image=Image.open(path).convert("RGBA"),
            provider=self.name,
            prompt=prompt,
            meta={"source_file": str(path)},
        )
