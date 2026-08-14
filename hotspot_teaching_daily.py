#!/usr/bin/env python3
"""Project-root launcher for the hotspot teaching daily."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "scripts" / "serve_hotspot_teaching_daily.py"


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("serve_hotspot_teaching_daily", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载热点教学日报：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
