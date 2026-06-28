#!/usr/bin/env python3
"""生成微信公众号运营数据的连续分析总览。"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "core" / "wechat_official_account.sqlite"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "analysis" / "wechat-official-account" / "overview.md"


@dataclass
class Batch:
    batch_id: str
    imported_at: str
    start_date: str
    end_date: str
    days: int
    published: int
    total_reads: int
    avg_reads: float
    avg_shares: float
    avg_favorites: float


def fetch_batches(conn: sqlite3.Connection) -> list[Batch]:
    rows = conn.execute(
        """
        SELECT
            b.batch_id,
            b.imported_at,
            MIN(d.date) AS start_date,
            MAX(d.date) AS end_date,
            COUNT(d.row_no) AS days,
            COALESCE(SUM(d.published_count), 0) AS published,
            COALESCE(SUM(d.read_users), 0) AS total_reads,
            COALESCE(AVG(d.read_users), 0) AS avg_reads,
            COALESCE(AVG(d.share_users), 0) AS avg_shares,
            COALESCE(AVG(d.wechat_favorites), 0) AS avg_favorites
        FROM import_batches b
        JOIN daily_trends d ON d.batch_id = b.batch_id
        GROUP BY b.batch_id, b.imported_at
        ORDER BY end_date, b.imported_at
        """
    ).fetchall()
    return [Batch(*row) for row in rows]


def daily_rows(conn: sqlite3.Connection, batch_id: str) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT date, published_count, read_users, share_users, wechat_favorites
        FROM daily_trends
        WHERE batch_id = ?
        ORDER BY date
        """,
        (batch_id,),
    ).fetchall()
    return {row["date"]: row for row in rows}


