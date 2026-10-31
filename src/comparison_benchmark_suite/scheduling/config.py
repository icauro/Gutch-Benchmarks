"""Small, typed-enough scenario loader shared by benchmark adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ScenarioDocument:
    name: str
    values: dict[str, Any]
    source_path: Path


def load_scenario(path: Path) -> ScenarioDocument:
    with path.open("r", encoding="utf-8") as handle:
        values = yaml.safe_load(handle) or {}
    if not isinstance(values, dict):
        raise ValueError(f"scenario must contain a mapping: {path}")
    name = values.get("name") or path.stem
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"scenario name must be a non-empty string: {path}")
    return ScenarioDocument(name=name, values=values, source_path=path)


class ScenarioCatalog:
    def __init__(self, root: Path):
        self.root = root

    def list(self) -> list[ScenarioDocument]:
        documents = [load_scenario(path) for path in sorted(self.root.rglob("*.yaml"))]
        names: set[str] = set()
        for document in documents:
            if document.name in names:
                raise ValueError(f"duplicate scenario name: {document.name}")
            names.add(document.name)
        return documents

    def resolve(self, name: str) -> ScenarioDocument:
        for document in self.list():
            if document.name == name:
                return document
        raise FileNotFoundError(f"unknown scenario {name!r} in {self.root}")
