#!/usr/bin/env python3
"""导入微信公众号变现与增长数据（文章收入 / 广告位 / 全部文章内容分析 / 用户增长）。

为什么单独建这个脚本，而不是塞进既有批次导入：
- 既有的趋势/搜索数据是"滚动窗口快照"，必须按批次（batch_id）留存；
- 收入、广告位、用户增长是"按日追加的事实"，同一日期重复导入应该覆盖而不是累加，
  所以这里用日期做主键全局入库，与批次解耦，避免滚动窗口重叠日期被重复计算。

支持的五类后台导出（表头自动识别，也允许 --kind 强制指定）：
1. ad_income_daily       流量主每日收入汇总（时间、拉取量、曝光量、收入……）
2. ad_slot_daily         流量主分广告位每日数据（广告位、拉取量、曝光量、收入……）
3. article_income        单篇文章收入（标题/链接、收入、曝光……）
4. article_content_stats 全部文章内容分析（标题/链接、阅读、分享、收藏、点赞、在看……）
5. user_growth_daily     用户增长（日期、新增关注、取消关注、净增、累计……）
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "core" / "wechat_official_account.sqlite"
DATA_ROOT = ROOT / "data" / "data_analysis"
RAW_MONETIZATION_DIR = DATA_ROOT / "raw" / "monetization"
EXPORT_MONETIZATION_DIR = DATA_ROOT / "exports" / "monetization"

VALID_KINDS = (
    "ad_income_daily",
    "ad_slot_daily",
    "article_income",
    "article_content_stats",
    "user_growth_daily",
)

# 后台导出的中文表头常有细微差异（全角括号、有无"人数/次数"后缀），
# 用别名表兜底，避免因为后台改一个表头就导入失败。
COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["时间", "日期", "统计日期"],
    "ad_requests": ["拉取量", "广告拉取量", "拉取次数"],
    "impressions": ["曝光量", "广告曝光量", "曝光次数"],
    "impression_rate": ["曝光率", "广告曝光率"],
    "clicks": ["点击量", "点击次数"],
    "click_rate": ["点击率"],
    "ecpm": ["eCPM（元）", "eCPM(元)", "eCPM", "千次曝光收益（元）", "千次曝光收益(元)", "千次曝光收益"],
    "income": ["累计收入（元）", "累计收入(元)", "累计收入", "收入（元）", "收入(元)", "收入", "收入金额（元）", "收入金额(元)", "收入金额"],
    "slot_name": ["广告位", "广告位类型", "广告位名称"],
    "title": ["文章标题", "标题", "文章名", "内容标题", "文章", "名称"],
    "url": ["链接", "文章链接", "url", "URL", "地址"],
    "publish_date": ["发布时间", "发表时间", "发布日期", "发表日期"],
    "read_users": ["阅读人数"],
    "read_times": ["阅读次数"],
    "share_users": ["分享人数", "分享次数"],
    "collect_users": ["收藏人数", "微信收藏人数", "收藏次数"],
    "like_users": ["点赞人数", "点赞次数"],
    "wow_users": ["在看人数", "在看次数"],
    "new_followers": ["新增关注", "新关注人数", "新增人数", "新增关注人数"],
    "unfollow_users": ["取消关注", "取消关注人数"],
    "net_followers": ["净增关注", "净增人数", "净增关注人数"],
    "cumulative_followers": ["累积关注", "累计关注", "累积人数", "累计关注人数", "累积关注人数"],
}

# 每类数据的识别特征：这些字段必须在表头里找到（取别名表中任意一个命中即可）。
# 顺序有意义：article_income 与 article_content_stats 都含标题，先判收入再判阅读。
KIND_SIGNATURES: list[tuple[str, list[str]]] = [
    ("ad_slot_daily", ["slot_name"]),
    ("article_income", ["title", "income"]),
    ("article_content_stats", ["title", "read_users"]),
    ("user_growth_daily", ["date", "new_followers"]),
    ("ad_income_daily", ["date", "ad_requests", "income"]),
]

# 每类数据最终落库时从行内提取的字段（整数 / 浮点 / 文本在建表时区分）。
INTEGER_FIELDS = {
    "ad_requests", "impressions", "clicks", "read_users", "read_times",
    "share_users", "collect_users", "like_users", "wow_users",
    "new_followers", "unfollow_users", "net_followers", "cumulative_followers",
}
FLOAT_FIELDS = {"impression_rate", "click_rate", "ecpm", "income"}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_int(value: object) -> int | None:
    text = str(value or "").strip().replace(",", "")
    if not text or text == "-":
        return None
    return int(float(text))


def parse_float(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text or text == "-":
        return None
    if text.endswith("%"):
        return float(text[:-1]) / 100
    return float(text)


def normalize_number(raw: str) -> str:
    """把 '3,593' / '12.22%' 规整为纯数字文本，便于统一导出 CSV。"""
    text = raw.strip().replace(",", "")
    if text.endswith("%"):
        try:
            return f"{float(text[:-1]) / 100:.4f}".rstrip("0").rstrip(".")
        except ValueError:
            return text
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open(encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别 CSV 编码：{path}")


def read_xlsx(path: Path) -> list[dict[str, object]]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = list(sheet.iter_rows(values_only=True))
    workbook.close()
    if not rows:
        return []
    headers = [str(value or "").strip() for value in rows[0]]
    return [dict(zip(headers, row)) for row in rows[1:] if any(value is not None for value in row)]


def read_rows(path: Path) -> list[dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        return read_xlsx(path)
    if suffix == ".xls":
        raise ValueError(
            f"{path.name} 是老版 .xls 格式；请在后台改选 CSV 导出，"
            "或先另存为 .xlsx 后再导入"
        )
    return read_csv(path)


def article_key(url: str, title: str = "") -> str:
    """单篇文章的稳定标识：优先取链接里的 mid:idx，取不到退化为标题哈希。

    为什么不用标题做主键：同一文章可能被老师改过标题重发，
    而 mid:idx 是微信后台对一篇图文的内部编号，不会随标题变化。
    """
    match = re.search(r"[?&]mid=([^&]+).*?[?&]idx=([^&]+)", url)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    match = re.search(r"[?&]sn=([^&]+)", url)
    if match:
        return match.group(1)
    basis = url or title
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def build_header_map(headers: list[str]) -> dict[str, str]:
    """把识别到的后台表头映射到内部字段名；返回 {内部字段: 实际表头}。"""
    cleaned = {h.strip(): h for h in headers if h}
    result: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in cleaned:
                result[field] = cleaned[alias]
                break
    return result


def detect_kind(headers: list[str]) -> str | None:
    fields = set(build_header_map(headers))
    for kind, required in KIND_SIGNATURES:
        if all(field in fields for field in required):
            return kind
    return None


def extract_field(row: dict[str, object], header_map: dict[str, str], field: str) -> object:
    header = header_map.get(field)
    if header is None:
        return None
    value = row.get(header)
    if value is None:
        return None
    if field in INTEGER_FIELDS:
        return parse_int(value)
    if field in FLOAT_FIELDS:
        return parse_float(value)
    return str(value).strip()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS monetization_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            source_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ad_income_daily (
            date TEXT PRIMARY KEY,
            ad_requests INTEGER,
            impressions INTEGER,
            impression_rate REAL,
            clicks INTEGER,
            click_rate REAL,
            ecpm REAL,
            income REAL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ad_slot_daily (
            date TEXT NOT NULL,
            slot_name TEXT NOT NULL,
            ad_requests INTEGER,
            impressions INTEGER,
            impression_rate REAL,
            clicks INTEGER,
            click_rate REAL,
            ecpm REAL,
            income REAL,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (date, slot_name)
        );

        CREATE TABLE IF NOT EXISTS article_income (
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            article_key TEXT NOT NULL,
            title TEXT,
            url TEXT,
            publish_date TEXT,
            income REAL,
            impressions INTEGER,
            ecpm REAL,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (window_start, window_end, article_key)
        );

        CREATE TABLE IF NOT EXISTS article_content_stats (
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            article_key TEXT NOT NULL,
            title TEXT,
            url TEXT,
            publish_date TEXT,
            read_users INTEGER,
            read_times INTEGER,
            share_users INTEGER,
            collect_users INTEGER,
            like_users INTEGER,
            wow_users INTEGER,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (window_start, window_end, article_key)
        );

        CREATE TABLE IF NOT EXISTS user_growth_daily (
            date TEXT PRIMARY KEY,
            new_followers INTEGER,
            unfollow_users INTEGER,
            net_followers INTEGER,
            cumulative_followers INTEGER,
            raw_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_article_income_key ON article_income(article_key);
        CREATE INDEX IF NOT EXISTS idx_article_content_key ON article_content_stats(article_key);
        CREATE INDEX IF NOT EXISTS idx_ad_slot_date ON ad_slot_daily(date);
        """
    )


