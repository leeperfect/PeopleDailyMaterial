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
SELF_MEDIA_ROOT = ROOT / "data" / "data_analysis"
DEFAULT_OUTPUT_PATH = SELF_MEDIA_ROOT / "overview.md"
DEFAULT_REPORT_DIR = SELF_MEDIA_ROOT / "reports"


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


def channel_totals_for_dates(
    conn: sqlite3.Connection,
    batch_id: str,
    dates: list[str],
) -> dict[str, int]:
    if not dates:
        return {}
    placeholders = ",".join("?" for _ in dates)
    rows = conn.execute(
        f"""
        SELECT channel, SUM(read_users) AS read_users
        FROM channel_daily_reads
        WHERE batch_id = ?
          AND date IN ({placeholders})
          AND channel <> '全部'
        GROUP BY channel
        """,
        (batch_id, *dates),
    ).fetchall()
    return {row["channel"]: int(row["read_users"] or 0) for row in rows}


def comparison_dates(
    current_daily: dict[str, sqlite3.Row],
    previous_daily: dict[str, sqlite3.Row],
    previous: Batch | None,
) -> tuple[list[str], list[str], list[str], bool]:
    """Return current, baseline, backfill dates and whether this is a long export."""
    if not previous:
        return [], [], [], False

    is_extended = len(current_daily) > max(37, len(previous_daily) + 7)
    if not is_extended:
        return (
            sorted(set(current_daily) - set(previous_daily)),
            sorted(set(previous_daily) - set(current_daily)),
            [],
            False,
        )

    current_dates = sorted(date for date in current_daily if date > previous.end_date)
    backfill_dates = sorted(date for date in current_daily if date < previous.start_date)
    if not current_dates:
        return [], [], backfill_dates, True
    earlier_dates = sorted(date for date in current_daily if date < current_dates[0])
    baseline_dates = earlier_dates[-len(current_dates) :]
    return current_dates, baseline_dates, backfill_dates, True


def period_metrics(rows: list[sqlite3.Row]) -> dict[str, float]:
    days = len(rows)
    reads = sum(row["read_users"] or 0 for row in rows)
    shares = sum(row["share_users"] or 0 for row in rows)
    favorites = sum(row["wechat_favorites"] or 0 for row in rows)
    posts = sum(row["published_count"] or 0 for row in rows)
    return {
        "days": days,
        "reads": reads,
        "shares": shares,
        "favorites": favorites,
        "posts": posts,
        "avg_reads": reads / days if days else 0,
        "avg_shares": shares / days if days else 0,
        "avg_favorites": favorites / days if days else 0,
    }


def fmt_int(value: int | float | None) -> str:
    return f"{int(value or 0):,}"


def fmt_float(value: float | None) -> str:
    return f"{float(value or 0):,.1f}"


