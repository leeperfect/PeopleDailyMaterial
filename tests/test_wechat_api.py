#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

import requests

from modules.wechat_api import (
    DEFAULT_EXPECTED_PUBLIC_IP,
    DEFAULT_PUBLIC_IP_URL,
    WechatApiError,
    add_draft,
    public_ip,
    response_json,
    update_draft,
)


class WechatApiTest(unittest.TestCase):
    def test_text_plain_response_is_decoded_as_utf8(self):
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "text/plain"
        response.encoding = "ISO-8859-1"
        response._content = '{"title":"中国品牌"}'.encode("utf-8")

        data = response_json(response)

        self.assertEqual(data["title"], "中国品牌")

    @patch("modules.wechat_api.requests.post")
    @patch("modules.wechat_api.get_access_token", return_value="test-token")
    def test_draft_payload_keeps_chinese_as_utf8(
        self,
        _get_access_token,
        post,
    ):
        post.return_value.content = b'{"media_id":"test-media-id"}'

        media_id = add_draft({"title": "中国品牌"})

        self.assertEqual(media_id, "test-media-id")
        kwargs = post.call_args.kwargs
        self.assertNotIn("json", kwargs)
        self.assertIn("中国品牌".encode("utf-8"), kwargs["data"])
        self.assertNotIn(b"\\u4e2d", kwargs["data"])
        self.assertEqual(
            kwargs["headers"]["Content-Type"],
            "application/json; charset=utf-8",
        )

    @patch("modules.wechat_api.requests.post")
    @patch("modules.wechat_api.get_access_token", return_value="test-token")
    def test_draft_update_keeps_chinese_as_utf8(
        self,
        _get_access_token,
        post,
    ):
        post.return_value.content = b'{"errcode":0}'

        update_draft("test-media-id", {"title": "中国品牌"})

        kwargs = post.call_args.kwargs
        self.assertIn("中国品牌".encode("utf-8"), kwargs["data"])
        self.assertNotIn(b"\\u4e2d", kwargs["data"])
        self.assertIn(b'"media_id": "test-media-id"', kwargs["data"])

    @patch("modules.wechat_api.requests.get")
    def test_public_ip_uses_aws_and_matches_expected(self, get):
        response = requests.Response()
        response.status_code = 200
        response._content = b"193.112.28.112\n"
        get.return_value = response

        ip = public_ip()

        self.assertEqual(ip, DEFAULT_EXPECTED_PUBLIC_IP)
        get.assert_called_once()
        self.assertEqual(get.call_args.args[0], DEFAULT_PUBLIC_IP_URL)

    @patch("modules.wechat_api.requests.get")
    def test_public_ip_mismatch_stops(self, get):
        response = requests.Response()
        response.status_code = 200
        response._content = b"8.8.8.8"
        get.return_value = response

        with self.assertRaises(WechatApiError) as ctx:
            public_ip()
        self.assertIn("已停止", str(ctx.exception))
        self.assertIn("8.8.8.8", str(ctx.exception))
        self.assertIn(DEFAULT_EXPECTED_PUBLIC_IP, str(ctx.exception))

    @patch("modules.wechat_api.requests.get")
    def test_public_ip_query_failure_stops(self, get):
        get.side_effect = requests.ConnectionError("simulated unreachable")

        with self.assertRaises(WechatApiError) as ctx:
            public_ip()
        self.assertIn("查询公网 IP 失败", str(ctx.exception))
        self.assertNotIn("simulated unreachable", str(ctx.exception))



if __name__ == "__main__":
    unittest.main()