def resolve_window(args: argparse.Namespace, rows: list[dict[str, object]],
                   header_map: dict[str, str], source: Path) -> tuple[str, str]:
    """确定文章类数据的统计窗口。

    优先级：命令行显式指定 > 行内日期列范围 > 文件名里的两个日期。
    文章收入/内容分析导出通常不带逐日列，窗口来自导出时选的范围，
    不记下来就无法和其他批次做同龄比较，所以识别不出时直接报错而不是瞎猜。
    """
    if args.window_start and args.window_end:
        return args.window_start, args.window_end
    date_header = header_map.get("date") or header_map.get("publish_date")
    if date_header:
        dates = sorted(str(row.get(date_header))[:10] for row in rows if row.get(date_header))
        if dates:
            return dates[0], dates[-1]
    found = re.findall(r"\d{4}[-.]\d{2}[-.]\d{2}", source.name)
    if len(found) >= 2:
        return found[0].replace(".", "-"), found[1].replace(".", "-")
    raise ValueError(
        f"无法识别 {source.name} 的统计范围，请用 --window-start YYYY-MM-DD "
        "--window-end YYYY-MM-DD 显式指定"
    )


def import_ad_income_daily(conn: sqlite3.Connection, rows: list[dict[str, object]],
                           header_map: dict[str, str]) -> int:
    count = 0
    for row in rows:
        date = extract_field(row, header_map, "date")
        if not date:
            continue
        record = {field: extract_field(row, header_map, field) for field in (
            "ad_requests", "impressions", "impression_rate", "clicks", "click_rate", "ecpm", "income")}
        conn.execute(
            "INSERT OR REPLACE INTO ad_income_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(date)[:10], record["ad_requests"], record["impressions"],
             record["impression_rate"], record["clicks"], record["click_rate"],
             record["ecpm"], record["income"], json.dumps(row, ensure_ascii=False, default=str)),
        )
        count += 1
    return count


