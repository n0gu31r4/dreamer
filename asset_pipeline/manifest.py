"""Asset manifest: the ledger tracing spec -> prompt -> provider -> file.

Every asset the game needs is one entry; regeneration is re-running one entry.
Statuses: pending -> passed | failed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = ("sprite", "tileset", "ui", "background")
STATUSES = ("pending", "passed", "failed")


@dataclass(frozen=True)
class AssetSpec:
    """What the game needs, independent of how it gets generated."""

    id: str
    category: str  # one of CATEGORIES
    size: tuple[int, int]  # target (width, height) in pixels
    description: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("asset spec needs an id")
        if self.category not in CATEGORIES:
            raise ValueError(
                f"asset {self.id!r}: category must be one of {CATEGORIES}, got {self.category!r}"
            )
        w, h = self.size
        if w <= 0 or h <= 0:
            raise ValueError(f"asset {self.id!r}: size must be positive, got {self.size}")
        object.__setattr__(self, "size", (int(w), int(h)))

    @classmethod
    def from_dict(cls, data: dict) -> "AssetSpec":
        try:
            return cls(
                id=data["id"],
                category=data["category"],
                size=tuple(data["size"]),
                description=data["description"],
            )
        except KeyError as e:
            raise ValueError(f"asset spec missing required field: {e.args[0]}") from e

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "size": list(self.size),
            "description": self.description,
        }


@dataclass
class ManifestEntry:
    spec: AssetSpec
    status: str = "pending"
    provenance: dict | None = None

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(
                f"asset {self.spec.id!r}: status must be one of {STATUSES}, got {self.status!r}"
            )


@dataclass
class Manifest:
    entries: list[ManifestEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for entry in self.entries:
            if entry.spec.id in seen:
                raise ValueError(f"duplicate asset id {entry.spec.id!r} in manifest")
            seen.add(entry.spec.id)

    def pending(self) -> list[ManifestEntry]:
        return [e for e in self.entries if e.status == "pending"]

    def get(self, asset_id: str) -> ManifestEntry:
        for entry in self.entries:
            if entry.spec.id == asset_id:
                return entry
        raise KeyError(f"no asset {asset_id!r} in manifest")

    def set_result(self, asset_id: str, status: str, provenance: dict) -> None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {status!r}")
        entry = self.get(asset_id)
        entry.status = status
        entry.provenance = provenance

    @classmethod
    def load(cls, path: str | Path) -> "Manifest":
        data = json.loads(Path(path).read_text())
        return cls(
            entries=[
                ManifestEntry(
                    spec=AssetSpec.from_dict(item),
                    status=item.get("status", "pending"),
                    provenance=item.get("provenance"),
                )
                for item in data["assets"]
            ]
        )

    def save(self, path: str | Path) -> None:
        data = {
            "version": 1,
            "assets": [
                {**e.spec.to_dict(), "status": e.status, "provenance": e.provenance}
                for e in self.entries
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2) + "\n")
