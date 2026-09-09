#!/usr/bin/env python3
"""把 collect_wechat_content_api.py 采集的 JSON 导入公众号运营数据库。

入库设计（对应"数据、逻辑分离"原则，采集器只产 JSON，这里负责建模）：

1. article_detail_30d（新表）——单篇文章"发表后30天"完整指标。
   为什么不复用 article_content_stats：那张表装的是 Excel 导出的"任意窗口"数据，
   而 API 详情页是固定的发表后30天同龄窗口，语义不同，分开建模查询才不歧义。

2. user_growth_daily ——每日新关注/取关/净增/累计，date 为主键，重复导入覆盖。

3. channel_daily_reads ——账号级每日分渠道阅读，作为一个新批次写入，
   与既有 Excel 批次同表同结构，长期数据链只有一条查询路径。
   scene 数字到中文渠道名的映射不写死：用同一日期范围内既有批次的
   渠道总量做数值匹配得出，匹配不上才回退到约定映射。

用法：
    python3 scripts/import_wechat_api_stats.py 2026-06-08 2026-09-06
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "core" / "wechat_official_account.sqlite"

# 约定映射（仅当数值匹配失败时兜底）：微信场景码的常见含义
SCENE_FALLBACK = {
    0: "公众号消息", 1: "朋友圈", 2: "聊天会话", 4: "推荐",
    5: "搜一搜", 6: "公众号主页", 7: "其他", 9999: "全部",
}


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS article_detail_30d (
            msg_id TEXT NOT NULL,
            item_idx INTEGER NOT NULL,
            title TEXT,
            publish_date TEXT,
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            read_users INTEGER,
            avg_read_minutes REAL,
            completion_rate REAL,
            new_followers INTEGER,
            listen_users INTEGER,
            share_users INTEGER,
            collect_users INTEGER,
            wow_users INTEGER,
            like_users INTEGER,
            comment_count INTEGER,
            reward_yuan REAL,
            deliver_users INTEGER,
            first_share_users INTEGER,
            share_driven_read_users INTEGER,
            channel_pct_json TEXT,
            window_read_users INTEGER,
            tendency_30d TEXT,
            interaction_unit TEXT,
            note TEXT,
            raw_json TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            PRIMARY KEY (msg_id, item_idx, window_start, window_end)
        );

        CREATE TABLE IF NOT EXISTS user_growth_daily (
            date TEXT PRIMARY KEY,
            new_followers INTEGER,
            unfollow_users INTEGER,
            net_followers INTEGER,
            cumulative_followers INTEGER,
            raw_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_article_detail_date ON article_detail_30d(publish_date);
        """
    )


def import_article_details(conn: sqlite3.Connection, rows: list[dict],
                           window_start: str, window_end: str) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    count = 0
    for row in rows:
        if row.get("error"):
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO article_detail_30d VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                str(row["msg_id"]), row["item_idx"], row.get("title"),
                (row.get("ref_date") or "").replace("/", "-"),
                window_start, window_end,
                _int(row.get("read_uv")), row.get("avg_read_minutes"),
                row.get("completion_rate"), _int(row.get("new_followers")),
                _int(row.get("listen_uv")), _int(row.get("share_uv")),
                _int(row.get("collect_uv")), _int(row.get("wow_uv")),
                _int(row.get("like_uv")), _int(row.get("comment_count")),
                row.get("reward_yuan"), _int(row.get("deliver_uv")),
                _int(row.get("first_share_uv")), _int(row.get("share_driven_read_uv")),
                json.dumps(row.get("channel_pct") or {}, ensure_ascii=False),
                _int(row.get("window_read_uv")), row.get("tendency_30d"),
                row.get("interaction_unit"), row.get("note"),
                json.dumps(row, ensure_ascii=False), now,
            ),
        )
        count += 1
    return count


def import_user_growth(conn: sqlite3.Connection, payload: dict) -> int:
    entries = []
    for category in payload.get("category_list", []):
        entries.extend(category.get("list", []))
    count = 0
    for entry in entries:
        if not entry.get("date"):
            continue
        conn.execute(
            "INSERT OR REPLACE INTO user_growth_daily VALUES (?, ?, ?, ?, ?, ?)",
            (
                entry["date"], entry.get("new_user"), entry.get("cancel_user"),
                entry.get("netgain_user"), entry.get("cumulate_user"),
                json.dumps(entry, ensure_ascii=False),
            ),
        )
        count += 1
    return count


