#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从人民日报 APP 评论库梳理官媒评论热点。

默认规则：同一事件/话题下，至少 3 个不同来源媒体发表评论，视为热点。
输出 Markdown 与 CSV，便于教学选题和后续人工复核。
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import jieba

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.article_identity import normalize_date
from modules.peopleapp_opinion import EXPORT_DIR, TIMEZONE, load_articles

HOTSPOT_DIR = EXPORT_DIR / "hotspots"

COLUMN_PREFIXES = [
    "人民锐评",
    "人民时评",
    "人民论坛",
    "今日谈",
    "钟声",
    "和音",
    "经济热点快评",
    "人民日报刊文",
    "夜读",
    "零时差",
]

STOPWORDS = {
    "人民日报",
    "人民日报客户端",
    "评论",
    "锐评",
    "刊文",
    "快评",
    "为何",
    "为什么",
    "如何",
    "不能",
    "不应",
    "就该",
    "没有",
    "不是",
    "一个",
    "一种",
    "这个",
    "这件事",
    "说开去",
    "总书记",
    "来之不易",
}

MERGE_PATTERNS = [
    ("停车计费规则", ["停车", "计费"]),
    ("教师减负", ["教师", "减负"]),
    ("高考志愿填报", ["高考", "志愿"]),
    ("开屏广告治理", ["开屏", "广告"]),
    ("研学治理", ["研学", "流量"]),
    ("算法与青年婚育观", ["算法", "婚育"]),
    ("营商环境", ["营商", "环境"]),
    ("粮食安全", ["粮食", "丰收"]),
]


def clean_title(title: str) -> str:
    text = str(title or "")
    for prefix in COLUMN_PREFIXES:
        text = re.sub(rf"^\s*{re.escape(prefix)}\s*[|｜：:丨-]?\s*", "", text)
    text = re.sub(r"[“”\"《》\[\]（）()]", "", text)
    return text.strip()


def normalize_source(source: str) -> str:
    text = str(source or "").strip()
    text = text.replace("微信公众号", "微信公号")
    return text or "未知来源"


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def pattern_anchor(article: Dict) -> str:
    text = compact_text(" ".join([article.get("title", ""), article.get("summary", ""), article.get("content", "")[:300]]))
    for label, words in MERGE_PATTERNS:
        if all(word in text for word in words):
            return label
    return ""


def tokens_for_article(article: Dict) -> Set[str]:
    title = clean_title(article.get("title", ""))
    base_text = f"{title} {article.get('summary', '')}"
    tokens: Set[str] = set()

    for token in jieba.lcut(base_text):
        token = token.strip()
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        if re.fullmatch(r"\d+", token):
            continue
        tokens.add(token)

    for keyword in article.get("keywords") or []:
        keyword = str(keyword).strip()
        if len(keyword) >= 2 and keyword not in STOPWORDS:
            tokens.add(keyword)

    title_words = [
        word
        for word in jieba.lcut(title)
        if len(word.strip()) >= 2 and word.strip() not in STOPWORDS and not re.fullmatch(r"\d+", word.strip())
    ]
    for left, right in zip(title_words, title_words[1:]):
        phrase = f"{left}{right}"
        if 4 <= len(phrase) <= 12:
            tokens.add(phrase)

    anchor = pattern_anchor(article)
    if anchor:
        tokens.add(anchor)
    return tokens


def similarity(left: Set[str], right: Set[str]) -> float:
    if not left or not right:
        return 0.0
    shared = left & right
    if not shared:
        return 0.0
    overlap = len(shared) / max(1, min(len(left), len(right)))
    strong_shared = any(len(token) >= 4 for token in shared)
    if strong_shared and len(shared) >= 1:
        return max(overlap, 0.35)
    return overlap


def build_clusters(articles: List[Dict], min_similarity: float) -> List[List[Dict]]:
    article_tokens = {article["article_id"]: tokens_for_article(article) for article in articles}
    parent = {article["article_id"]: article["article_id"] for article in articles}

    def find(article_id: str) -> str:
        while parent[article_id] != article_id:
            parent[article_id] = parent[parent[article_id]]
            article_id = parent[article_id]
        return article_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for index, left in enumerate(articles):
        for right in articles[index + 1 :]:
            left_id = left["article_id"]
            right_id = right["article_id"]
            left_anchor = pattern_anchor(left)
            right_anchor = pattern_anchor(right)
            if left_anchor and left_anchor == right_anchor:
                union(left_id, right_id)
                continue
            if similarity(article_tokens[left_id], article_tokens[right_id]) >= min_similarity:
                union(left_id, right_id)

    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for article in articles:
        grouped[find(article["article_id"])].append(article)

    return [group for group in grouped.values() if len(group) >= 2]


def representative_topic(group: List[Dict]) -> str:
    anchors = [pattern_anchor(article) for article in group]
    anchors = [anchor for anchor in anchors if anchor]
    if anchors:
        return max(set(anchors), key=anchors.count)

    token_counts: Dict[str, int] = defaultdict(int)
    for article in group:
        for token in tokens_for_article(article):
            token_counts[token] += 1
    candidates = [
        (token, count)
        for token, count in token_counts.items()
        if count >= 2 and len(token) >= 2 and token not in STOPWORDS
    ]
    if candidates:
        candidates.sort(key=lambda item: (-item[1], -len(item[0]), item[0]))
        return candidates[0][0]
    return clean_title(group[0].get("title", "未命名热点"))


def source_set(group: List[Dict]) -> Set[str]:
    return {normalize_source(article.get("source_name") or article.get("source")) for article in group}


