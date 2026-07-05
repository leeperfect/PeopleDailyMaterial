#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path

from modules.writing_workflow import (
    bold_phrases,
    cover_for_article,
    detect_series,
    digest_from_article,
    emphasis_only_issues,
    effective_layout,
    join_frontmatter,
    load_public_config,
    split_frontmatter,
    structural_issues,
    title_from_article,
)
from scripts.render_wechat_html import layout_for_article


class WritingWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.config = load_public_config()

    def test_frontmatter_roundtrip(self):
        source = "---\ntitle: 测试文章\nseries: 热点系列\n---\n\n# 标题\n\n正文"
        frontmatter, body, metadata = split_frontmatter(source)
        self.assertEqual(metadata["title"], "测试文章")
        self.assertTrue(body.startswith("# 标题"))
        self.assertEqual(join_frontmatter(frontmatter, body), source + "\n")

    def test_series_and_cover_mapping(self):
        people_path = Path("data/articles/人民日报系列/35-test.md")
        hotspot_path = Path("data/articles/热点系列/热点4-test.md")
        self.assertEqual(detect_series(people_path, {}), "people_daily")
        self.assertEqual(detect_series(hotspot_path, {}), "hotspot")
        self.assertEqual(
            cover_for_article(people_path, {}, self.config).name,
            "people-daily-header.png",
        )
        self.assertEqual(
            cover_for_article(hotspot_path, {}, self.config).name,
            "hotspot-header.png",
        )

    def test_default_layout_and_article_override(self):
        layout = effective_layout(
            {"wechat_layout": {"theme": "grace"}},
            self.config,
            {"primaryColor": "#123456"},
        )
        self.assertEqual(layout["theme"], "grace")
        self.assertEqual(layout["primaryColor"], "#123456")
        self.assertEqual(layout["fontSize"], "16px")
        self.assertTrue(layout["isUseIndent"])
        self.assertTrue(layout["isUseJustify"])

    def test_exported_fragment_keeps_indent_and_justify(self):
        layout = layout_for_article(
            Path("data/articles/人民日报系列/35-test.md"),
            {},
            self.config,
        )
        self.assertIn("section.container p", layout["customCSS"])
        self.assertIn("text-indent: 2em !important", layout["customCSS"])
        self.assertIn("text-align: justify !important", layout["customCSS"])

    def test_structural_guard(self):
        old = "# 标题\n\n正文内容很长" + "内容" * 100 + "\n\n## 参考文章\n\nhttps://example.com/a"
        new = "短文"
        issues = structural_issues(old, new)
        self.assertTrue(any("异常" in issue or "丢失" in issue for issue in issues))
        self.assertGreaterEqual(len(issues), 3)

    def test_title_and_digest(self):
        body = "# 正文标题\n\n这是第一段摘要，应当直接用于公众号摘要。\n\n## 一、内容"
        path = Path("data/articles/热点系列/热点4-test.md")
        self.assertEqual(title_from_article(path, {}, body), "正文标题")
        self.assertEqual(
            digest_from_article({}, body),
            "这是第一段摘要，应当直接用于公众号摘要。",
        )

    def test_emphasis_review_only_allows_new_bold_markers(self):
        before = "# 标题\n\n核心判断需要突出。\n\n## 参考文章"
        after = "# 标题\n\n**核心判断需要突出。**\n\n## 参考文章"
        self.assertEqual(emphasis_only_issues(before, after), [])
        self.assertEqual(bold_phrases(after), ["核心判断需要突出。"])

    def test_emphasis_review_rejects_wording_changes(self):
        before = "# 标题\n\n原来的判断。"
        after = "# 标题\n\n**调整后的判断。**"
        self.assertTrue(emphasis_only_issues(before, after))


if __name__ == "__main__":
    unittest.main()
