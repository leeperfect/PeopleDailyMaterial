#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from scripts.sync_dual_drafts import save_toutiao_profile


class SyncDualDraftsTest(unittest.TestCase):
    def test_profile_cannot_enable_automatic_publish(self):
        with self.assertRaisesRegex(RuntimeError, "不能开启自动正式发布"):
            save_toutiao_profile('{"auto_publish": true, "原创声明": true}')

    def test_profile_stores_only_visible_page_options(self):
        state = {"schema_version": 1, "articles": {}}
        with (
            patch("scripts.sync_dual_drafts.load_public_config", return_value={}),
            patch("scripts.sync_dual_drafts.load_state", return_value=state),
            patch("scripts.sync_dual_drafts.save_state") as save_state,
        ):
            result = save_toutiao_profile(
                '{"save_as_draft": true, "auto_publish": false, "原创声明": true}'
            )
        self.assertEqual(result, {"原创声明": True})
        self.assertEqual(state["toutiao_option_profile"], {"原创声明": True})
        save_state.assert_called_once()


if __name__ == "__main__":
    unittest.main()
