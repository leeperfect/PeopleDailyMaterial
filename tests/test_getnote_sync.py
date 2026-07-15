#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "getnote_sync.py"
SPEC = importlib.util.spec_from_file_location("getnote_sync", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GetnoteSyncTest(unittest.TestCase):
    def test_note_id_is_always_string(self):
        output = '{"data":{"note":{"id":1907962187788341186,"note_id":"1907962187788341186","content":"正文"}}}'
        self.assertEqual(MODULE.note_id_from_output(output), "1907962187788341186")

    def test_nested_note_detail(self):
        note = MODULE.find_note(
            {
                "data": {
                    "note": {
                        "note_id": "1907962187788341186",
                        "content": "正文",
                    }
                }
            }
        )
        self.assertEqual(note["content"], "正文")

    def test_normalizes_only_first_markdown_heading_marker(self):
        content = "#44｜标题\n\n正文里的#标签保持原样。\n\n## 二级标题"
        normalized = MODULE.normalize_pulled_markdown(content)
        self.assertEqual(
            normalized,
            "# 44｜标题\n\n正文里的#标签保持原样。\n\n## 二级标题",
        )

    def test_keeps_valid_heading_unchanged(self):
        content = "# 44｜标题\n\n正文"
        self.assertEqual(MODULE.normalize_pulled_markdown(content), content)


if __name__ == "__main__":
    unittest.main()
