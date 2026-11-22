"""Local CAVS capture, server-backed installation, and independently verified recovery.

CAVS is a delivery tool: `cavs pack-dir` packages a build, `cavs store add`
deduplicates it into a packfile store, and `cavs-client fetch` installs from a
`cavs-server` serving that store. The server is a local origin, started after
capture and stopped after verification; its startup is never timed.
"""

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import time

from ..scheduling.dataset import DatasetSelection
from ..support.filesystem import file_sha256, remove_tree, scan_tree
from ..support.recovery import capture_metrics, recovery_checks, validate_installation
from .models import LaneResult

SERVER_START_TIMEOUT_SECONDS = 30.0
# Rayon pools inside the CAVS binaries; `--connections` sets client fetch workers.
WORKERS = "4"
# cavs-client 1.8.0 returns early when every managed file already matches, so
# `--prune` never runs when the only damage is extra files.
EXTRA_FILE_REASON = "UNSUPPORTED: cavs-client skips --prune when every managed file already matches"


def companion_executables(executable: Path) -> dict[str, Path]:
    """Resolve `cavs-client` and `cavs-server` beside the configured `cavs` binary."""
    tools = {"cavs": executable}
    for name in ("cavs-client", "cavs-server"):
        companion = executable.with_name(name + executable.suffix)
        if not companion.is_file():
            raise FileNotFoundError(f"{name} must sit beside {executable}")
        tools[name] = companion
    return tools


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _wait_for_port(port: int, server: subprocess.Popen, log: Path) -> None:
    deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"cavs-server exited with {server.returncode}; see {log}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"cavs-server did not listen on port {port} within {SERVER_START_TIMEOUT_SECONDS:.0f} s")


@contextmanager
def serve_store(server_executable: Path, store: Path, lane_root: Path, log: Path, env: dict[str, str]):
    """Run `cavs-server --store` on a free loopback port and always stop it.

    The log lives with lane evidence so disk sampling excludes it.
    """
    port = _free_local_port()
    with log.open("wb") as output:
        server = subprocess.Popen(
            [str(server_executable), "--store", str(store), "--listen", f"127.0.0.1:{port}"],
            cwd=lane_root, env=env, stdout=output, stderr=subprocess.STDOUT,
        )
        try:
            _wait_for_port(port, server, log)
            yield f"http://127.0.0.1:{port}"
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


def run_cavs(executable, commands, lane, product, specification, *, dataset=None, recovery_enabled=False):
    tools = companion_executables(executable)
    dataset = dataset or DatasetSelection.resolve(product)
    store = lane.payload / "store"
    packages = lane.payload / "packages"
    cache = lane.payload / "client-cache"
    output = lane.payload / "installation"
    for directory in (store, packages, cache, output):
        remove_tree(directory)
    packages.mkdir(parents=True)
    env = {"RAYON_NUM_THREADS": WORKERS}
    assets = {source.name: f"v{index:04d}" for index, source in enumerate(dataset.sources, start=1)}
    snapshots = dataset.snapshot_metrics()
    elapsed = 0.0
    for source in dataset.sources:
        package = packages / f"{assets[source.name]}.cavs"
        before = scan_tree(store).total_bytes if store.exists() else 0
        packed = commands.run(
            [tools["cavs"], "pack-dir", source, "-o", package, *specification.arguments],
            description=f"CAVS pack {source.name}", cwd=lane.root, env=env,
        )
        added = commands.run(
            [tools["cavs"], "store", store, "add", assets[source.name], package, "--storage", "packfiles"],
            description=f"CAVS store add {source.name}", cwd=lane.root, env=env,
        )
        # The container is an intermediate; only the deduplicated store remains.
        package.unlink()
        capture = packed.elapsed_seconds + added.elapsed_seconds
        elapsed += capture
        snapshots[source.name].update(backup=capture, repo_growth_bytes=scan_tree(store).total_bytes - before)
    remove_tree(packages)
    stored = scan_tree(store)

    server_env = {**os.environ, **env}
    with serve_store(tools["cavs-server"], store, lane.root, lane.stats / "cavs-server.log", server_env) as origin:

        def install(record_snapshots, *, clean=False):
            # A fresh client cache makes every operation read from the store,
            # as Gutch does; cache reuse across the versions of one operation stays.
            remove_tree(cache)
            total = 0.0
            operation = "restore" if record_snapshots else "in-place recovery"
            for source in reversed(dataset.sources):
                result = commands.run([
                    tools["cavs-client"], "fetch", origin, assets[source.name],
                    "-o", output / source.name, "--cache", cache, "--no-resume",
                    "--prune", "--connections", WORKERS,
                ], description=f"CAVS {operation} {source.name}", cwd=lane.root, env=env)
                total += result.elapsed_seconds
                if record_snapshots:
                    snapshots[source.name]["restore"] = result.elapsed_seconds
            return total

        restored = install(True)
        validation_seconds = validate_installation(dataset, output, lane.stats, "restored")
        recovery, operations = {}, {}
        if recovery_enabled:
            recovery, operations = recovery_checks(dataset, lane, output, lambda operation: install(False),
                                                   lambda: install(False, clean=True), delete_extra=False)
            operations["exact_recovery"] = EXTRA_FILE_REASON
    verified = commands.run([tools["cavs"], "store", store, "verify"],
                            description="CAVS store verify", cwd=lane.root, env=env)
    remove_tree(cache)
    return LaneResult(specification.label, specification.kind,
                      metrics={"backup": elapsed, "restore": restored, "repository_check": verified.elapsed_seconds,
                               "repo_size": stored.total_bytes, "repo_files": stored.file_count,
                               "restore_validated": restored + validation_seconds,
                               **capture_metrics(snapshots), **recovery},
                      metadata={**dataset.metadata(), "status": "PASS", "measurement_contract": 2,
                                "recovery_mode": "restore_existing",
                                "extra_file_policy": "no_native_delete_option",
                                "snapshot_metrics": snapshots,
                                "binary_sha256": {name: file_sha256(path) for name, path in tools.items()},
                                "verify_position": "after_recovery",
                                "operations": {"capture": "PASS", "clean_restore": "PASS", **operations}})
