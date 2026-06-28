#!/usr/bin/env python3
"""Start the local APP opinion hotspot workbench from the project root."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "scripts" / "serve_peopleapp_hotspot_magazine.py"


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("serve_peopleapp_hotspot_magazine", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载热点选题工作台: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
