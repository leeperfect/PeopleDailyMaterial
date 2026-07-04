#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "wechat_setup.py"
SPEC = importlib.util.spec_from_file_location("wechat_setup", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class WechatSetupTest(unittest.TestCase):
    def test_credentials_are_written_without_echo_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            old_root = MODULE.PROJECT_ROOT
            MODULE.PROJECT_ROOT = Path(temporary)
            try:
                MODULE.save_credentials(
                    "wx1234567890abcdef",
                    "a" * 32,
                )
                env_path = Path(temporary) / ".env"
                content = env_path.read_text(encoding="utf-8")
                self.assertIn("WECHAT_APPID=wx1234567890abcdef", content)
                self.assertIn("WECHAT_APPSECRET=" + "a" * 32, content)
                self.assertNotIn("a" * 32, MODULE.page())
            finally:
                MODULE.PROJECT_ROOT = old_root

    def test_newline_injection_is_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.save_credentials(
                "wx1234567890abcdef\nOTHER=value",
                "a" * 32,
            )


if __name__ == "__main__":
    unittest.main()