def summarize_group(group: List[Dict]) -> Dict:
    group = sorted(group, key=lambda item: (item.get("date", ""), item.get("title", "")))
    sources = sorted(source_set(group))
    dates = [article.get("date", "") for article in group if article.get("date")]
    return {
        "topic": representative_topic(group),
        "media_count": len(sources),
        "article_count": len(group),
        "sources": sources,
        "start_date": min(dates) if dates else "",
        "end_date": max(dates) if dates else "",
        "articles": group,
    }


def default_range(days: int) -> Tuple[str, str]:
    today = datetime.now(TIMEZONE).date()
    start = today - timedelta(days=max(1, days) - 1)
    return start.isoformat(), today.isoformat()


def select_articles(args) -> List[Dict]:
    if args.all:
        return load_articles(limit=args.limit)
    start = normalize_date(args.start) if args.start else None
    end = normalize_date(args.end) if args.end else None
    if not start and not end:
        start, end = default_range(args.days)
    return load_articles(start_date=start, end_date=end, limit=args.limit)


def write_markdown(hotspots: List[Dict], candidates: List[Dict], args) -> Path:
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    path = HOTSPOT_DIR / f"peopleapp_opinion_hotspots_{timestamp}.md"
    lines = [
        "# 人民日报 APP 评论库官媒热点梳理",
        "",
        f"- 生成时间：{datetime.now(TIMEZONE).isoformat(timespec='seconds')}",
        f"- 热点标准：至少 {args.min_media} 个不同来源媒体发表评论",
        f"- 最低相似度：{args.min_similarity}",
        f"- 热点数量：{len(hotspots)}",
        f"- 候选数量：{len(candidates)}",
        "",
    ]

    lines.extend(["## 已达热点标准", ""])
    if not hotspots:
        lines.append("本次范围内暂无达到标准的热点。")
        lines.append("")
    for index, item in enumerate(hotspots, 1):
        lines.extend(
            [
                f"### {index}. {item['topic']}",
                "",
                f"- 时间：{item['start_date']} 至 {item['end_date']}",
                f"- 媒体数：{item['media_count']}",
                f"- 文章数：{item['article_count']}",
                f"- 来源：{'、'.join(item['sources'])}",
                "",
            ]
        )
        for article in item["articles"]:
            lines.append(
                f"- {article.get('date', '')}｜{normalize_source(article.get('source_name') or article.get('source'))}｜"
                f"[{article.get('title', '无标题')}]({article.get('source_url') or article.get('url') or ''})"
            )
        lines.append("")

    lines.extend(["## 候选热点", ""])
    if not candidates:
        lines.append("暂无候选热点。")
        lines.append("")
    for index, item in enumerate(candidates, 1):
        lines.extend(
            [
                f"### {index}. {item['topic']}",
                "",
                f"- 时间：{item['start_date']} 至 {item['end_date']}",
                f"- 媒体数：{item['media_count']}",
                f"- 文章数：{item['article_count']}",
                f"- 来源：{'、'.join(item['sources'])}",
                "",
            ]
        )
        for article in item["articles"]:
            lines.append(
                f"- {article.get('date', '')}｜{normalize_source(article.get('source_name') or article.get('source'))}｜"
                f"{article.get('title', '无标题')}"
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_csv(items: List[Dict]) -> Path:
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    path = HOTSPOT_DIR / f"peopleapp_opinion_hotspots_{timestamp}.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "topic",
                "status",
                "media_count",
                "article_count",
                "start_date",
                "end_date",
                "sources",
                "article_id",
                "date",
                "source",
                "title",
                "url",
            ]
        )
        for item in items:
            for article in item["articles"]:
                writer.writerow(
                    [
                        item["topic"],
                        item["status"],
                        item["media_count"],
                        item["article_count"],
                        item["start_date"],
                        item["end_date"],
                        "、".join(item["sources"]),
                        article.get("article_id", ""),
                        article.get("date", ""),
                        normalize_source(article.get("source_name") or article.get("source")),
                        article.get("title", ""),
                        article.get("source_url") or article.get("url") or "",
                    ]
                )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="导出人民日报 APP 评论库官媒热点")
    parser.add_argument("--days", type=int, default=7, help="默认回看最近几天，默认 7 天")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--all", action="store_true", help="分析 APP 评论库全部文章")
    parser.add_argument("--limit", type=int, help="限制参与分析的文章数量")
    parser.add_argument("--min-media", type=int, default=3, help="热点至少需要几个不同媒体，默认 3")
    parser.add_argument("--min-similarity", type=float, default=0.22, help="文章归并最低相似度，默认 0.22")
    args = parser.parse_args()

    articles = select_articles(args)
    clusters = [summarize_group(group) for group in build_clusters(articles, args.min_similarity)]
    clusters.sort(key=lambda item: (-item["media_count"], -item["article_count"], item["topic"]))

    hotspots = [item for item in clusters if item["media_count"] >= args.min_media]
    candidates = [item for item in clusters if item["media_count"] < args.min_media]
    for item in hotspots:
        item["status"] = "hotspot"
    for item in candidates:
        item["status"] = "candidate"

    markdown_path = write_markdown(hotspots, candidates, args)
    csv_path = write_csv(hotspots + candidates)

    print("官媒评论热点梳理完成")
    print(f"参与文章：{len(articles)}")
    print(f"达到热点标准：{len(hotspots)}")
    print(f"候选热点：{len(candidates)}")
    print(f"Markdown：{markdown_path.relative_to(PROJECT_ROOT)}")
    print(f"CSV：{csv_path.relative_to(PROJECT_ROOT)}")
    if hotspots:
        print("\n已达热点标准：")
        for item in hotspots:
            print(f"- {item['topic']}：{item['media_count']} 家媒体，{item['article_count']} 篇")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
