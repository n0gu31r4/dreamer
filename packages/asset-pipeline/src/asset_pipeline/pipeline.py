"""Pipeline runner: the act -> observe -> judge -> correct loop for one asset.

    generate (provider) -> post-process (code) -> checks (code)
        -> vision QA (judge) -> pass: save + ledger | fail: retry with feedback

Bounded retries; failures land in the manifest with full provenance so a
human (or a later agent) can see exactly what was asked and what came back.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .checks import run_checks
from .manifest import AssetSpec, Manifest
from .postprocess import postprocess
from .providers import GenerationRequest, Provider
from .qa import VisionJudge
from .style_bible import StyleBible


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_asset(
    spec: AssetSpec,
    bible: StyleBible,
    provider: Provider,
    judge: VisionJudge,
    out_dir: str | Path,
    max_attempts: int = 2,
) -> tuple[str, dict]:
    """Run one asset through the loop. Returns (status, provenance)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    attempts: list[dict] = []
    feedback: str | None = None

    for attempt in range(1, max_attempts + 1):
        record: dict = {"attempt": attempt}
        try:
            result = provider.generate(GenerationRequest(spec, bible, attempt, feedback))
        except Exception as e:  # provider errors are terminal, not retryable
            record["error"] = f"{type(e).__name__}: {e}"
            attempts.append(record)
            break

        record["prompt"] = result.prompt
        record["meta"] = result.meta

        processed = postprocess(result.image, spec, bible)
        record["postprocess"] = processed.notes

        report = run_checks(processed.image, spec, bible)
        record["checks"] = report.to_dict()

        if not report.passed:
            feedback = report.summary()
            attempts.append(record)
            continue

        verdict = judge.review(processed.image, spec, bible)
        record["verdict"] = verdict.to_dict()
        attempts.append(record)

        if verdict.passed:
            out_path = out_dir / f"{spec.id}.png"
            processed.image.save(out_path)
            return "passed", _provenance(spec, bible, provider, attempts, str(out_path))

        feedback = verdict.notes

    return "failed", _provenance(spec, bible, provider, attempts, None)


def _provenance(
    spec: AssetSpec,
    bible: StyleBible,
    provider: Provider,
    attempts: list[dict],
    file: str | None,
) -> dict:
    return {
        "provider": provider.name,
        "bible": {"name": bible.name, "version": bible.version},
        "attempts": attempts,
        "file": file,
        "created_at": _now(),
    }


def run_manifest(
    manifest: Manifest,
    bible: StyleBible,
    provider: Provider,
    judge: VisionJudge,
    out_dir: str | Path,
    max_attempts: int = 2,
) -> dict[str, int]:
    """Run every pending asset. Returns {"passed": n, "failed": n}."""
    counts = {"passed": 0, "failed": 0}
    for entry in manifest.pending():
        status, provenance = run_asset(
            entry.spec, bible, provider, judge, out_dir, max_attempts
        )
        manifest.set_result(entry.spec.id, status, provenance)
        counts[status] += 1
    return counts
