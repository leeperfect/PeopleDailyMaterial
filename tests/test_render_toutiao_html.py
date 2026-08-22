#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from pathlib import Path

from scripts.render_toutiao_html import (
    fragment_without_images,
    fragment_without_lead_title,
    sanitize_fragment,
    toutiao_title,
)


class RenderToutiaoHtmlTest(unittest.TestCase):
    def test_image_caption_and_duplicate_lead_title_are_removed(self):
        source = "<h1>主标题</h1><figure><img src='a.png'><figcaption>配图说明</figcaption></figure><p>正文</p>"
        sanitized = sanitize_fragment(source)
        self.assertNotIn("配图说明", sanitized)
        without_title = fragment_without_lead_title(sanitized)
        self.assertNotIn("<h1", without_title)
        self.assertIn("正文", without_title)

    def test_sanitize_removes_platform_specific_style(self):
        source = '<section class="container"><h2 style="color:red">标题</h2><p id="x">正文<strong>重点</strong></p></section>'
        result = sanitize_fragment(source)
        self.assertNotIn("style=", result)
        self.assertNotIn("class=", result)
        self.assertIn("<h2>标题</h2>", result)
        self.assertIn("<strong>重点</strong>", result)

    def test_browser_fill_html_excludes_local_images(self):
        source = '<p>正文</p><img src="media/a.png" alt="图"><h2>第二章</h2>'
        result = fragment_without_images(source)
        self.assertNotIn("<img", result)
        self.assertIn("<h2>第二章</h2>", result)

    def test_sanitize_removes_duplicate_list_markers(self):
        source = "<ol><li>1. 第一项</li><li>2. 第二项</li></ol><ul><li>• 要点</li><li><strong>正常要点</strong></li></ul>"
        result = sanitize_fragment(source)
        self.assertIn("<ol><li>第一项</li><li>第二项</li></ol>", result)
        self.assertIn("<ul><li>要点</li><li><strong>正常要点</strong></li></ul>", result)
        self.assertNotIn("<li>1. ", result)
        self.assertNotIn("<li>• ", result)

    def test_sanitize_converts_leftover_markdown_bold(self):
        source = "<p>前文**需要加粗的判断**后文</p><pre>**代码原样保留**</pre>"
        result = sanitize_fragment(source)
        self.assertIn("前文<strong>需要加粗的判断</strong>后文", result)
        self.assertIn("<pre>**代码原样保留**</pre>", result)

    def test_toutiao_title_prefers_public_h1_and_removes_internal_number(self):
        title = toutiao_title(
            Path("data/articles/人民日报系列/75-test.md"),
            {"title": "75-【R】｜内部标题", "wechat_title": "公众号短标题"},
            "# 75-【R】｜对外长标题\n\n正文",
        )
        self.assertEqual(title, "对外长标题")


if __name__ == "__main__":
    unittest.main()
