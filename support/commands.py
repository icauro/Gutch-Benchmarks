"""Gutch CLI command construction."""

from pathlib import Path

from comparison_benchmark_suite.support.models import GutchProfile


class GutchCli:
    def __init__(self, executable: Path, *, profile_mode: str = "off"):
        self.executable = executable
        self.profile_mode = profile_mode

    def command(self, *arguments: str | Path) -> list[str | Path]:
        command = [self.executable, *arguments]
        if "--profile-dir" in command:
            if self.profile_mode == "off":
                index = command.index("--profile-dir")
                del command[index:index + 2]
            command.extend(["--profile", self.profile_mode])
        if "--output" in command and "--json" not in command:
            command.append("--json")
        return command

    @staticmethod
    def profile_args(profile: GutchProfile) -> list[str]:
        arguments = [
            "--chunker",
            profile.chunker,
            "--chunk-preset",
            profile.chunk_profile.removeprefix("chunk_"),
            "--bundle-preset",
            profile.bundle_profile.removeprefix("bundle_"),
            "--compression-algorithm",
            profile.compression_algorithm,
            "--storage-mode",
            profile.storage_mode.replace("_", "-"),
        ]
        if profile.compression_level is not None:
            arguments.extend(["--compression-level", str(profile.compression_level)])
        if profile.jobs is not None:
            arguments.extend(["--jobs", str(profile.jobs)])
        return arguments

    @staticmethod
    def runtime_args(profile: GutchProfile) -> list[str]:
        return ["--jobs", str(profile.jobs)] if profile.jobs is not None else []