def match_scene_names(conn: sqlite3.Connection, tendency: list[dict],
                      ref_start: str, ref_end: str) -> dict[int, str]:
    """用同一日期范围内既有 Excel 批次的渠道总量，反推 scene 数字的渠道名。

    为什么不写死 scene=4 是"推荐"：微信从未公开承诺场景码含义，
    写死一旦错位就是静默错数据；数值匹配只要两边总量对得上就是铁证。
    """
    ref = conn.execute(
        """
        SELECT channel, SUM(read_users) FROM channel_daily_reads
        WHERE batch_id = ? GROUP BY channel
        """,
        (f"{ref_start}_to_{ref_end}_tendency",),
    ).fetchall()
    if not ref:
        return dict(SCENE_FALLBACK)

    scene_totals: dict[int, int] = {}
    for row in tendency:
        day = datetime.fromtimestamp(row["date"]).strftime("%Y-%m-%d")
        if ref_start <= day <= ref_end:
            scene_totals[row["scene"]] = scene_totals.get(row["scene"], 0) + row.get("read_uv", 0)

    # 总量最接近的 scene <-> channel 两两配对（允许 3% 以内的口径差）
    mapping: dict[int, str] = {}
    remaining = dict(ref)
    for scene, total in sorted(scene_totals.items(), key=lambda kv: -kv[1]):
        best = min(remaining.items(), key=lambda kv: abs(kv[1] - total), default=None)
        if best and total > 0 and abs(best[1] - total) / total < 0.03:
            mapping[scene] = best[0]
            del remaining[best[0]]
    for scene, name in SCENE_FALLBACK.items():
        mapping.setdefault(scene, name)
    return mapping


def import_channel_tendency(conn: sqlite3.Connection, payload: dict,
                            window_start: str, window_end: str,
                            source_dir: Path) -> tuple[int, dict[int, str]]:
    tendency = payload.get("all_article_stat_tendency", {}).get("list", [])
    if not tendency:
        return 0, {}

    # 找与采集窗口尾部重叠的既有批次做场景匹配（最新批次窗口 = 采集窗口后 30 天）
    mapping = match_scene_names(conn, tendency, "2026-08-08", "2026-09-06")

    batch_id = f"{window_start}_to_{window_end}_api_tendency"
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("DELETE FROM channel_daily_reads WHERE batch_id = ?", (batch_id,))
    conn.execute("DELETE FROM import_batches WHERE batch_id = ?", (batch_id,))
    conn.execute(
        "INSERT INTO import_batches VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            batch_id, "channel_tendency.json（内容分析 API）",
            _sha256(source_dir / "channel_tendency.json"),
            str(source_dir.relative_to(ROOT)), "", now,
            json.dumps({"source": "wechat_mp_api", "scene_mapping":
                        {str(k): v for k, v in mapping.items()}}, ensure_ascii=False),
        ),
    )
    count = 0
    for row_no, row in enumerate(tendency, start=1):
        day = datetime.fromtimestamp(row["date"]).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO channel_daily_reads VALUES (?, ?, ?, ?, ?, ?)",
            (batch_id, row_no, day, mapping.get(row["scene"], f"scene_{row['scene']}"),
             row.get("read_uv"), json.dumps(row, ensure_ascii=False)),
        )
        count += 1
    return count, mapping


def _int(value: object) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def main() -> None:
    parser = argparse.ArgumentParser(description="导入公众号内容 API 采集数据")
    parser.add_argument("start", help="窗口开始日期 YYYY-MM-DD")
    parser.add_argument("end", help="窗口结束日期 YYYY-MM-DD")
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    args = parser.parse_args()

    source_dir = (ROOT / "data" / "data_analysis" / "raw" / "monetization"
                  / "content_api" / f"{args.start}_{args.end}")
    if not source_dir.exists():
        raise FileNotFoundError(f"采集目录不存在：{source_dir}，请先运行 collect_wechat_content_api.py")

    conn = sqlite3.connect(str(args.db_path))
    create_tables(conn)

    with conn:
        details = json.loads((source_dir / "article_details.json").read_text(encoding="utf-8"))
        n1 = import_article_details(conn, details, args.start, args.end)
        print(f"article_detail_30d：导入 {n1} 篇")

        growth = json.loads((source_dir / "user_growth.json").read_text(encoding="utf-8"))
        n2 = import_user_growth(conn, growth)
        print(f"user_growth_daily：导入 {n2} 天")

        tendency = json.loads((source_dir / "channel_tendency.json").read_text(encoding="utf-8"))
        n3, mapping = import_channel_tendency(conn, tendency, args.start, args.end, source_dir)
        print(f"channel_daily_reads：导入 {n3} 行，场景映射 {mapping}")

    conn.close()


if __name__ == "__main__":
    main()
