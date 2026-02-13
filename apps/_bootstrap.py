from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
FONTS_DIR = REPO_ROOT / "assets" / "fonts"


def ensure_repo_root_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
