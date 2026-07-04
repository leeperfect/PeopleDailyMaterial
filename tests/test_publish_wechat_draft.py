#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_wechat_draft.py"
SPEC = importlib.util.spec_from_file_location("publish_wechat_draft", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PublishWechatDraftTest(unittest.TestCase):
    def test_remote_image_is_not_treated_as_local(self):
        article = Path(__file__)
        self.assertIsNone(MODULE.local_image_path("https://example.com/a.png", article))

    def test_fingerprint_changes_with_layout(self):
        first = MODULE.publication_fingerprint("abc", {"theme": "default"})
        second = MODULE.publication_fingerprint("abc", {"theme": "grace"})
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