def import_ad_slot_daily(conn: sqlite3.Connection, rows: list[dict[str, object]],
                         header_map: dict[str, str], fallback_slot: str | None = None) -> int:
    count = 0
    for row in rows:
        date = extract_field(row, header_map, "date")
        # 流量主后台按广告位标签导出的明细不带广告位列，只能靠导入时显式补齐，
        # 否则不同广告位的同名文件会互相覆盖，把账号数据搅浑。
        slot = extract_field(row, header_map, "slot_name") or fallback_slot
        if not date or not slot:
            continue
        record = {field: extract_field(row, header_map, field) for field in (
            "ad_requests", "impressions", "impression_rate", "clicks", "click_rate", "ecpm", "income")}
        conn.execute(
            "INSERT OR REPLACE INTO ad_slot_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(date)[:10], slot, record["ad_requests"], record["impressions"],
             record["impression_rate"], record["clicks"], record["click_rate"],
             record["ecpm"], record["income"], json.dumps(row, ensure_ascii=False, default=str)),
        )
        count += 1
    return count


def import_article_rows(conn: sqlite3.Connection, kind: str, rows: list[dict[str, object]],
                        header_map: dict[str, str], window: tuple[str, str]) -> int:
    count = 0
    for row in rows:
        title = extract_field(row, header_map, "title") or ""
        url = extract_field(row, header_map, "url") or ""
        if not title and not url:
            continue
        key = article_key(str(url), str(title))
        publish_date = extract_field(row, header_map, "publish_date")
        if kind == "article_income":
            conn.execute(
                "INSERT OR REPLACE INTO article_income VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (window[0], window[1], key, title, url,
                 str(publish_date)[:10] if publish_date else None,
                 extract_field(row, header_map, "income"),
                 extract_field(row, header_map, "impressions"),
                 extract_field(row, header_map, "ecpm"),
                 json.dumps(row, ensure_ascii=False, default=str)),
            )
        else:
            conn.execute(
                "INSERT OR REPLACE INTO article_content_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (window[0], window[1], key, title, url,
                 str(publish_date)[:10] if publish_date else None,
                 extract_field(row, header_map, "read_users"),
                 extract_field(row, header_map, "read_times"),
                 extract_field(row, header_map, "share_users"),
                 extract_field(row, header_map, "collect_users"),
                 extract_field(row, header_map, "like_users"),
                 extract_field(row, header_map, "wow_users"),
                 json.dumps(row, ensure_ascii=False, default=str)),
            )
        count += 1
    return count


def import_user_growth_daily(conn: sqlite3.Connection, rows: list[dict[str, object]],
                             header_map: dict[str, str]) -> int:
    count = 0
    for row in rows:
        date = extract_field(row, header_map, "date")
        if not date:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO user_growth_daily VALUES (?, ?, ?, ?, ?, ?)",
            (str(date)[:10],
             extract_field(row, header_map, "new_followers"),
             extract_field(row, header_map, "unfollow_users"),
             extract_field(row, header_map, "net_followers"),
             extract_field(row, header_map, "cumulative_followers"),
             json.dumps(row, ensure_ascii=False, default=str)),
        )
        count += 1
    return count


IMPORTERS = {
    "ad_income_daily": import_ad_income_daily,
    "user_growth_daily": import_user_growth_daily,
}