def article_rows(conn: sqlite3.Connection, batch_id: str) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT
            total.title,
            total.publish_date,
            total.read_users,
            recommended.read_users AS recommended_reads
        FROM source_overview total
        LEFT JOIN source_overview recommended
          ON recommended.batch_id = total.batch_id
         AND recommended.title = total.title
         AND recommended.channel = '推荐'
        WHERE total.batch_id = ? AND total.channel = '全部'
        """,
        (batch_id,),
    ).fetchall()
    return {row["title"]: row for row in rows}


def fmt_int(value: int | float | None) -> str:
    return f"{int(value or 0):,}"


def fmt_float(value: float | None) -> str:
    return f"{float(value or 0):,.1f}"


def markdown_table(headers: list[str], rows: list[list[Any]], aligns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(aligns) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return lines


def generate_report(db_path: Path, output_path: Path) -> Path:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    batches = fetch_batches(conn)
    if not batches:
        raise ValueError("核心库中还没有可分析的公众号运营批次")

    latest = batches[-1]
    previous = batches[-2] if len(batches) > 1 else None
    latest_daily = daily_rows(conn, latest.batch_id)
    previous_daily = daily_rows(conn, previous.batch_id) if previous else {}
    latest_articles = article_rows(conn, latest.batch_id)
    previous_articles = article_rows(conn, previous.batch_id) if previous else {}

    new_dates = sorted(set(latest_daily) - set(previous_daily))
    new_daily = [latest_daily[date] for date in new_dates]
    new_reads = sum(row["read_users"] or 0 for row in new_daily)
    new_posts = sum(row["published_count"] or 0 for row in new_daily)
    new_shares = sum(row["share_users"] or 0 for row in new_daily)
    new_favorites = sum(row["wechat_favorites"] or 0 for row in new_daily)

    top_articles = sorted(
        latest_articles.values(),
        key=lambda row: row["read_users"] or 0,
        reverse=True,
    )[:10]
    new_titles = sorted(
        (row for title, row in latest_articles.items() if title not in previous_articles),
        key=lambda row: row["read_users"] or 0,
        reverse=True,
    )
    growth_rows = []
    for title, current in latest_articles.items():
        old = previous_articles.get(title)
        if not old:
            continue
        delta = (current["read_users"] or 0) - (old["read_users"] or 0)
        growth_rows.append((delta, title, old["read_users"] or 0, current["read_users"] or 0))
    growth_rows.sort(reverse=True)

    channel_rows: list[sqlite3.Row] = []
    if new_dates:
        placeholders = ",".join("?" for _ in new_dates)
        channel_rows = conn.execute(
            f"""
            SELECT channel, SUM(read_users) AS read_users
            FROM channel_daily_reads
            WHERE batch_id = ?
              AND date IN ({placeholders})
              AND channel <> '全部'
            GROUP BY channel
            ORDER BY read_users DESC
            """,
            (latest.batch_id, *new_dates),
        ).fetchall()
    conn.close()

    lines = [
        "# 微信公众号运营数据总览",
        "",
        "> 本页在每次导入后台数据后自动刷新，用于连续观察周度变化、文章长尾和选题表现。每一期原始表与批次记录仍单独保留。",
        "",
        "## 数据链",
        "",
        f"- 已归档批次：{len(batches)} 个",
        f"- 最早统计日期：{batches[0].start_date}",
        f"- 最新统计日期：{latest.end_date}",
        f"- 最新批次：`{latest.batch_id}`",
        "",
    ]
    lines.extend(
        markdown_table(
            ["批次截止日", "统计范围", "天数", "发文", "日阅读合计", "日均阅读", "日均分享", "日均收藏"],
            [
                [
                    batch.end_date,
                    f"{batch.start_date} 至 {batch.end_date}",
                    batch.days,
                    batch.published,
                    fmt_int(batch.total_reads),
                    fmt_float(batch.avg_reads),
                    fmt_float(batch.avg_shares),
                    fmt_float(batch.avg_favorites),
                ]
                for batch in reversed(batches)
            ],
            ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:"],
        )
    )

    lines.extend(["", "## 本次新增日期", ""])
    if new_dates:
        lines.extend(
            [
                f"- 新增日期：{new_dates[0]} 至 {new_dates[-1]}，共 {len(new_dates)} 天。",
                f"- 新增日期内发表 {new_posts} 篇，日阅读人数合计 {fmt_int(new_reads)}。",
                f"- 分享人数合计 {fmt_int(new_shares)}，微信收藏人数合计 {fmt_int(new_favorites)}。",
                "",
                "这里的“新增日期”是最新导出覆盖、上次导出尚未覆盖的日期，是周度复盘最可靠的新增区间。",
            ]
        )
        if channel_rows:
            lines.extend(["", "### 新增日期渠道表现", ""])
            lines.extend(
                markdown_table(
                    ["渠道", "阅读人数合计"],
                    [[row["channel"], fmt_int(row["read_users"])] for row in channel_rows],
                    ["---", "---:"],
                )
            )
            lines.extend(
                [
                    "",
                    "不同渠道可能存在重复读者，渠道阅读人数用于比较贡献强弱，不与“全部”简单相加。",
                ]
            )
    else:
        lines.append("- 最新批次没有比上一批多出新的日期，需检查导出范围是否正确。")

    if previous:
        avg_delta = latest.avg_reads - previous.avg_reads
        direction = "增加" if avg_delta >= 0 else "减少"
        lines.extend(
            [
                "",
                "## 滚动周期变化",
                "",
                f"- 最新周期日均阅读 {fmt_float(latest.avg_reads)}，较上一批{direction} {fmt_float(abs(avg_delta))}。",
                "- 两批起止日期不同，这里反映滚动窗口热度变化，不作为严格同比增长率。",
            ]
        )

    lines.extend(["", "## 最新文章表现", ""])
    lines.extend(
        markdown_table(
            ["排名", "发布日期", "文章", "阅读人数", "推荐阅读", "推荐约比"],
            [
                [
                    index,
                    row["publish_date"],
                    row["title"],
                    fmt_int(row["read_users"]),
                    fmt_int(row["recommended_reads"]) if row["recommended_reads"] is not None else "-",
                    (
                        f"{100 * row['recommended_reads'] / row['read_users']:.1f}%"
                        if row["recommended_reads"] is not None and row["read_users"]
                        else "-"
                    ),
                ]
                for index, row in enumerate(top_articles, start=1)
            ],
            ["---:", "---", "---", "---:", "---:", "---:"],
        )
    )

    lines.extend(["", "## 本批新出现文章", ""])
    if new_titles:
        lines.extend(
            markdown_table(
                ["发布日期", "文章", "阅读人数", "推荐阅读"],
                [
                    [
                        row["publish_date"],
                        row["title"],
                        fmt_int(row["read_users"]),
                        fmt_int(row["recommended_reads"]) if row["recommended_reads"] is not None else "-",
                    ]
                    for row in new_titles
                ],
                ["---", "---", "---:", "---:"],
            )
        )
    else:
        lines.append("- 后台“数据来源概况”中没有识别到相对上一批新增的文章。")
    lines.extend(
        [
            "",
            "注意：后台“数据来源概况”通常只展示部分文章，不等于完整发文清单。要逐篇评估全部文章，还需定期补充“单篇内容分析”明细。",
        ]
    )

    lines.extend(["", "## 同篇文章快照变化", ""])
    if growth_rows:
        lines.extend(
            markdown_table(
                ["文章", "上批阅读", "本批阅读", "净变化"],
                [
                    [title, fmt_int(old), fmt_int(current), f"{delta:+,}"]
                    for delta, title, old, current in growth_rows[:10]
                ],
                ["---", "---:", "---:", "---:"],
            )
        )
        lines.extend(
            [
                "",
                "净变化用于识别持续增长的长尾文章。由于后台导出是滚动窗口，较早文章的首发阅读可能移出统计范围，因此净变化不总等于一周新增阅读。",
            ]
        )

    lines.extend(
        [
            "",
            "## 固定分析方法",
            "",
            "1. 看新增日期：判断本周整体阅读、分享、收藏和渠道表现。",
            "2. 看新文章：判断本周哪些选题和标题获得较好起量。",
            "3. 看同篇文章净变化：识别仍被推荐、搜索或转发的长尾内容。",
            "4. 看滚动周期：判断账号整体热度是在上升、持平还是回落。",
            "5. 连续积累选题标签后，再比较就业、治理、经济、文化等母题的平均表现和稳定性。",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="生成微信公众号运营数据连续分析总览")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="公众号运营核心分析库")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="总览 Markdown 输出路径")
    args = parser.parse_args()
    output = generate_report(Path(args.db_path), Path(args.output))
    try:
        display_path = output.relative_to(ROOT)
    except ValueError:
        display_path = output
    print(f"已更新连续分析总览：{display_path}")


if __name__ == "__main__":
    main()
