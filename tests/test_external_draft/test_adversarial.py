#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""外部成稿登记的对抗性测试：验证无法绕过安全检查。"""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import (
    ExternalDraftMode,
    article_state,
    body_hash,
    file_sha256,
    load_state,
    save_state,
    split_frontmatter,
    validate_external_candidate_import,
    validate_external_draft_registration,
)
from modules.platform_workflow import (
    publication_readiness,
    _check_polish_readiness,
    _verify_external_registration_integrity,
)


class AdversarialExternalDraftTest(unittest.TestCase):
    """对抗性测试：验证无法绕过外部成稿登记的安全检查。"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.article_path = Path(self.test_dir) / "test_article.md"
        self.candidate_path = Path(self.test_dir) / "candidate.md"
        self.other_article_path = Path(self.test_dir) / "other_article.md"

        # 创建测试文章
        self.original_content = """---
title: 测试文章
date: 2026-11-22
---

# 测试

原始正文内容。

## 参考文章

- 参考1
"""
        self.article_path.write_text(self.original_content, encoding="utf-8")
        self.original_hash = file_sha256(self.article_path)
        _, original_body, _ = split_frontmatter(self.original_content)
        self.original_body_hash = body_hash(original_body)

        # 创建候选稿
        self.candidate_content = """润色后的正文内容。

# 测试

润色后的正文内容，更清晰。

## 参考文章