# 各表全量导出的排序方式，保证 exports/monetization/ 下的 CSV 稳定可对比。
EXPORT_QUERIES = {
    "ad_income_daily": "SELECT * FROM ad_income_daily ORDER BY date",
    "ad_slot_daily": "SELECT * FROM ad_slot_daily ORDER BY date, slot_name",
    "article_income": "SELECT * FROM article_income ORDER BY window_end DESC, income DESC",
    "article_content_stats": "SELECT * FROM article_content_stats ORDER BY window_end DESC, read_users DESC",
    "user_growth_daily": "SELECT * FROM user_growth_daily ORDER BY date",
}


def dump_exports(conn: sqlite3.Connection) -> None:
    """把全局表整体导出成 CSV，方便老师直接打开查看，也为后续报告提供稳定快照。"""
    EXPORT_MONETIZATION_DIR.mkdir(parents=True, exist_ok=True)
    for kind, query in EXPORT_QUERIES.items():
        cursor = conn.execute(query)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        if not rows:
            continue
        path = EXPORT_MONETIZATION_DIR / f"{kind}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)


def archive_source(path: Path, kind: str) -> Path:
    """把原始导出归档到 raw/monetization/<kind>/。

    如果文件已经在 data/data_analysis/raw/ 里（例如随批次归档过），
    就不再复制第二份，只在导入记录里指向已有位置，避免事实层出现两份拷贝。
    """
    try:
        path.relative_to(DATA_ROOT / "raw")
        return path
    except ValueError:
        pass
    destination_dir = RAW_MONETIZATION_DIR / kind
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / path.name
    if not destination.exists() or sha256_file(destination) != sha256_file(path):
        shutil.copy2(path, destination)
    return destination


def import_one_file(conn: sqlite3.Connection, path: Path, args: argparse.Namespace) -> tuple[str, int]:
    rows = read_rows(path)
    if not rows:
        raise ValueError(f"{path.name} 没有读到任何数据行")
    headers = [str(key) for key in rows[0].keys()]
    header_map = build_header_map(headers)
    kind = args.kind or detect_kind(headers)
    if not kind:
        raise ValueError(
            f"无法识别 {path.name} 的数据类型。识别到的表头：{'、'.join(headers)}。"
            "如确认属于某类数据，请用 --kind 指定：" + " / ".join(VALID_KINDS)
        )
    if kind not in VALID_KINDS:
        raise ValueError(f"--kind 只支持：{' / '.join(VALID_KINDS)}")

    if kind in ("article_income", "article_content_stats"):
        window = resolve_window(args, rows, header_map, path)
        count = import_article_rows(conn, kind, rows, header_map, window)
    elif kind == "ad_slot_daily":
        count = import_ad_slot_daily(conn, rows, header_map, args.slot_name)
    else:
        count = IMPORTERS[kind](conn, rows, header_map)

    archived = archive_source(path, kind)
    conn.execute(
        "INSERT INTO monetization_imports (kind, source_path, sha256, row_count, imported_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (kind, str(archived.relative_to(ROOT)), sha256_file(archived), count, now()),
    )
    return kind, count


def main() -> None:
    parser = argparse.ArgumentParser(description="导入公众号变现与增长数据（文章收入/广告位/全部文章/用户增长）")
    parser.add_argument("files", nargs="+", type=Path, help="后台导出的 CSV/XLSX，可一次传多份")
    parser.add_argument("--kind", choices=VALID_KINDS, default=None, help="强制指定数据类型（默认识别）")
    parser.add_argument("--slot-name", help="广告位名称；按广告位标签导出、文件内无广告位列时必须指定")
    parser.add_argument("--window-start", help="文章类数据统计开始日期 YYYY-MM-DD")
    parser.add_argument("--window-end", help="文章类数据统计结束日期 YYYY-MM-DD")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--dry-run", action="store_true", help="只识别和校验，不写入数据库")
    args = parser.parse_args()

    for path in args.files:
        if not path.exists():
            raise FileNotFoundError(path)

    conn = sqlite3.connect(str(args.db_path))
    conn.row_factory = sqlite3.Row
    create_schema(conn)

    results: list[tuple[str, str, int]] = []
    try:
        for path in args.files:
            kind, count = import_one_file(conn, path, args)
            results.append((path.name, kind, count))
        if args.dry_run:
            # 演练只验证识别与解析，必须回滚，不能让"试运行"污染事实库。
            conn.rollback()
        else:
            conn.commit()
            dump_exports(conn)
    except Exception:
        # 任一文件失败就整体回滚，避免半导半不导的中间态污染事实库。
        conn.rollback()
        conn.close()
        raise
    conn.close()

    if args.dry_run:
        print("演练模式：识别成功，未写入数据库。")
    for filename, kind, count in results:
        print(f"已导入 {filename} → {kind}，{count} 行")
    print(f"标准化明细：{EXPORT_MONETIZATION_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
