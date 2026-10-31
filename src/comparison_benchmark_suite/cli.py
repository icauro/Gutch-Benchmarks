"""Terminal entrypoint: gutch-bench [--fixture NAME_OR_PATH]."""

import argparse
from pathlib import Path
import sys

def main(arguments=None) -> int:
    parser = argparse.ArgumentParser(description="Compare build storage tools. Results go to .artifacts/runs/.")
    parser.add_argument("--fixture", help="Fixture name, directory, or YAML file")
    parser.add_argument("--no-open-perfetto", action="store_true", help="Keep traces for manual opening")
    parser.add_argument("--discard-outputs", action="store_true",
                        help="Remove repositories and restored files after each case, including failures")
    args = parser.parse_args(arguments)
    if args.fixture is None:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            parser.error("Interactive mode needs a terminal; use --fixture NAME for scripted runs.")
        try:
            from .interactive import BenchmarkApp
        except ImportError as error:
            print(f"Missing dependency: {error}. Reinstall comparison-benchmark-suite.", file=sys.stderr)
            return 2
        BenchmarkApp(Path.cwd()).run()
        return 0
    try:
        import yaml
        from .benchmark import run_benchmark
    except ImportError as error:
        print(f"Missing dependency: {error}. Reinstall comparison-benchmark-suite.", file=sys.stderr)
        return 2
    try:
        return run_benchmark(Path.cwd(), args.fixture, open_perfetto=False if args.no_open_perfetto else None,
                             discard_outputs=args.discard_outputs)
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as error:
        print(f"Comparison benchmark: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
