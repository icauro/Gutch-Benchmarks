"""Adapters for the local Restic, Kopia, Borg, and Plakar comparison lanes."""

from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import Path
import tempfile
import shutil
import time

from comparison_benchmark_suite.support.command import CommandRunner, CommandError
from comparison_benchmark_suite.support.filesystem import remove_tree, scan_tree
from comparison_benchmark_suite.support.recovery import apply_corruption_plan, build_corruption_plan
from comparison_benchmark_suite.scheduling.dataset import DatasetSelection
from comparison_benchmark_suite.support.filesystem import file_sha256
from comparison_benchmark_suite.tools.models import LaneResult, LaneSpec


@dataclass
class ExternalTools:
    commands: CommandRunner
    restic: Path | None = None
    kopia: Path | None = None
    borg: Path | None = None
    plakar: Path | None = None
    borg_version: str | None = None

    def __post_init__(self):
        if self.borg is not None:
            self.check_borg_version()

    def check_borg_version(self):
        if self.borg_version is None:
            self.borg = self.executable("borg")
            # Preflight happens when configuring the runner, before lane clocks
            # and measurement slices begin. Reuse the result for every repeat.
            self.borg_version = self.commands.run(
                [self.borg, "--version"], description="Borg version preflight",
            ).stdout.strip()
            if re.search(r"\bborg(?:\.exe)?\s+2\.", self.borg_version) is None:
                raise ValueError(f"Borg 2 is required; found: {self.borg_version}")

    def executable(self, kind: str) -> Path:
        explicit = {
            "restic": self.restic,
            "kopia": self.kopia,
            "borg": self.borg,
            "plakar": self.plakar,
        }.get(kind)
        if explicit is not None:
            if not explicit.is_file():
                raise FileNotFoundError(f"configured {kind} executable does not exist: {explicit}")
            return explicit
        found = shutil.which(kind)
        if found:
            return Path(found).resolve()
        raise FileNotFoundError(f"{kind} executable is not configured or on PATH")


def _restic_id(output: str) -> str:
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("message_type") == "summary" and value.get("snapshot_id"):
            return str(value["snapshot_id"])
    raise RuntimeError("restic backup did not return a snapshot id")


def _plakar_cache_directory(lane_root: Path) -> Path:
    lane_id = hashlib.sha256(str(lane_root.resolve()).encode("utf-8")).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"gutch-p-{lane_id}"


def _plakar_command(
    executable: Path,
    repo: Path,
    cache_directory: Path,
    *arguments: str | Path,
) -> list[str | Path]:
    return [
        executable,
        "-quiet",
        "-cachedir",
        cache_directory,
        "-stdio",
        "at",
        repo,
        *arguments,
    ]


