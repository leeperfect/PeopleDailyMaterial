#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "register_notebooklm_assets.py"
SPEC = importlib.util.spec_from_file_location("register_notebooklm_assets", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class NotebooklmAssetsTest(unittest.TestCase):
    def test_print_assessment_marks_small_slide_for_redraw(self):
        result = MODULE.print_assessment(1376, 768)
        self.assertEqual(result["publication_status"], "needs_redraw")
        self.assertEqual(result["print_width_mm_at_300dpi"], 116.5)

    def test_dense_infographic_requires_review(self):
        result = MODULE.print_assessment(2752, 1536, dense=True)
        self.assertEqual(result["publication_status"], "review_required")
        self.assertEqual(result["print_width_mm_at_300dpi"], 233.0)

    def test_outline_titles_reads_numbered_slides(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "outline.md"
            path.write_text(
                "# 提纲\n\n## 第1页｜封面\n\n## 第2页｜核心框架\n",
                encoding="utf-8",
            )
            original = MODULE.project_path
            MODULE.project_path = lambda _value: path
            try:
                self.assertEqual(
                    MODULE.outline_titles({"ppt_outline": "outline.md"}),
                    {1: "封面", 2: "核心框架"},
                )
            finally:
                MODULE.project_path = original

    def test_first_registration_fields_are_not_lost(self):
        record = {"id": "fig-44-01", "title": "自动标题", "used_in_wechat": False}
        existing = {"id": "fig-44-01", "title": "人工标题", "used_in_wechat": True}
        MODULE.merge_human_fields(record, existing)
        self.assertEqual(record["title"], "人工标题")
        self.assertTrue(record["used_in_wechat"])


if __name__ == "__main__":
    unittest.main()
