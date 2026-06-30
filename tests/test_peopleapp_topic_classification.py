#!/usr/bin/env python3

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_peopleapp_opinion_hotspots.py"
SPEC = importlib.util.spec_from_file_location("peopleapp_topic_classification_test", SCRIPT)
assert SPEC and SPEC.loader
classifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(classifier)


def article(article_id, title, source, word_count=1000):
    return {
        "article_id": article_id,
        "title": title,
        "source_name": source,
        "date": "2026-06-30",
        "word_count": word_count,
        "content": title,
    }


def test_generic_china_or_ai_words_do_not_merge_unrelated_articles():
    topics = classifier.build_curated_topics(
        [
            article("1", "意大利学者眼中的“中国全球领导力”", "人民日报"),
            article("2", "AI时代，真人微短剧该何去何从？", "经济日报"),
            article("3", "AI时代，哲学教授为何屡屡被赞？", "南方都市报"),
        ]
    )
    assert topics == []


def test_fire_safety_keeps_paper_maintenance_event_separate():
    topics = classifier.build_curated_topics(
        [
            article("1", "灭火器“纸面维保”泛滥，安全监管不能流于纸面", "新京报"),
            article("2", "灭火器“纸面维保”，症结在于“纸面监管”", "北京青年报"),
            article("3", "灭火器合格证6毛一张，“纸面维保”包不住火", "中工网"),
            article("4", "养老机构消防，岂能“一问三不知”", "光明网"),
        ]
    )
    topic = next(item for item in topics if item["topic"] == "灭火器纸面维保治理")
    assert topic["article_count"] == 3
    assert topic["media_count"] == 3
    assert all("养老机构" not in item["title"] for item in topic["articles"])


def test_same_source_repost_is_counted_once():
    topics = classifier.build_curated_topics(
        [
            article("1", "停车费叫停“向上取整”，小账本里有大民生", "光明论微信公号"),
            article("2", "停车计费算清“明白账”，精细治理温暖城市街角", "上观新闻"),
            article("3", "停车计费，就该“分秒必争”", "人民日报客户端", 1000),
            article("4", "人民锐评 | 停车计费，就该“分秒必争”", "人民日报客户端", 90),
        ]
    )
    topic = next(item for item in topics if item["topic"] == "停车计费规则透明化")
    assert topic["article_count"] == 3
    assert topic["media_count"] == 3
    assert topic["category"] == "城市治理与公共服务"


def test_incomplete_body_is_not_counted_as_topic_support():
    topics = classifier.build_curated_topics(
        [
            article("1", "意大利学者眼中的“中国全球领导力”", "人民日报"),
            article("2", "和音：“创新红利”，推动中国机遇再升级", "人民日报"),
            article("3", "国际论坛：理解当代中国需要兼具历史纵深与现实视野", "人民日报", 43),
        ]
    )
    topic = next(item for item in topics if item["topic"] == "理解中国发展与世界机遇")
    assert topic["article_count"] == 2
    assert all(item["article_id"] != "3" for item in topic["articles"])