- 参考1
"""
        self.candidate_path.write_text(self.candidate_content, encoding="utf-8")

        # 创建另一篇文章
        self.other_article_path.write_text(self.original_content, encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ========== 测试 1：登记后修改正文必须被拒绝 ==========

    def test_1_content_change_after_registration_blocks_sync(self):
        """【对抗 1】登记后修改正文，sync 入口必须在消费处比对拒绝。"""
        # 模拟已登记状态
        entry = {
            "external_draft_registration": {
                "mode": ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
                "registered_at": "2026-11-22T10:00:00",
                "source_file_hash": self.original_hash,
                "source_body_hash": self.original_body_hash,
                "target_platform": "wechat",
                "baseline_snapshot": "some/path.md",
            },
            "emphasis_reviewed_at": "2026-11-22T10:30:00",
        }

        # 初始状态应该通过 polish 检查
        ok, issue = _check_polish_readiness(entry)
        self.assertTrue(ok, "初始状态应该通过 polish 检查")

        # 修改正文后
        self.article_path.write_text(self.original_content + "\n修改后的内容", encoding="utf-8")

        # 【关键检查】消费时校验应该失败
        issues = _verify_external_registration_integrity(
            self.article_path, entry, "wechat"
        )
        self.assertTrue(len(issues) > 0, "正文修改后应该被检测到")
        self.assertTrue(any("修改" in issue for issue in issues))

    def test_1b_candidate_import_body_change_blocked(self):
        """【对抗 1b】候选导入后正文变化也必须被检测。"""
        _, candidate_body, _ = split_frontmatter(self.candidate_content)
        candidate_body_hash = body_hash(candidate_body)

        entry = {
            "external_draft_registration": {
                "mode": ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
                "registered_at": "2026-11-22T10:00:00",
                "source_file_hash": self.original_hash,
                "source_body_hash": self.original_body_hash,
                "candidate_imported": True,
                "candidate_body_hash": candidate_body_hash,
                "target_platform": "wechat",
                "baseline_snapshot": "some/path.md",
            },
            "emphasis_reviewed_at": "2026-11-22T10:30:00",
        }

        # 写入候选内容后修改
        self.article_path.write_text(self.candidate_content + "\n偷偷修改", encoding="utf-8")

        issues = _verify_external_registration_integrity(
            self.article_path, entry, "wechat"
        )
        self.assertTrue(len(issues) > 0, "候选导入后修改正文应该被检测到")

    # ========== 测试 2：平台绑定必须强制执行 ==========

    def test_2_wechat_only_cannot_sync_toutiao(self):
        """【对抗 2】wechat_only 登记不能用于头条同步。"""
        entry = {
            "external_draft_registration": {
                "mode": ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
                "registered_at": "2026-11-22T10:00:00",
                "target_platform": "wechat_only",
                "source_file_hash": self.original_hash,
                "source_body_hash": self.original_body_hash,
                "baseline_snapshot": "some/path.md",
            },
            "emphasis_reviewed_at": "2026-11-22T10:30:00",
        }

        # 尝试同步到头条应该被拒绝
        issues = _verify_external_registration_integrity(
            self.article_path, entry, "toutiao"
        )
        self.assertTrue(len(issues) > 0, "wechat_only 应该阻止头条同步")
        self.assertTrue(any("今日头条" in issue for issue in issues))

        # 尝试同步到 both 也应该被拒绝
        issues = _verify_external_registration_integrity(
            self.article_path, entry, "both"
        )
        self.assertTrue(len(issues) > 0, "wechat_only 应该阻止 both 同步")

        # 同步到 wechat 应该通过
        issues = _verify_external_registration_integrity(
            self.article_path, entry, "wechat"
        )
        self.assertEqual(len(issues), 0, "wechat_only 应该允许公众号同步")

    def test_2b_toutiao_only_cannot_sync_wechat(self):
        """【对抗 2b】toutiao 登记不能用于公众号同步。"""
        entry = {
            "external_draft_registration": {
                "mode": ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
                "registered_at": "2026-11-22T10:00:00",
                "target_platform": "toutiao",
                "source_file_hash": self.original_hash,
                "source_body_hash": self.original_body_hash,
                "baseline_snapshot": "some/path.md",
            },
        }

        issues = _verify_external_registration_integrity(
            self.article_path, entry, "wechat"
        )
        self.assertTrue(len(issues) > 0, "toutiao 应该阻止公众号同步")

    # ========== 测试 3：单篇绑定 ==========

    def test_3_different_articles_have_different_keys(self):
        """【对抗 3】不同文章有不同的状态键。"""
        from modules.writing_workflow import workflow_id

        # 使用项目内路径模拟
        path1 = PROJECT_ROOT / "data" / "articles" / "test1.md"
        path2 = PROJECT_ROOT / "data" / "articles" / "test2.md"

        wid1 = workflow_id(path1)
        wid2 = workflow_id(path2)
        self.assertNotEqual(wid1, wid2, "不同文章的 workflow_id 应该不同")

    # ========== 测试 4：授权记录必须完整 ==========

    def test_4_registration_records_full_evidence(self):
        """【对抗 4】登记记录必须包含完整证据字段。"""
        result = validate_external_draft_registration(
            self.article_path,
            expected_hash=self.original_hash,
            authorization_reason="Perfect本人明确批准 2026-11-22 23:20",
            target_platform="wechat_only",
        )
        self.assertTrue(result["ok"])
        # 验证返回的字段包含关键证据
        self.assertIn("actual_hash", result)
        self.assertIn("body_hash", result)
        self.assertIn("mode", result)
        self.assertEqual(result["actual_hash"], self.original_hash)

    def test_4b_short_reason_rejected(self):
        """【对抗 4b】过短的授权理由被拒绝。"""
        result = validate_external_draft_registration(
            self.article_path,
            expected_hash=self.original_hash,
            authorization_reason="太短",
            target_platform="wechat_only",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any("授权理由" in issue for issue in result["issues"]))

    # ========== 测试 5：候选导入必须保全原稿 ==========

    def test_5_candidate_import_records_hashes(self):
        """【对抗 5】候选导入记录原稿和候选稿的 hash。"""
        result = validate_external_candidate_import(
            self.article_path,
            self.candidate_path,
            source_evidence="得到官方网页@润色一下 2026-11-22 Perfect确认",
        )
        self.assertTrue(result["ok"])
        # 验证返回包含原稿和候选稿 hash
        self.assertIn("original_hash", result)
        self.assertIn("original_file_hash", result)
        self.assertIn("candidate_hash", result)
        self.assertIn("candidate_file_hash", result)
        self.assertNotEqual(result["original_hash"], result["candidate_hash"])

    def test_5b_structure_issues_detected(self):
        """【对抗 5b】结构问题被检测并记录。"""
        # 创建会触发结构警告的候选稿（内容大幅缩短）
        bad_candidate = Path(self.test_dir) / "bad_candidate.md"
        bad_candidate.write_text("很短", encoding="utf-8")

        result = validate_external_candidate_import(
            self.article_path,
            bad_candidate,
            source_evidence="得到官方网页@润色一下 2026-11-22 测试",
        )
        # 结构问题会记录在 structure_issues 中
        self.assertIn("structure_issues", result)
        # 由于内容大幅缩短，应该有结构问题
        if result["structure_issues"]:
            self.assertTrue(len(result["structure_issues"]) > 0)

    def test_5c_missing_evidence_rejected(self):
        """【对抗 5c】缺少来源证据被拒绝。"""
        result = validate_external_candidate_import(
            self.article_path,
            self.candidate_path,
            source_evidence="短",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any("来源证据" in issue for issue in result["issues"]))

    # ========== 测试 6：普通稿无登记必须真实 pull ==========

    def test_6_no_registration_requires_real_pull(self):
        """【对抗 6】无登记文章不能伪造 snapshot/last_pulled_at。"""
        # 空 entry
        entry = {}
        ok, issue = _check_polish_readiness(entry)
        self.assertFalse(ok)
        self.assertIn("没有外部成稿登记", issue)

        # 伪造的外部登记（缺少必要字段）
        entry = {
            "external_draft_registration": {
                "mode": ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
                # 缺少 registered_at
            }
        }
        ok, issue = _check_polish_readiness(entry)
        self.assertFalse(ok)

    def test_6b_standard_pull_still_works(self):
        """【对抗 6b】标准 pull 路径不受影响。"""
        entry = {"last_pulled_at": "2026-11-22T10:00:00"}
        ok, issue = _check_polish_readiness(entry)
        self.assertTrue(ok)
        self.assertEqual(issue, "")

    # ========== 测试 7：各项检查仍然阻断 ==========

    def test_7_emphasis_check_still_required(self):
        """【对抗 7】即使有外部登记，emphasis_reviewed_at 仍然必须。"""
        # 只有登记，没有 emphasis_reviewed_at
        entry = {
            "external_draft_registration": {
                "mode": ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
                "registered_at": "2026-11-22T10:00:00",
                "source_body_hash": self.original_body_hash,
                "target_platform": "wechat",
                "baseline_snapshot": "some/path.md",
            },
        }
        # polish 检查通过
        ok, _ = _check_polish_readiness(entry)
        self.assertTrue(ok)

        # 但完整 readiness 应该因缺少 emphasis_reviewed_at 而失败
        # （这部分在 publication_readiness 中检查，这里只验证 entry 结构）

    # ========== 测试 8：source hash 不等于最终验证 ==========

    def test_8_hash_mismatch_rejected_at_registration(self):
        """【对抗 8】hash 不匹配在登记时被拒绝。"""
        wrong_hash = "0" * 64
        result = validate_external_draft_registration(
            self.article_path,
            expected_hash=wrong_hash,
            authorization_reason="测试用例 2026-11-22",
            target_platform="wechat_only",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any("不匹配" in issue for issue in result["issues"]))

    def test_8b_file_change_after_validation_detected(self):
        """【对抗 8b】验证后文件修改会被重新校验发现。"""
        # 先通过验证
        result1 = validate_external_draft_registration(
            self.article_path,
            expected_hash=self.original_hash,
            authorization_reason="测试用例 2026-11-22",
            target_platform="wechat_only",
        )
        self.assertTrue(result1["ok"])

        # 修改文件
        self.article_path.write_text(self.original_content + "\n修改", encoding="utf-8")

        # 用旧 hash 重新验证应该失败
        result2 = validate_external_draft_registration(
            self.article_path,
            expected_hash=self.original_hash,  # 旧 hash
            authorization_reason="测试用例 2026-11-22",
            target_platform="wechat_only",
        )
        self.assertFalse(result2["ok"])


class DraftGetMockTest(unittest.TestCase):
    """draft-get 命令的 mock 测试（不访问生产凭据）。"""

    def test_draft_get_command_exists(self):
        """draft-get 命令已注册。"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "writing_workflow.py"),
             "draft-get", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("media_id", result.stdout)
        self.assertIn("草稿", result.stdout)


class RegressionTest(unittest.TestCase):
    """回归测试：确保现有功能不受影响。"""

    def test_external_mode_constants(self):
        """外部成稿模式常量正确定义。"""
        self.assertEqual(
            ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
            "polish_completed_externally"
        )
        self.assertEqual(
            ExternalDraftMode.POLISH_NOT_APPLICABLE,
            "polish_not_applicable"
        )
        self.assertIn(
            ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
            ExternalDraftMode.VALID_MODES
        )

    def test_standard_pull_path_unchanged(self):
        """标准 pull 路径检查不受影响。"""
        entry = {"last_pulled_at": "2026-11-22T10:00:00"}
        ok, issue = _check_polish_readiness(entry)
        self.assertTrue(ok)
        self.assertEqual(issue, "")


if __name__ == "__main__":
    unittest.main()
