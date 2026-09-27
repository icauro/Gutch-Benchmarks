"""Prepare immutable benchmark inputs outside the measured operations."""

import json
import hashlib
from pathlib import Path
import platform
import shutil
import tarfile
from urllib.request import urlopen
import zipfile
import yaml

from .support.filesystem import file_sha256, inventory
from .support.retention import remove_owned


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            for entry in source.infolist():
                parts = entry.filename.replace("\\", "/").split("/")
                target = destination.joinpath(*parts).resolve()
                if (".." in parts or ":" in entry.filename or
                        not target.is_relative_to(destination.resolve())):
                    raise ValueError(f"Archive path escapes extraction directory: {entry.filename}")
                if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError(f"ZIP symlink is not supported: {entry.filename}")
            source.extractall(destination)
    else:
        with tarfile.open(archive) as source:
            source.extractall(destination, filter="data")


def prepare_dataset(values: dict, fixture: Path, artifacts: Path) -> tuple[Path, dict]:
    if "dataset" in values:
        if "builds" in values:
            raise ValueError("Use either dataset or builds, not both.")
        reference = values["dataset"]
        if not isinstance(reference, str) or not reference.strip():
            raise ValueError("dataset must name a YAML file containing builds.")
        fixture = (fixture.parent / reference).resolve()
        values = yaml.safe_load(fixture.read_text(encoding="utf-8"))
        if not isinstance(values, dict) or "dataset" in values:
            raise ValueError("Shared dataset must directly define builds; nested references are unsupported.")
    builds = values.get("builds")
    if not isinstance(builds, list) or len(builds) < 2:
        raise ValueError("The fixture needs at least two builds, ordered oldest to newest.")
    fingerprint = hashlib.sha256(
        json.dumps({"fixture": str(fixture), "builds": builds, "platform": platform.system(), "machine": platform.machine()}, sort_keys=True).encode()
    ).hexdigest()[:16]
    cache = artifacts / "datasets" / fingerprint
    product = cache / "builds"
    product.mkdir(parents=True, exist_ok=True)
    origins = []
    for index, build in enumerate(builds, 1):
        if not isinstance(build, dict):
            raise ValueError("Each build must contain a path or platform downloads.")
        target = product / f"v{index}"
        expected_file = cache / f"v{index}.json"
        if "path" in build:
            if not isinstance(build["path"], str) or not build["path"].strip():
                raise ValueError("Each local build path must be a nonempty string.")
            source = (fixture.parent / build["path"]).resolve()
            if not source.is_dir():
                raise ValueError(f"Build directory does not exist: {source}")
            if source == artifacts or source.is_relative_to(artifacts) or artifacts.is_relative_to(source):
                raise ValueError("Build inputs and the suite artifact directory must not contain each other.")
            expected = inventory(source)
            origins.append({"source": str(source), "version": build.get("version", f"v{index}")})
            if not target.is_dir() or inventory(target) != expected:
                remove_owned(target, cache)
                shutil.copytree(source, target, symlinks=True)
        else:
            host = {"Windows": "windows-x64", "Linux": "linux-x64"}.get(platform.system())
            if platform.machine().lower() not in {"amd64", "x86_64"}:
                host = None
            downloads = build.get("downloads", {})
            if not isinstance(downloads, dict):
                raise ValueError("downloads must map platform names to URL/checksum pairs.")
            asset = downloads.get(host)
            if not isinstance(asset, dict):
                raise ValueError("No pinned download for this platform. Use local build paths in a custom fixture.")
            url, digest = asset.get("url"), asset.get("sha256")
            if not isinstance(url, str) or not url.strip():
                raise ValueError("Every download requires a URL.")
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("Every download requires a lowercase SHA-256 checksum.")
            origins.append({"url": url, "sha256": digest, "version": build.get("version", f"v{index}")})
            if target.is_dir() and expected_file.exists():
                expected = json.loads(expected_file.read_text(encoding="utf-8"))
                if inventory(target) == expected:
                    continue
            archive = artifacts / "downloads" / digest
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.is_file() or file_sha256(archive) != digest:
                print(f"Downloading {build.get('version', index)}: {url}", flush=True)
                temporary = archive.with_suffix(".part")
                with urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                    shutil.copyfileobj(response, output)
                if file_sha256(temporary) != digest:
                    raise ValueError(f"Download checksum mismatch: {url}")
                temporary.replace(archive)
            extracted = cache / "extract"
            remove_owned(extracted, cache)
            extract_archive(archive, extracted)
            roots = list(extracted.iterdir())
            if len(roots) != 1 or not roots[0].is_dir():
                raise ValueError("A fixture archive must contain one build directory.")
            remove_owned(target, cache)
            shutil.move(str(roots[0]), target)
            remove_owned(extracted, cache)
            expected = inventory(target)
        expected_file.write_text(json.dumps(expected, sort_keys=True), encoding="utf-8")
    return product, {"builds": origins, "order": [f"v{i}" for i in range(1, len(builds) + 1)]}