def fmt_delta(current: float, previous: float) -> str:
    delta = current - previous
    if not previous:
        return f"{delta:+,.1f}"
    return f"{delta:+,.1f} ({delta / previous:+.1%})"


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

    new_dates, removed_dates, backfill_dates, is_extended = comparison_dates(
        latest_daily, previous_daily, previous
    )
    new_daily = [latest_daily[date] for date in new_dates]
    baseline_source = latest_daily if is_extended else previous_daily
    removed_daily = [baseline_source[date] for date in removed_dates]
    new_reads = sum(row["read_users"] or 0 for row in new_daily)
    new_posts = sum(row["published_count"] or 0 for row in new_daily)
    new_shares = sum(row["share_users"] or 0 for row in new_daily)
    new_favorites = sum(row["wechat_favorites"] or 0 for row in new_daily)
    removed_reads = sum(row["read_users"] or 0 for row in removed_daily)
    removed_shares = sum(row["share_users"] or 0 for row in removed_daily)
    removed_favorites = sum(row["wechat_favorites"] or 0 for row in removed_daily)

    top_articles = sorted(
        latest_articles.values(),
        key=lambda row: row["read_users"] or 0,
        reverse=True,
    )[:10]
    new_titles = sorted(
        (
            row
            for title, row in latest_articles.items()
            if title not in previous_articles
            and (
                not is_extended
                or not previous
                or (row["publish_date"] or "") > previous.end_date
            )
        ),
        key=lambda row: row["read_users"] or 0,
        reverse=True,
    )
    growth_rows = []
    for title, current in latest_articles.items():
        old = previous_articles.get(title)
        if not old:
            continue
        if is_extended and previous and (current["publish_date"] or "") < previous.start_date:
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
    new_channel_totals = {row["channel"]: int(row["read_users"] or 0) for row in channel_rows}
    removed_channel_totals = (
        channel_totals_for_dates(
            conn,
            latest.batch_id if is_extended else previous.batch_id,
            removed_dates,
        )
        if previous
        else {}
    )
    latest_30 = period_metrics(
        [latest_daily[date] for date in sorted(latest_daily)[-30:]]
    )
    previous_30 = period_metrics(
        [previous_daily[date] for date in sorted(previous_daily)[-30:]]
    ) if previous else {}
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
    if is_extended:
        lines.extend(
            [
                "",
                f"> 最新批次是 {latest.days} 天长周期导出，表中合计和日均用于全周期回看；周度变化统一按相邻等长日期和最近30天计算。",
            ]
        )

    lines.extend(["", "## 本次新增日期", ""])
    if new_dates:
        if is_extended and backfill_dates:
            lines.extend(
                [
                    f"- 本批是 {latest.days} 天长周期回看；另补充 {backfill_dates[0]} 至 {backfill_dates[-1]} 的 {len(backfill_dates)} 个历史日期。",
                    "- 历史补录只用于长期回看，不计入本周增长。",
                ]
            )
        lines.extend(
            [
                f"- 新增日期：{new_dates[0]} 至 {new_dates[-1]}，共 {len(new_dates)} 天。",
                f"- 新增日期内发表 {new_posts} 篇，日阅读人数合计 {fmt_int(new_reads)}。",
                f"- 分享人数合计 {fmt_int(new_shares)}，微信收藏人数合计 {fmt_int(new_favorites)}。",
                "",
                "这里的“新增日期”只保留上次截止日之后的日期，是周度复盘最可靠的新增区间。",
            ]
        )
        if channel_rows:
            lines.extend(["", "### 新增日期渠道表现", ""])
            if removed_channel_totals:
                lines.extend(
                    markdown_table(
                        ["渠道", "上期对照" if is_extended else "移出区间", "新增区间", "变化"],
                        [
                            [
                                row["channel"],
                                fmt_int(removed_channel_totals.get(row["channel"], 0)),
                                fmt_int(new_channel_totals.get(row["channel"], 0)),
                                f"{new_channel_totals.get(row['channel'], 0) - removed_channel_totals.get(row['channel'], 0):+,}",
                            ]
                            for row in channel_rows
                        ],
                        ["---", "---:", "---:", "---:"],
                    )
                )
            else:
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
        current_avg = latest_30["avg_reads"] if is_extended else latest.avg_reads
        previous_avg = previous_30["avg_reads"] if is_extended else previous.avg_reads
        avg_delta = current_avg - previous_avg
        direction = "增加" if avg_delta >= 0 else "减少"
        lines.extend(
            [
                "",
                "## 滚动周期变化",
                "",
                f"- {'最新30天' if is_extended else '最新周期'}日均阅读 {fmt_float(current_avg)}，较上一批最近30天{direction} {fmt_float(abs(avg_delta))}。",
                "- 长周期导出不直接与30天批次比较；本行统一使用最近30天口径。" if is_extended else "- 两批起止日期不同，这里反映滚动窗口热度变化，不作为严格同比增长率。",
            ]
        )
        if new_daily and removed_daily:
            new_avg = new_reads / len(new_daily)
            removed_avg = removed_reads / len(removed_daily)
            lines.extend(
                [
                    "",
                    "### 相邻等长区间比较" if is_extended else "### 滚动窗口替换拆解",
                    "",
                    f"- {'上期对照' if is_extended else '移出区间'}：{removed_dates[0]} 至 {removed_dates[-1]}，{len(removed_dates)} 天，阅读 {fmt_int(removed_reads)}。",
                    f"- 新增区间：{new_dates[0]} 至 {new_dates[-1]}，{len(new_dates)} 天，阅读 {fmt_int(new_reads)}。",
                    f"- 新增区间日均阅读 {fmt_float(new_avg)}，相对{'上期对照' if is_extended else '移出区间'}日均阅读 {fmt_float(removed_avg)}，变化 {fmt_delta(new_avg, removed_avg)}。",
                    f"- 分享由 {fmt_int(removed_shares)} 变为 {fmt_int(new_shares)}，收藏由 {fmt_int(removed_favorites)} 变为 {fmt_int(new_favorites)}。",
                    "",
                    "这个比较使用相邻、等长日期，避免长周期历史补录影响周度判断。" if is_extended else "这个拆解用于判断滚动窗口变化究竟来自新一周走强或走弱，还是仅由统计区间移动造成。",
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


def generate_batch_reports(db_path: Path, report_dir: Path) -> list[Path]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    batches = fetch_batches(conn)
    report_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    for index, batch in enumerate(batches):
        previous = batches[index - 1] if index > 0 else None
        current_daily = daily_rows(conn, batch.batch_id)
        previous_daily = daily_rows(conn, previous.batch_id) if previous else {}
        current_articles = article_rows(conn, batch.batch_id)
        previous_articles = article_rows(conn, previous.batch_id) if previous else {}
        new_dates, removed_dates, backfill_dates, is_extended = comparison_dates(
            current_daily, previous_daily, previous
        )
        new_daily = [current_daily[date] for date in new_dates]
        baseline_source = current_daily if is_extended else previous_daily
        removed_daily = [baseline_source[date] for date in removed_dates]
        current_30 = period_metrics(
            [current_daily[date] for date in sorted(current_daily)[-30:]]
        )
        previous_30 = period_metrics(
            [previous_daily[date] for date in sorted(previous_daily)[-30:]]
        ) if previous else {}
        top_articles = sorted(
            current_articles.values(),
            key=lambda row: row["read_users"] or 0,
            reverse=True,
        )[:15]
        new_titles = sorted(
            (
                row
                for title, row in current_articles.items()
                if title not in previous_articles
                and (
                    not is_extended
                    or not previous
                    or (row["publish_date"] or "") > previous.end_date
                )
            ),
            key=lambda row: row["read_users"] or 0,
            reverse=True,
        )
        growth_rows: list[tuple[int, str, int, int]] = []
        for title, current in current_articles.items():
            old = previous_articles.get(title)
            if not old:
                continue
            if is_extended and previous and (current["publish_date"] or "") < previous.start_date:
                continue
            delta = (current["read_users"] or 0) - (old["read_users"] or 0)
            growth_rows.append((delta, title, old["read_users"] or 0, current["read_users"] or 0))
        growth_rows.sort(reverse=True)

        peak_pool = (
            [current_daily[date] for date in sorted(current_daily)[-30:]]
            if is_extended
            else list(current_daily.values())
        )
        peak_days = sorted(
            peak_pool,
            key=lambda row: row["read_users"] or 0,
            reverse=True,
        )[:5]
        channel_dates = sorted(current_daily)[-30:] if is_extended else []
        channel_date_filter = ""
        channel_params: tuple[Any, ...] = (batch.batch_id,)
        if channel_dates:
            placeholders = ",".join("?" for _ in channel_dates)
            channel_date_filter = f" AND date IN ({placeholders})"
            channel_params = (batch.batch_id, *channel_dates)
        channel_rows = conn.execute(
            f"""
            SELECT channel, SUM(read_users) AS read_users
            FROM channel_daily_reads
            WHERE batch_id = ? AND channel <> '全部'{channel_date_filter}
            GROUP BY channel
            ORDER BY read_users DESC
            """,
            channel_params,
        ).fetchall()
        new_channel_totals = channel_totals_for_dates(conn, batch.batch_id, new_dates)
        removed_channel_totals = (
            channel_totals_for_dates(
                conn,
                batch.batch_id if is_extended else previous.batch_id,
                removed_dates,
            )
            if previous
            else {}
        )
        source = conn.execute(
            """
            SELECT source_filename, raw_path, export_dir, imported_at
            FROM import_batches
            WHERE batch_id = ?
            """,
            (batch.batch_id,),
        ).fetchone()

        top = top_articles[0] if top_articles else None
        top_new = new_titles[0] if new_titles else None
        growth_leader = growth_rows[0] if growth_rows else None
        lines = [
            f"# 微信公众号详细运营分析报告：{batch.end_date}",
            "",
            f"> 统计范围：{batch.start_date} 至 {batch.end_date}。本报告对应批次 `{batch.batch_id}`，并与上一批连续比较。",
            "",
            "## 一、运营结论速读",
            "",
            f"- 本周期发表 {batch.published} 篇，日阅读人数合计 {fmt_int(batch.total_reads)}，日均 {fmt_float(batch.avg_reads)}。",
            f"- 日均分享 {fmt_float(batch.avg_shares)}，日均微信收藏 {fmt_float(batch.avg_favorites)}。",
        ]
        if top:
            lines.append(
                f"- 当前阅读最高文章为 **{top['title']}**，阅读人数 {fmt_int(top['read_users'])}。"
            )
        if previous:
            current_avg = current_30["avg_reads"] if is_extended else batch.avg_reads
            previous_avg = previous_30["avg_reads"] if is_extended else previous.avg_reads
            avg_delta = current_avg - previous_avg
            direction = "增加" if avg_delta >= 0 else "减少"
            lines.append(
                f"- 相比上一批最近30天，日均阅读{direction} {fmt_float(abs(avg_delta))}；"
                + ("本批为长周期回看，已统一到最近30天口径。" if is_extended else "由于统计窗口移动，该数值用于判断近期热度，不作为严格同比。")
            )
            if new_dates:
                new_reads = sum(row["read_users"] or 0 for row in new_daily)
                new_posts = sum(row["published_count"] or 0 for row in new_daily)
                lines.append(
                    f"- 本次周度新增 {len(new_dates)} 个日期（{new_dates[0]} 至 {new_dates[-1]}），新增区间发表 {new_posts} 篇，日阅读人数合计 {fmt_int(new_reads)}。"
                )
                if removed_daily:
                    removed_reads = sum(row["read_users"] or 0 for row in removed_daily)
                    net_replacement = new_reads - removed_reads
                    contribution = "多" if net_replacement >= 0 else "少"
                    cycle_direction = "回升" if net_replacement >= 0 else "回落"
                    if is_extended:
                        lines.append(
                            f"- 与紧邻上一个等长区间相比，本周{contribution}贡献 {fmt_int(abs(net_replacement))} 阅读，近期表现{cycle_direction}。"
                        )
                    else:
                        lines.append(
                            f"- 滚动窗口中，新加入日期比移出日期{contribution}贡献 {fmt_int(abs(net_replacement))} 阅读；这是本周期{cycle_direction}的直接统计来源。"
                        )
            if is_extended and backfill_dates:
                lines.append(
                    f"- 本批另补录 {backfill_dates[0]} 至 {backfill_dates[-1]} 的 {len(backfill_dates)} 个历史日期，只用于长期回看，不计入本周增长。"
                )
        else:
            lines.append("- 这是数据链的首个批次，作为后续周度比较的基线。")

        lines.extend(
            [
                "",
                "## 二、数据范围与归档",
                "",
                f"- 后台源文件：`{source['source_filename']}`",
                f"- 原始表位置：`{source['raw_path']}`",
                f"- 数据明细位置：`{source['export_dir']}`",
                f"- 导入时间：{source['imported_at']}",
                f"- 每日趋势：{batch.days} 天；来源概况收录文章：{len(current_articles)} 篇。",
                "",
                "## 三、核心指标",
                "",
            ]
        )
        metric_rows = [
            ["统计天数", 30 if is_extended else batch.days, previous.days if previous else "-", "-"],
            ["发表篇数", int(current_30["posts"]) if is_extended else batch.published, previous.published if previous else "-", "-"],
            ["日阅读人数合计", fmt_int(current_30["reads"] if is_extended else batch.total_reads), fmt_int(previous.total_reads) if previous else "-", "-"],
            [
                "日均阅读",
                fmt_float(current_30["avg_reads"] if is_extended else batch.avg_reads),
                fmt_float(previous_30["avg_reads"] if is_extended else previous.avg_reads) if previous else "-",
                fmt_delta(current_30["avg_reads"] if is_extended else batch.avg_reads, previous_30["avg_reads"] if is_extended else previous.avg_reads) if previous else "-",
            ],
            [
                "日均分享",
                fmt_float(current_30["avg_shares"] if is_extended else batch.avg_shares),
                fmt_float(previous_30["avg_shares"] if is_extended else previous.avg_shares) if previous else "-",
                fmt_delta(current_30["avg_shares"] if is_extended else batch.avg_shares, previous_30["avg_shares"] if is_extended else previous.avg_shares) if previous else "-",
            ],
            [
                "日均收藏",
                fmt_float(current_30["avg_favorites"] if is_extended else batch.avg_favorites),
                fmt_float(previous_30["avg_favorites"] if is_extended else previous.avg_favorites) if previous else "-",
                fmt_delta(current_30["avg_favorites"] if is_extended else batch.avg_favorites, previous_30["avg_favorites"] if is_extended else previous.avg_favorites) if previous else "-",
            ],
        ]
        if is_extended:
            lines.extend(
                [
                    f"- 本批完整导出共 {batch.days} 天、发表 {batch.published} 篇、阅读 {fmt_int(batch.total_reads)}；下表统一展示最近30天可比口径。",
                    "",
                ]
            )
        lines.extend(
            markdown_table(
                ["指标", "本批", "上批", "变化"],
                metric_rows,
                ["---", "---:", "---:", "---:"],
            )
        )

        lines.extend(["", "## 四、相邻等长区间比较" if is_extended else "## 四、滚动窗口替换拆解", ""])
        if previous and new_daily and removed_daily:
            new_reads = sum(row["read_users"] or 0 for row in new_daily)
            new_shares = sum(row["share_users"] or 0 for row in new_daily)
            new_favorites = sum(row["wechat_favorites"] or 0 for row in new_daily)
            new_posts = sum(row["published_count"] or 0 for row in new_daily)
            removed_reads = sum(row["read_users"] or 0 for row in removed_daily)
            removed_shares = sum(row["share_users"] or 0 for row in removed_daily)
            removed_favorites = sum(row["wechat_favorites"] or 0 for row in removed_daily)
            removed_posts = sum(row["published_count"] or 0 for row in removed_daily)
            new_avg = new_reads / len(new_daily)
            removed_avg = removed_reads / len(removed_daily)
            replacement_delta = new_reads - removed_reads
            contribution = "多" if replacement_delta >= 0 else "少"
            cycle_direction = "回升" if replacement_delta >= 0 else "回落"
            strength = "高于" if new_avg >= removed_avg else "低于"
            lines.extend(
                markdown_table(
                    ["窗口区间", "日期", "天数", "发文", "阅读", "日均阅读", "分享", "收藏"],
                    [
                        ["上期对照" if is_extended else "移出本批", f"{removed_dates[0]} 至 {removed_dates[-1]}", len(removed_dates), removed_posts, fmt_int(removed_reads), fmt_float(removed_avg), fmt_int(removed_shares), fmt_int(removed_favorites)],
                        ["新加入本批", f"{new_dates[0]} 至 {new_dates[-1]}", len(new_dates), new_posts, fmt_int(new_reads), fmt_float(new_avg), fmt_int(new_shares), fmt_int(new_favorites)],
                    ],
                    ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:"],
                )
            )
            lines.extend(
                [
                    "",
                    f"新增区间比{'上期对照' if is_extended else '移出区间'}{contribution} {fmt_int(abs(replacement_delta))} 阅读；新增区间日均阅读变化 {fmt_delta(new_avg, removed_avg)}。因此，近期表现{cycle_direction}，新增日期阅读强度{strength}{'上期对照区间' if is_extended else '被移出日期'}。",
                ]
            )
        elif previous:
            lines.append("- 两批没有形成可直接比较的移出区间与新增区间。")
        else:
            lines.append("- 首批数据暂不进行窗口替换拆解。")

        lines.extend(["", "## 五、最近30天阅读高峰" if is_extended else "## 五、阅读高峰", ""])
        lines.extend(
            markdown_table(
                ["日期", "阅读人数", "分享人数", "收藏人数", "发文篇数"],
                [
                    [
                        row["date"],
                        fmt_int(row["read_users"]),
                        fmt_int(row["share_users"]),
                        fmt_int(row["wechat_favorites"]),
                        row["published_count"] or 0,
                    ]
                    for row in peak_days
                ],
                ["---", "---:", "---:", "---:", "---:"],
            )
        )

        lines.extend(["", "## 六、本次新增日期表现", ""])
        if previous and new_daily:
            lines.extend(
                markdown_table(
                    ["日期", "阅读人数", "分享人数", "收藏人数", "发文篇数"],
                    [
                        [
                            row["date"],
                            fmt_int(row["read_users"]),
                            fmt_int(row["share_users"]),
                            fmt_int(row["wechat_favorites"]),
                            row["published_count"] or 0,
                        ]
                        for row in new_daily
                    ],
                    ["---", "---:", "---:", "---:", "---:"],
                )
            )
        elif previous:
            lines.append("- 本批没有比上一批增加新的统计日期，请核对导出时间范围。")
        else:
            lines.append("- 首批数据作为连续分析基线，从下一批开始识别新增日期。")

        lines.extend(["", "## 七、最近30天渠道表现" if is_extended else "## 七、渠道表现", ""])
        lines.extend(
            markdown_table(
                ["渠道", "周期阅读人数合计"],
                [[row["channel"], fmt_int(row["read_users"])] for row in channel_rows],
                ["---", "---:"],
            )
        )
        lines.extend(
            [
                "",
                "不同渠道可能存在重复读者，渠道数据用于判断传播来源强弱，不与“全部”简单相加。",
            ]
        )
        if new_channel_totals and removed_channel_totals:
            channels = sorted(
                set(new_channel_totals) | set(removed_channel_totals),
                key=lambda channel: new_channel_totals.get(channel, 0),
                reverse=True,
            )
            lines.extend(["", "### 新增区间与上期对照渠道变化" if is_extended else "### 新增区间与移出区间渠道变化", ""])
            lines.extend(
                markdown_table(
                    ["渠道", "上期对照" if is_extended else "移出区间", "新增区间", "变化"],
                    [
                        [
                            channel,
                            fmt_int(removed_channel_totals.get(channel, 0)),
                            fmt_int(new_channel_totals.get(channel, 0)),
                            f"{new_channel_totals.get(channel, 0) - removed_channel_totals.get(channel, 0):+,}",
                        ]
                        for channel in channels
                    ],
                    ["---", "---:", "---:", "---:"],
                )
            )
            lines.extend(
                [
                    "",
                    "该表比较相邻等长日期，用于识别本周变化由哪些阅读来源推动。" if is_extended else "该表比较等长的新增与移出日期区间，用于识别本次滚动窗口变化由哪些阅读来源推动。",
                ]
            )
        lines.extend(["", "## 八、文章阅读排名", ""])
        lines.extend(
            markdown_table(
                ["排名", "发布日期", "文章", "阅读人数", "推荐阅读", "推荐约比"],
                [
                    [
                        rank,
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
                    for rank, row in enumerate(top_articles, start=1)
                ],
                ["---:", "---", "---", "---:", "---:", "---:"],
            )
        )

        lines.extend(["", "## 九、本批新出现文章", ""])
        if previous and new_titles:
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
        elif previous:
            lines.append("- 来源概况中未识别到相对上一批新出现的文章。")
        else:
            lines.append("- 首批数据不区分新旧文章，后续批次开始连续追踪。")

        lines.extend(
            [
                "",
                "“本批新出现”表示首次进入后台来源概况，不一定等同于本周刚发布。来源概况通常只展示部分文章，不能替代完整的单篇内容明细。",
                "",
                "## 十、同篇文章长尾变化",
                "",
            ]
        )
        if growth_rows:
            lines.extend(
                markdown_table(
                    ["文章", "上批阅读", "本批阅读", "净变化"],
                    [
                        [title, fmt_int(old), fmt_int(current), f"{delta:+,}"]
                        for delta, title, old, current in growth_rows[:15]
                    ],
                    ["---", "---:", "---:", "---:"],
                )
            )
            lines.extend(
                [
                    "",
                    "后台数据为滚动窗口，较早文章的首发阅读可能逐步移出统计范围，因此这里记录的是快照净变化，不一定等于一周新增阅读。",
                ]
            )
        else:
            lines.append("- 暂无上一批同篇文章数据可供比较。")

        lines.extend(["", "## 十一、选题与运营判断", ""])
        judgment_items: list[str] = []
        if previous and new_daily and removed_daily:
            read_change = (
                100 * (new_reads - removed_reads) / removed_reads
                if removed_reads
                else 0
            )
            share_change = (
                100 * (new_shares - removed_shares) / removed_shares
                if removed_shares
                else 0
            )
            favorite_change = (
                100 * (new_favorites - removed_favorites) / removed_favorites
                if removed_favorites
                else 0
            )
            post_comparison = (
                f"少发 {removed_posts - new_posts} 篇"
                if new_posts < removed_posts
                else (
                    f"多发 {new_posts - removed_posts} 篇"
                    if new_posts > removed_posts
                    else "发文数量相同"
                )
            )
            judgment_items.append(
                f"**发文效率**：新增区间在{post_comparison}的情况下，阅读较{'上期对照' if is_extended else '移出区间'}变化 {read_change:+.1f}%，"
                f"分享变化 {share_change:+.1f}%，收藏变化 {favorite_change:+.1f}%。"
            )

        if new_channel_totals and removed_channel_totals:
            channel_changes = sorted(
                (
                    (
                        new_channel_totals.get(channel, 0)
                        - removed_channel_totals.get(channel, 0),
                        channel,
                        removed_channel_totals.get(channel, 0),
                        new_channel_totals.get(channel, 0),
                    )
                    for channel in set(new_channel_totals) | set(removed_channel_totals)
                ),
                reverse=True,
            )
            positive_changes = [row for row in channel_changes if row[0] > 0]
            if positive_changes:
                delta, channel, old_value, new_value = positive_changes[0]
                rate = 100 * delta / old_value if old_value else 0
                judgment_items.append(
                    f"**最大渠道驱动**：{channel}阅读由 {fmt_int(old_value)} 增至 {fmt_int(new_value)}，"
                    f"增加 {fmt_int(delta)}（{rate:+.1f}%），是新增区间最明显的渠道变化。"
                )

        no_post_days = [
            row
            for row in new_daily
            if (row["published_count"] or 0) == 0 and (row["read_users"] or 0) > 0
        ]
        if no_post_days:
            strongest_no_post_day = max(
                no_post_days,
                key=lambda row: row["read_users"] or 0,
            )
            judgment_items.append(
                f"**长尾证据**：新增区间有 {len(no_post_days)} 个无发文日仍产生阅读，"
                f"其中 {strongest_no_post_day['date']} 达到 {fmt_int(strongest_no_post_day['read_users'])}，"
                "说明历史文章仍在持续获得推荐、转发或搜索流量。"
            )

        if top:
            judgment_items.append(
                f"**当前最强样本**：{top['title']} 是本周期阅读最高的文章，应拆解它的母题、标题结构和读者收益，作为后续选题参照。"
            )
        if top_new:
            judgment_items.append(
                f"**新内容观察**：{top_new['title']} 是本批新出现文章中阅读最高的一篇，当前阅读 {fmt_int(top_new['read_users'])}，下一批需继续观察其推荐和长尾增长。"
            )
        if growth_leader:
            judgment_items.append(
                f"**长尾样本**：{growth_leader[1]} 较上批净增 {fmt_int(growth_leader[0])}，说明旧文仍有持续分发或转发价值。"
            )
        judgment_items.extend(
            [
                "**选题方法**：优先复用“考试高频母题 + 明确读者收益 + 纠正常见答题误区”的组合，同时避免只更换标题、不更换分析切口。",
                "**评价方法**：高阅读判断吸引力，高推荐判断平台扩散力，高分享和高收藏判断教学价值与读者留存价值。",
            ]
        )
        lines.extend(
            [
                *[
                    f"{number}. {item}"
                    for number, item in enumerate(judgment_items, start=1)
                ],
                "",
                "## 十二、下一期追踪清单",
                "",
                "- 检查本批新出现文章在下一批的净增长和推荐变化。",
                "- 检查高阅读文章是否还能持续获得推荐、会话、朋友圈和搜索流量。",
                "- 将表现稳定的母题拆成新角度，进入公众号选题池继续验证。",
                "- 尽量补充“单篇内容分析”明细，以覆盖来源概况未展示的文章。",
                "",
                "## 十三、数据限制",
                "",
                "- 本报告依据公众号后台导出的滚动周期数据，不把重叠日期重复累计为本周新增。",
                "- 来源概况未必覆盖期间全部发文，未出现的文章不能直接判定为零阅读。",
                "- 推荐约比用于观察推荐渠道强弱；不同渠道可能存在读者交叉。",
                *( ["- 本批为长周期导出，周度结论只使用上次截止日后的新增日期，并与紧邻等长区间比较；全周期合计不与30天批次直接环比。"] if is_extended else [] ),
                "",
            ]
        )

        output_path = report_dir / f"{batch.batch_id}.md"
        deep_analysis_marker = "<!-- CODEX_DEEP_ANALYSIS -->"
        deep_analysis = ""
        if output_path.exists():
            existing = output_path.read_text(encoding="utf-8")
            if deep_analysis_marker in existing:
                deep_analysis = existing.split(deep_analysis_marker, 1)[1].strip()

        report_text = "\n".join(lines)
        if deep_analysis:
            report_text = (
                f"{report_text.rstrip()}\n\n{deep_analysis_marker}\n\n"
                f"{deep_analysis}\n"
            )
        output_path.write_text(report_text, encoding="utf-8")
        outputs.append(output_path)

    conn.close()
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="生成微信公众号运营数据连续分析总览")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="公众号运营核心分析库")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="总览 Markdown 输出路径")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="每批详细运营报告目录")
    args = parser.parse_args()
    output = generate_report(Path(args.db_path), Path(args.output))
    reports = generate_batch_reports(Path(args.db_path), Path(args.report_dir))
    try:
        display_path = output.relative_to(ROOT)
    except ValueError:
        display_path = output
    print(f"已更新连续分析总览：{display_path}")
    print(f"已更新详细运营报告：{len(reports)} 份")


if __name__ == "__main__":
    main()
