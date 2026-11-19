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

    def test_fingerprint_changes_when_figure_content_changes(self):
        first = MODULE.publication_fingerprint("abc", {"theme": "default"}, "figure-a")
        second = MODULE.publication_fingerprint("abc", {"theme": "default"}, "figure-b")
        self.assertNotEqual(first, second)

    def test_digest_is_truncated_by_utf8_bytes(self):
        truncated = MODULE.truncate_utf8("中国品牌走向世界", 12)
        self.assertEqual(truncated, "中国品牌")
        self.assertLessEqual(len(truncated.encode("utf-8")), 12)

    def test_draft_comments_are_enabled_for_everyone(self):
        payload = MODULE.draft_article_payload(
            title="标题",
            author="LeePerfect",
            digest="摘要",
            content="<p>正文</p>",
            metadata={},
            thumb_media_id="cover-id",
        )
        self.assertEqual(payload["need_open_comment"], 1)
        self.assertEqual(payload["only_fans_can_comment"], 0)

    def test_zen_whitespace_orange_theme_is_accepted(self):
        fragment = '<section style="color:#525252"><span style="color:#FF6900">01</span><u style="border-color:#FFCAB3">关键词</u><strong style="color:#E65100">结论</strong></section>'
        label, theme_id, primary = MODULE.detect_gzh_theme(fragment)
        self.assertEqual(theme_id, "zen-whitespace-orange")
        self.assertEqual(primary, "#FF6900")

    def test_legacy_red_white_theme_still_accepted(self):
        fragment = '<section><span style="color:#DC2626">01</span><u style="border-color:#FECACA">关键词</u></section>'
        label, theme_id, primary = MODULE.detect_gzh_theme(fragment)
        self.assertEqual(theme_id, "red-white")
        self.assertEqual(primary, "#DC2626")

    def test_retired_zen_green_is_rejected(self):
        fragment = '<section><span style="color:#FF6900">01</span><u style="border-color:#FFCAB3">词</u><span style="color:#4A5D52">旧墨绿</span></section>'
        with self.assertRaises(RuntimeError):
            MODULE.detect_gzh_theme(fragment)

    def test_mixed_or_unknown_colors_are_rejected(self):
        with self.assertRaises(RuntimeError):
            MODULE.detect_gzh_theme('<section><span style="color:#FF6900">橙</span><span style="color:#DC2626">红</span><span style="color:#FECACA">浅红</span><span style="color:#FFCAB3">浅橙</span></section>')
        with self.assertRaises(RuntimeError):
            MODULE.detect_gzh_theme('<section><p>无主题色</p></section>')


if __name__ == "__main__":
    unittest.main()
