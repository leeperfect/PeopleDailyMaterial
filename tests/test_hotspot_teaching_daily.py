#!/usr/bin/env python3

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_hotspot_teaching_daily.py"
SPEC = importlib.util.spec_from_file_location("build_hotspot_teaching_daily_test", SCRIPT)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def topic_fixture():
    return {
        "topic_id": "topic-ai",
        "topic": "AI应用风险与智能向善治理",
        "category": "数字治理与消费权益",
        "angle": "AI进入教育、投资和测评场景后，要防诈骗、防滥用、守真实、明边界。",
        "status": "热点",
        "priority": "S",
        "media_count": 4,
        "article_count": 4,
        "start_date": "2026-07-12",
        "end_date": "2026-07-27",
        "sources": ["人民日报客户端", "经济日报"],
        "app_articles": [
            {
                "article_id": "app-1",
                "date": "2026-07-12",
                "source_name": "人民日报客户端",
                "title": "AI智能荐股？投资没有一键致富",
                "url": "https://example.com/app-1",
            },
            {
                "article_id": "app-2",
                "date": "2026-07-14",
                "source_name": "经济日报",
                "title": "校准智能向善航向",
                "url": "https://example.com/app-2",
            },
        ],
    }


class HotspotTeachingDailyTest(unittest.TestCase):
    def test_paper_support_requires_real_keyword_overlap(self):
        topic = topic_fixture()
        paper_articles = [
        {
            "article_id": "paper-ai",
            "date": "2026-07-20",
            "title": "校准智能向善航向",
            "summary": "人工智能进入教育和投资场景，需要明确平台责任与技术边界。",
            "content": "人工智能治理既要鼓励创新，也要保护消费者权益。",
            "section_name": "评论",
            "category": "政治",
            "source_url": "https://example.com/paper-ai",
        },
        {
            "article_id": "paper-rain",
            "date": "2026-07-20",
            "title": "抓紧抓实防汛救灾",
            "summary": "多地迎来强降雨。",
            "content": "要加强监测预警和应急处置。",
            "section_name": "要闻",
            "category": "政治",
            "source_url": "https://example.com/paper-rain",
        },
        ]
        matched = builder.match_paper_support(topic, paper_articles)
        self.assertEqual([item["article_id"] for item in matched], ["paper-ai"])
        self.assertIn(matched[0]["relation_role"], {"规范表达", "政策依据", "延伸母题"})
        self.assertIn("主题关键词相符", matched[0]["match_reason"])


    def test_card_has_two_teaching_layers_and_source_separation(self):
        topic = topic_fixture()
        app_articles = [
        {
            **topic["app_articles"][0],
            "source_url": "https://example.com/app-1",
            "content": "AI荐股不能承诺一键致富，投资者需要警惕新型诈骗。",
            "summary": "",
        }
        ]
        supports = [
        {
            "article_id": "paper-ai",
            "date": "2026-07-20",
            "title": "让人工智能向善发展",
            "summary": "治理与创新需要同步推进。",
            "section_name": "评论",
            "source_url": "https://example.com/paper-ai",
            "confidence": 0.85,
            "match_reason": "主题关键词相符：人工智能、治理",
            "relation_role": "规范表达",
        }
        ]
        card = builder.build_card(topic, app_articles, supports)
        self.assertTrue(card["quick_intro"])
        self.assertIn("AI主题研学订单同比增长370%", card["news_overview"])
        self.assertNotIn("本地人民日报APP评论库", card["news_overview"])
        self.assertNotIn("人民日报客户端", card["news_overview"])
        self.assertNotIn("《AI智能荐股？投资没有一键致富》", card["news_overview"])
        self.assertGreaterEqual(len(card["news_overview"]), 240)
        self.assertLessEqual(len(card["news_overview"]), 420)
        self.assertEqual(len(card["key_facts"]), 1)
        self.assertEqual(len(card["core_judgments"]), 3)
        self.assertEqual(set(card["analysis_framework"]), {"问题", "原因", "影响", "对策"})
        self.assertTrue(all(len(items) == 3 for items in card["analysis_framework"].values()))
        self.assertEqual(card["paper_support"][0]["article_id"], "paper-ai")
        self.assertEqual(len(card["classroom_questions"]), 3)


    def test_daily_lead_prefers_topic_that_changed_that_day(self):
        with tempfile.TemporaryDirectory() as directory:
            output_db = Path(directory) / "hotspot_teaching.sqlite"
            conn = builder.connect_output(output_db)
            topics = [
                {
                    "topic_id": "long-running",
                    "topic": "长期持续的高优先级热点",
                    "category": "公共安全与监管",
                    "status": "热点",
                    "priority": "S",
                    "media_count": 20,
                    "article_count": 20,
                    "start_date": "2026-07-01",
                    "end_date": "2026-08-07",
                },
                {
                    "topic_id": "changed-today",
                    "topic": "当天发生阶段变化的热点",
                    "category": "数字治理与消费权益",
                    "status": "热点",
                    "priority": "A",
                    "media_count": 3,
                    "article_count": 3,
                    "start_date": "2026-07-20",
                    "end_date": "2026-07-27",
                },
            ]
            builder.build_editions(conn, topics, "2026-08-11T12:00:00")
            row = conn.execute(
                "SELECT topic_ids_json FROM daily_editions WHERE edition_date='2026-07-27'"
            ).fetchone()
            conn.close()
            self.assertEqual(json.loads(row[0])[0], "changed-today")

    def test_today_fallback_prefers_most_recent_topic(self):
        with tempfile.TemporaryDirectory() as directory:
            output_db = Path(directory) / "hotspot_teaching.sqlite"
            conn = builder.connect_output(output_db)
            topics = [
                {
                    "topic_id": "older-high-priority",
                    "topic": "较早的高优先级热点",
                    "category": "公共安全与监管",
                    "status": "热点",
                    "priority": "S",
                    "media_count": 20,
                    "article_count": 20,
                    "start_date": "2026-07-01",
                    "end_date": "2026-08-07",
                },
                {
                    "topic_id": "recent-update",
                    "topic": "昨天刚获得新来源的热点",
                    "category": "教育与青年成长",
                    "status": "热点",
                    "priority": "A",
                    "media_count": 4,
                    "article_count": 4,
                    "start_date": "2026-07-20",
                    "end_date": "2026-08-11",
                },
            ]
            class FixedDate(builder.date):
                @classmethod
                def today(cls):
                    return cls(2026, 8, 12)

            with patch.object(builder, "date", FixedDate):
                builder.build_editions(conn, topics, "2026-08-12T12:00:00")
            row = conn.execute(
                "SELECT topic_ids_json FROM daily_editions WHERE edition_date='2026-08-12'"
            ).fetchone()
            conn.close()
            self.assertEqual(json.loads(row[0])[0], "recent-update")


    def test_export_bundle_is_portable(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            output_root = tmp_path / "hotspot_teaching"
            output_db = output_root / "core" / "hotspot_teaching.sqlite"
            export_root = output_root / "exports"
            site_root = output_root / "site"
            web_root = tmp_path / "web"
            web_root.mkdir()
            for name in ("index.html", "styles.css", "app.js"):
                (web_root / name).write_text(name, encoding="utf-8")

            with patch.object(builder, "OUTPUT_ROOT", output_root), \
                 patch.object(builder, "OUTPUT_DB", output_db), \
                 patch.object(builder, "EXPORT_ROOT", export_root), \
                 patch.object(builder, "SITE_ROOT", site_root), \
                 patch.object(builder, "WEB_ROOT", web_root):
                conn = builder.connect_output(output_db)
                now = "2026-08-11T12:00:00"
                conn.execute(
        """INSERT INTO hotspot_topics VALUES
        ('topic-1','停车计费规则透明化','城市治理与公共服务','收费规则要透明',
         '热点','A',3,3,0,'2026-08-10','2026-08-11','[]','source_curated',?,?)""",
        (now, now),
                )
                conn.execute(
        """INSERT INTO teaching_cards VALUES
        ('card-topic-1','topic-1',1,'一句话','约三百字热点概览','值得讲','[]','[]','课堂入口','[]','争议',
         '[]','[]','{}','[]','{}','[]','[]','[]','editorial_preview','',NULL,?,?)""",
        (now, now),
                )
                conn.execute(
        """INSERT INTO daily_editions VALUES
        ('daily_20260811','2026-08-11',1,'日报','教学判断','[\"topic-1\"]',3,0,5,'preview',?,?)""",
        (now, now),
                )
                conn.commit()
                conn.close()

                manifest = builder.export_bundle(
                    {"topics": 1, "sources": 0, "links": 0, "cards": 1, "daily_editions": 1, "weekly_editions": 0}
                )
                expected = {
                    "hotspot_topics.jsonl", "source_articles.jsonl", "topic_article_links.csv",
                    "teaching_cards.jsonl", "daily_editions.jsonl", "weekly_editions.jsonl",
                    "manifest.json", "hotspot_teaching.sqlite",
                }
                self.assertTrue(expected.issubset({path.name for path in export_root.iterdir()}))
                self.assertEqual(manifest["counts"]["topics"], 1)
                payload = json.loads((site_root / "data.json").read_text(encoding="utf-8"))
                self.assertEqual(payload["topics"][0]["card"]["quick_intro"], "一句话")


if __name__ == "__main__":
    unittest.main()
