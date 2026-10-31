"""Gutch command settings used by comparison adapters."""
from dataclasses import dataclass

@dataclass(frozen=True)
class GutchProfile:
    name: str
    chunk_profile: str = "chunk_128KiB"
    bundle_profile: str = "bundle_8MiB"
    compression_algorithm: str = "zstd"
    compression_level: int | None = 3
    storage_mode: str = "bundled"
    jobs: int | None = None
    chunker: str = "fastcdc"


