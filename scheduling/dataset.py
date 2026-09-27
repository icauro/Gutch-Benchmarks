"""Resolve snapshot order and workload identity before running tools."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from comparison_benchmark_suite.support.filesystem import inventory, validate_output


from comparison_benchmark_suite.support.gutch import snapshot_version


def select_sources(product: Path, limit: int | None = None) -> list[Path]:
    if limit is not None and (isinstance(limit, bool) or limit < 1):
        raise ValueError("snapshot limit must be positive")
    sources = [path for path in product.iterdir() if path.is_dir() and not path.name.startswith('.')]
    sources.sort(key=lambda path: (tuple(int(part) for part in snapshot_version(path.name).split('.')), path.name))
    return sources[-limit:] if limit is not None else sources


@dataclass(frozen=True)
class DatasetSelection:
    product: Path
    sources: tuple[Path, ...]
    input_bytes: int
    input_files: int
    fingerprint: str
    inventories: dict[str, dict]

    @classmethod
    def resolve(cls, product: Path, limit: int | None = None, *, whole_product: bool = False):
        sources = (product,) if whole_product else tuple(select_sources(product, limit))
        if not sources:
            raise ValueError(f"product has no snapshots: {product}")
        entries = {source.name: inventory(source) for source in sources}
        files = [entry for tree in entries.values() for entry in tree.values() if entry['kind'] == 'file']
        fingerprint = hashlib.sha256(json.dumps(entries, sort_keys=True).encode('utf-8')).hexdigest()
        return cls(product, sources, sum(entry['bytes'] for entry in files), len(files), fingerprint, entries)

    def validate(self, source: Path, actual: Path, evidence: Path):
        validate_output(source, actual, evidence, expected_inventory=self.inventories[source.name])

    def metadata(self):
        return {'snapshots': [path.name for path in self.sources], 'input_bytes': self.input_bytes,
                'input_files': self.input_files, 'dataset_sha256': self.fingerprint}

    def snapshot_metrics(self):
        """Start measurement records from the frozen, selected inventories."""
        return {
            source.name: {
                'input_bytes': sum(entry['bytes'] for entry in self.inventories[source.name].values()
                                   if entry['kind'] == 'file'),
            }
            for source in self.sources
        }
