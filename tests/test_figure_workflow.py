#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from modules.figure_workflow import (
    PROJECT_ROOT,
    add_manual_figure,
    apply_plan,
    apply_plan_to_body,
    article_headings,
    effective_plan,
    normalize_manifest,
    confirm_figures,
    strip_managed_figures,
)


class FigureWorkflowTest(unittest.TestCase):
    def test_manual_upload_creates_manifest_and_deduplicates_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            article = root / "80-test.md"
            article.write_text(
                "---\ndate: 2026-08-22\ntopic: 手动配图测试\nplatform: 公众号 + 今日头条\n---\n\n# 标题\n\n## 一、内容\n\n正文\n",
                encoding="utf-8",
            )
            image_bytes = io.BytesIO()
            Image.new("RGB", (960, 540), "#f97316").save(image_bytes, format="PNG")
            config = {"workflow_state": str(root / "state.json")}
            with (
                patch("modules.figure_workflow.PROJECT_ROOT", root),
                patch("modules.writing_workflow.PROJECT_ROOT", root),
                patch("modules.figure_workflow.load_public_config", return_value=config),
            ):
                first = add_manual_figure(
                    article,
                    filename="我的配图.png",
                    data=image_bytes.getvalue(),
                )
                second = add_manual_figure(
                    article,
                    filename="重复图片.png",
                    data=image_bytes.getvalue(),
                )
            self.assertFalse(first["duplicate"])
            self.assertTrue(second["duplicate"])
            self.assertEqual(first["figure_count"], 1)
            self.assertIn("figure_manifest:", article.read_text(encoding="utf-8"))
            self.assertTrue(root.joinpath(first["figure"]["file"]).exists())

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

    def test_legacy_wechat_usage_becomes_shared_plan(self):
        manifest = normalize_manifest(
            {
                "figures": [
                    {
                        "id": "fig-1",
                        "file": "media/fig-1.png",
                        "used_in_wechat": True,
                        "article_order": 1,
                        "article_position": "## 二、内容之前",
                    }
                ]
            }
        )
        self.assertEqual(effective_plan(manifest, "wechat")[0]["id"], "fig-1")
        self.assertEqual(effective_plan(manifest, "toutiao")[0]["before_heading"], "## 二、内容")

    def test_toutiao_override_does_not_change_shared_plan(self):
        manifest = normalize_manifest(
            {
                "figures": [
                    {"id": "fig-1", "file": "media/fig-1.png", "width_px": 100, "height_px": 100},
                    {"id": "fig-2", "file": "media/fig-2.png", "width_px": 100, "height_px": 100},
                ],
                "plans": {
                    "shared": {"items": [{"id": "fig-1", "before_heading": "## 一、内容"}]},
                    "wechat": {"inherit": "shared", "items": None},
                    "toutiao": {"inherit": None, "items": [{"id": "fig-2", "before_heading": "## 二、内容"}]},
                },
            }
        )
        self.assertEqual(effective_plan(manifest, "wechat")[0]["id"], "fig-1")
        self.assertEqual(effective_plan(manifest, "toutiao")[0]["id"], "fig-2")

    def test_plan_is_inserted_before_selected_heading(self):
        manifest = {
            "figures": [
                {"id": "fig-1", "file": "media/fig-1.png", "width_px": 100, "height_px": 100}
            ]
        }
        body = "# 标题\n\n## 一、内容\n\n第一段\n\n## 二、内容\n\n第二段"
        # 纯转换测试不要求图片真实存在，因此只验证插入函数的结构行为。
        with patch("modules.figure_workflow.Path.exists", return_value=True):
            result = apply_plan_to_body(
                body,
                [{"id": "fig-1", "before_heading": "## 二、内容"}],
                manifest,
            )
        self.assertIn("![fig-1](media/fig-1.png)\n\n## 二、内容", result)

    def test_toutiao_override_keeps_wechat_markdown_and_confirmation_state(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            root = Path(temporary)
            article = root / "article.md"
            manifest_path = root / "figure-manifest.yml"
            first = root / "fig-1.png"
            second = root / "fig-2.png"
            first.write_bytes(b"image-one")
            second.write_bytes(b"image-two")
            relative_manifest = manifest_path.relative_to(PROJECT_ROOT)
            article.write_text(
                f"---\nfigure_manifest: {relative_manifest}\n---\n\n# 标题\n\n## 一、内容\n\n第一段\n\n## 二、内容\n\n第二段\n",
                encoding="utf-8",
            )
            import yaml

            manifest_path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 2,
                        "article": str(article.relative_to(PROJECT_ROOT)),
                        "figures": [
                            {"id": "fig-1", "file": str(first.relative_to(PROJECT_ROOT)), "width_px": 100, "height_px": 100, "sha256": "one"},
                            {"id": "fig-2", "file": str(second.relative_to(PROJECT_ROOT)), "width_px": 100, "height_px": 100, "sha256": "two"},
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            config = {"workflow_state": str(root / "state.json")}
            with (
                patch("modules.figure_workflow.load_public_config", return_value=config),
                patch("modules.figure_workflow.save_snapshot", return_value=root / "snapshot.md"),
            ):
                apply_plan(
                    article,
                    [{"id": "fig-1", "before_heading": "## 一、内容"}],
                    platform="shared",
                )
                wechat_markdown = article.read_text(encoding="utf-8")
                apply_plan(
                    article,
                    [{"id": "fig-2", "before_heading": "## 二、内容"}],
                    platform="toutiao",
                )
                self.assertEqual(article.read_text(encoding="utf-8"), wechat_markdown)
                result = confirm_figures(article)
            self.assertTrue(result["ok"])
            state = json.loads((root / "state.json").read_text(encoding="utf-8"))
            entry = next(iter(state["articles"].values()))
            self.assertEqual(entry["status"], "figures_confirmed")


if __name__ == "__main__":
    unittest.main()