def run_external(
    tools: ExternalTools,
    lane: object,
    product: Path,
    lane_spec: LaneSpec,
    *,
    recovery_enabled: bool = False,
    snapshot_limit: int | None = None,
    dataset: DatasetSelection | None = None,
) -> LaneResult:
    kind = lane_spec.tool
    executable = tools.executable(kind)
    lane_root = lane.root
    plakar_cache_directory = _plakar_cache_directory(lane_root)
    repo = lane.payload / "repo"
    output = lane.payload / "installation"
    remove_tree(repo)
    remove_tree(output)
    repo.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    dataset = dataset or DatasetSelection.resolve(product, snapshot_limit)
    sources = list(dataset.sources)
    if not sources:
        raise ValueError(f"product has no target directories: {product}")
    if kind == "borg" and tools.borg_version is None:
        raise ValueError("Borg version preflight must run before benchmark lanes")
    tool_version = tools.borg_version if kind == "borg" else None
    elapsed_commands: list[float] = []
    def execute(command, **kwargs):
        result = tools.commands.run(command, **kwargs)
        elapsed_commands.append(result.elapsed_seconds)
        return result

    env = {}
    if kind == "restic":
        env = {
            "RESTIC_PASSWORD": "bench",
            "RESTIC_CACHE_DIR": str(lane_root / "restic-cache"),
        }
        execute(
            [executable, "init", *lane_spec.arguments, "--repo", repo],
            description=f"{lane_spec.label} init",
            env=env,
        )
    elif kind == "kopia":
        env = {
            "KOPIA_CONFIG_PATH": str(lane_root / "kopia.config"),
            "KOPIA_PASSWORD": "bench",
            "KOPIA_CACHE_DIRECTORY": str(lane_root / "kopia-cache"),
            "KOPIA_LOG_DIR": str(lane_root / "kopia-logs"),
            "KOPIA_CHECK_FOR_UPDATES": "false",
        }
        execute(
            [executable, "repository", "create", "filesystem", "--path", repo, "--no-persist-credentials", "--no-progress"],
            description=f"{lane_spec.label} init",
            env=env,
        )
        if lane_spec.arguments:
            execute(
                [executable, "policy", "set", "--global", *lane_spec.arguments],
                description=f"{lane_spec.label} policy",
                env=env,
            )
    elif kind == "plakar":
        env = {"PLAKAR_INSECURE_PLAINTEXT": "1"}
        execute(
            _plakar_command(executable, repo, plakar_cache_directory, "create", "-plaintext"),
            description=f"{lane_spec.label} init",
            env=env,
        )
    else:
        env = {
            "BORG_BASE_DIR": str(lane_root / "borg"),
            "BORG_CACHE_DIR": str(lane_root / "borg-cache"),
            # Borg 2.0.0b25 removed none-sha256. Payloads stay unencrypted;
            # this fixed local test passphrase protects the authentication key.
            "BORG_PASSPHRASE": "bench",
        }
        execute(
            [executable, "repo-create", "--repo", repo, "--encryption", "authenticated-sha256"],
            description=f"{lane_spec.label} init",
            env=env,
        )

    started = len(elapsed_commands)
    snapshot_metrics = dataset.snapshot_metrics()
    identifiers: dict[str, str] = {}
    for index, source in enumerate(sources, start=1):
        if kind == "restic":
            result = execute(
                [executable, "backup", *lane_spec.arguments, "--json", "--repo", repo, source.name],
                description=f"{lane_spec.label} backup {source.name}",
                cwd=product,
                env=env,
            )
            identifiers[source.name] = _restic_id(result.stdout)
        elif kind == "kopia":
            execute([executable, "snapshot", "create", source, "--no-progress"], description=f"{lane_spec.label} create {source.name}", env=env)
            identifiers[source.name] = source.name
        elif kind == "plakar":
            tag = f"gutch-benchmark-{index:04d}"
            execute(
                _plakar_command(executable, repo, plakar_cache_directory, "backup", *lane_spec.arguments, "-no-progress", "-tag", tag, source.name),
                description=f"{lane_spec.label} backup {source.name}",
                cwd=product,
                env=env,
            )
            identifiers[source.name] = tag
        else:
            archive = f"{lane_spec.label}-{source.name}"
            execute(
                [executable, "create", "--repo", repo, *lane_spec.arguments, archive, source.name],
                description=f"{lane_spec.label} create {source.name}",
                cwd=product,
                env=env,
            )
            identifiers[source.name] = archive
        snapshot_metrics[source.name]["backup"] = elapsed_commands[-1]
    backup = sum(elapsed_commands[started:])
    repo_stats = scan_tree(repo)

    def restore_output(record_snapshots: bool = False) -> float:
        restore_started = len(elapsed_commands)
        operation = "restore" if record_snapshots else "in-place recovery"
        restic_options = [] if record_snapshots else ["--overwrite", "always", "--delete"]
        kopia_options = [] if record_snapshots else ["--delete-extra"]
        # Borg 2.0.0b25 requires this even for the initial restore once another
        # version directory exists under the shared output root.
        borg_options = ["--continue"]
        output.mkdir(parents=True, exist_ok=True)
        for source in reversed(sources):
            if kind == "restic":
                execute(
                    [executable, "restore", identifiers[source.name], *restic_options, "--verify", "--repo", repo, "--target", output, "--include", source.name],
                    description=f"{lane_spec.label} {operation} {source.name}",
                    env=env,
                )
            elif kind == "kopia":
                execute(
                    [executable, "snapshot", "restore", source, output / source.name, "--snapshot-time=latest", "--no-progress", *kopia_options],
                    description=f"{lane_spec.label} {operation} {source.name}",
                    env=env,
                )
            elif kind == "plakar":
                destination = output / source.name
                destination.mkdir(parents=True, exist_ok=True)
                execute(
                    _plakar_command(executable, repo, plakar_cache_directory, "restore", "-to", destination, "-tag", identifiers[source.name]),
                    description=f"{lane_spec.label} {operation} {source.name}",
                    env=env,
                )
            else:
                execute(
                    [executable, "extract", "--repo", repo, *borg_options, identifiers[source.name]],
                    description=f"{lane_spec.label} {operation} {source.name}",
                    cwd=output,
                    env=env,
                )
            if record_snapshots:
                snapshot_metrics[source.name]["restore"] = elapsed_commands[-1]
        elapsed = sum(elapsed_commands[restore_started:])
        return elapsed

    restore = restore_output(record_snapshots=True)
    for source in sources:
        dataset.validate(source, output / source.name, lane.stats / f"validate-restored-{source.name}.json")
    corrupt_seconds = 0.0
    repair_seconds = 0.0
    recovery_error = None
    if recovery_enabled:
        recovery_destinations = [output / source.name for source in reversed(sources)]
        plans = [
            build_corruption_plan(
                destination,
                lane_root / "stats" / f"corruption-{index:03d}.json",
                index,
            )
            for index, destination in enumerate(recovery_destinations, start=1)
        ]
        corrupt_started = time.perf_counter()
        for destination, plan in zip(recovery_destinations, plans, strict=True):
            apply_corruption_plan(destination, plan)
        corrupt_seconds = time.perf_counter() - corrupt_started
        try:
            repair_seconds = restore_output()
        except CommandError as error:
            recovery_error = str(error)

    verify_started = len(elapsed_commands)
    if kind == "restic":
        execute([executable, "check", "--read-data", "--repo", repo], description=f"{lane_spec.label} check", env=env)
    elif kind == "kopia":
        for source in sources:
            execute(
                [executable, "snapshot", "verify", "--sources", source, "--verify-files-percent=100", "--no-progress"],
                description=f"{lane_spec.label} verify {source.name}",
                env=env,
            )
    elif kind == "plakar":
        execute(
            _plakar_command(executable, repo, plakar_cache_directory, "check"),
            description=f"{lane_spec.label} check",
            env=env,
        )
    else:
        execute([executable, "check", "--repo", repo, "--verify-data"], description=f"{lane_spec.label} check", env=env)
    verify = sum(elapsed_commands[verify_started:])
    if recovery_error is None:
        try:
            for source in sources:
                dataset.validate(source, output / source.name, lane.stats / f"validate-final-{source.name}.json")
        except RuntimeError as error:
            recovery_error = str(error)
    return LaneResult(
        lane_spec.label,
        lane_spec.kind,
        {
            "backup": backup,
            "restore": restore,
            "repository_check": verify,
            **({"compare": 0.0} if recovery_error is None else {}),
            "corrupt": corrupt_seconds,
            **({"repair": repair_seconds} if recovery_enabled and recovery_error is None else {}),
            "repo_size": repo_stats.total_bytes,
            "repo_files": repo_stats.file_count,
        },
        {},
        {
            "status": "ERROR" if recovery_error else "PASS",
            "reason": recovery_error,
            "recovery_error": recovery_error,
            "recovery_mode": "restore_existing",
            "extra_file_policy": "native_delete" if kind in {"restic", "kopia"} else "no_native_delete_option",
            "snapshot_metrics": snapshot_metrics,
            "tool_version": tool_version,
            "binary_sha256": file_sha256(executable) if executable.is_file() else None,
            "verify_invocations": len(sources) if kind == "kopia" else 1,
            "verify_position": "after_recovery",
            "corrupt_repair_after_reconstruct": recovery_enabled,
            **({"differences": []} if recovery_error is None else {}),
        },
    )
