#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from modules.peopleapp_opinion import (
    build_opinion_article_id,
    html_fragment_to_markdown,
    normalize_article,
    parse_peopleapp_url,
    source_url,
)


def test_parse_peopleapp_url():
    content_id, rel_id = parse_peopleapp_url(
        "https://www.peopleapp.com/column/30052476000-500007564442"
    )
    assert content_id == "30052476000"
    assert rel_id == "500007564442"


def test_build_opinion_article_id():
    assert (
        build_opinion_article_id("2026-06-24", "30052476000", "500007564442")
        == "peopleapp_opinion_20260624_30052476000_500007564442"
    )


def test_html_fragment_to_markdown_extracts_text_and_images():
    markdown, text, image_urls = html_fragment_to_markdown(
        "<p>小区停车计费要讲清规则。</p>"
        "<p><strong>停车计费</strong>不能糊涂。</p>"
        '<p><img src="https://example.com/a.jpg"/></p>'
    )
    assert "小区停车计费要讲清规则。" in text
    assert "**停车计费**不能糊涂。" in markdown
    assert image_urls == ["https://example.com/a.jpg"]


def test_normalize_article_keeps_peopleapp_fields_separate():
    detail = {
        "newsId": 30052476000,
        "newsTitle": "停车计费岂能糊里糊涂",
        "newsSourceName": "人民日报客户端",
        "publishTime": "2026-06-24 10:00:00",
        "newsSummary": "停车计费规则要透明。",
        "newsContent": "<p>停车计费不能糊里糊涂，规则要公开透明。</p>",
        "reLInfo": {"relId": 500007564442},
        "authorList": [{"authorName": "张三"}],
        "shareInfo": {"shareCoverUrl": "https://example.com/cover.jpg"},
    }
    list_item = {
        "objectId": 30052476000,
        "relId": 500007564442,
        "source": "人民日报客户端",
    }

    article = normalize_article(detail, list_item)

    assert article["source"] == "peopleapp_opinion"
    assert article["article_id"] == "peopleapp_opinion_20260624_30052476000_500007564442"
    assert article["content_id"] == "30052476000"
    assert article["rel_id"] == "500007564442"
    assert article["section_name"] == "APP-锐评"
    assert article["source_name"] == "人民日报客户端"
    assert article["source_url"] == source_url("30052476000", "500007564442")
    assert "停车计费不能糊里糊涂" in article["content"]
