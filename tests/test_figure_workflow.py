#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from modules.figure_workflow import article_headings, strip_managed_figures


class FigureWorkflowTest(unittest.TestCase):
    def test_article_headings_keeps_exact_markdown(self):
        body = "# 标题\n\n## 一、内容\n\n正文\n\n## 参考文章"
        self.assertEqual(
            [item["value"] for item in article_headings(body)],
            ["## 一、内容", "## 参考文章"],
        )

    def test_strip_only_registered_images(self):
        manifest = {"figures": [{"file": "media/fig-1.png"}]}
        body = "正文\n\n![登记图](media/fig-1.png)\n\n![其他图](media/other.png)\n\n## 二"
        cleaned = strip_managed_figures(body, manifest)
        self.assertNotIn("fig-1.png", cleaned)
        self.assertIn("other.png", cleaned)


if __name__ == "__main__":
    unittest.main()
