"""Report this workspace's disposable storage, cascading to declared children."""
from pathlib import Path
import sys
from storage_report import local_main, pause_before_exit

if __name__ == '__main__':
    try:
        raise SystemExit(local_main(Path(__file__).resolve().parents[2]))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Storage report failed: {error}', file=sys.stderr)
        raise SystemExit(1)
    finally:
        pause_before_exit()
