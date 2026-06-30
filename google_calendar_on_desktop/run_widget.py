from __future__ import annotations

import os
import runpy
import sys
import traceback
from datetime import datetime
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
APP_SCRIPT = APP_DIR / "a.py"
LOG_PATH = APP_DIR / "run_widget_launcher.log"


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def redirect_output_to_log() -> None:
    log_file = LOG_PATH.open("a", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file


def main() -> int:
    os.chdir(APP_DIR)
    redirect_output_to_log()

    log(f"starting widget in same process: {APP_SCRIPT}")
    log(f"python executable: {sys.executable}")

    if not APP_SCRIPT.exists():
        log(f"failed: cannot find {APP_SCRIPT}")
        return 1

    try:
        runpy.run_path(str(APP_SCRIPT), run_name="__main__")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        log(f"stopped with SystemExit: {exc.code}")
        return code
    except Exception:
        log("crashed:")
        traceback.print_exc()
        return 1

    log("stopped normally")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
