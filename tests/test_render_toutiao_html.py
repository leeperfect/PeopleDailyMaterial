#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from pathlib import Path

from scripts.render_toutiao_html import fragment_without_images, sanitize_fragment, toutiao_title


class RenderToutiaoHtmlTest(unittest.TestCase):
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

    def test_toutiao_title_prefers_public_h1_and_removes_internal_number(self):
        title = toutiao_title(
            Path("data/articles/人民日报系列/75-test.md"),
            {"title": "75-【R】｜内部标题", "wechat_title": "公众号短标题"},
            "# 75-【R】｜对外长标题\n\n正文",
        )
        self.assertEqual(title, "对外长标题")


if __name__ == "__main__":
    unittest.main()
