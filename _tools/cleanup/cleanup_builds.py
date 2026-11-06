"""Clean this workspace and declared children; use --current-only to stay local."""
import json
from pathlib import Path
import runpy

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root / "_tools/workspace.json").read_text(encoding="utf-8"))
    engine = runpy.run_path(str(root / config["cleanup_engine"]))
    raise SystemExit(engine["main"](root, ".builds"))
