#!/usr/bin/env python3
"""导入微信公众号后台导出的运营数据。

这个脚本面向公众号运营复盘：保留后台导出的原始 .xls，同时生成
CSV 和 SQLite 数据，方便后续持续比较选题、标题与阅读来源。

不依赖 xlrd/LibreOffice，内置一个只读的简化 BIFF8 解析器，足够处理
微信公众号后台常见的 xlslib 导出表。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "core" / "wechat_official_account.sqlite"
SELF_MEDIA_ROOT = ROOT / "data" / "data_analysis"
DEFAULT_RAW_ROOT = SELF_MEDIA_ROOT / "raw"
DEFAULT_EXPORT_ROOT = SELF_MEDIA_ROOT / "exports"
DEFAULT_SUMMARY_ROOT = SELF_MEDIA_ROOT / "reports"
WECHAT_TIMEZONE = ZoneInfo("Asia/Shanghai")

END_OF_CHAIN = 0xFFFFFFFE
FREE_SECT = 0xFFFFFFFF


@dataclass
class SheetData:
    name: str
    rows: list[list[Any]]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\\s]+", "_", value.strip())
    return cleaned.strip("_") or "sheet"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def timestamp_to_date(value: str) -> str | None:
    try:
        stamp = int(value)
    except ValueError:
        return None
    if stamp < 946684800:
        return None
    return datetime.fromtimestamp(stamp, WECHAT_TIMEZONE).date().isoformat()


def batch_id_for(path: Path) -> str:
    stem = path.stem
    match = re.fullmatch(r"(.+?)_(\d{10})_(\d{10})", stem)
    if not match:
        return f"{datetime.now().date().isoformat()}_{safe_name(stem)}"
    prefix, start, end = match.groups()
    start_date = timestamp_to_date(start) or start
    end_date = timestamp_to_date(end) or end
    return f"{start_date}_to_{end_date}_{safe_name(prefix)}"


class CompoundFile:
    """Minimal OLE Compound File reader for the Workbook stream."""

    def __init__(self, path: Path):
        self.data = path.read_bytes()
        if self.data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise ValueError("不是 OLE2 复合文档，无法按 .xls 解析")
        self.sector_size = 1 << struct.unpack_from("<H", self.data, 30)[0]
        self.mini_sector_size = 1 << struct.unpack_from("<H", self.data, 32)[0]
        self.mini_cutoff = struct.unpack_from("<I", self.data, 56)[0]
        self.first_dir_sector = struct.unpack_from("<I", self.data, 48)[0]
        self.first_mini_fat_sector = struct.unpack_from("<I", self.data, 60)[0]
        self.num_mini_fat_sectors = struct.unpack_from("<I", self.data, 64)[0]
        self.first_difat_sector = struct.unpack_from("<I", self.data, 68)[0]
        self.num_difat_sectors = struct.unpack_from("<I", self.data, 72)[0]
        self.fat = self._read_fat()
        self.directory = self._read_directory()
        self.root_entry = next((entry for entry in self.directory if entry["type"] == 5), None)
        self.mini_fat = self._read_mini_fat()
        self.mini_stream = self._read_regular_stream(self.root_entry) if self.root_entry else b""

    def _sector(self, sector_id: int) -> bytes:
        offset = (sector_id + 1) * self.sector_size
        return self.data[offset : offset + self.sector_size]

    def _sector_chain(self, start: int, fat: list[int] | None = None) -> list[int]:
        if start in (END_OF_CHAIN, FREE_SECT):
            return []
        table = self.fat if fat is None else fat
        seen: set[int] = set()
        chain: list[int] = []
        current = start
        while current not in (END_OF_CHAIN, FREE_SECT) and current < len(table):
            if current in seen:
                raise ValueError("OLE2 扇区链出现循环")
            seen.add(current)
            chain.append(current)
            current = table[current]
        return chain

    def _read_fat(self) -> list[int]:
        difat = list(struct.unpack_from("<109I", self.data, 76))
        current = self.first_difat_sector
        for _ in range(self.num_difat_sectors):
            if current in (END_OF_CHAIN, FREE_SECT):
                break
            sector = self._sector(current)
            entries = struct.unpack_from(f"<{self.sector_size // 4}I", sector)
            difat.extend(entries[:-1])
            current = entries[-1]
        fat: list[int] = []
        for sector_id in difat:
            if sector_id in (END_OF_CHAIN, FREE_SECT) or sector_id >= 0xFFFFFFF0:
                continue
            sector = self._sector(sector_id)
            fat.extend(struct.unpack_from(f"<{self.sector_size // 4}I", sector))
        return fat

    def _read_regular_stream(self, entry: dict[str, Any]) -> bytes:
        chunks = [self._sector(sector_id) for sector_id in self._sector_chain(entry["start"])]
        return b"".join(chunks)[: entry["size"]]

    def _read_directory(self) -> list[dict[str, Any]]:
        chunks = [self._sector(sector_id) for sector_id in self._sector_chain(self.first_dir_sector)]
        directory_stream = b"".join(chunks)
        entries: list[dict[str, Any]] = []
        for offset in range(0, len(directory_stream), 128):
            raw = directory_stream[offset : offset + 128]
            if len(raw) < 128:
                continue
            name_len = struct.unpack_from("<H", raw, 64)[0]
            name = raw[: max(0, name_len - 2)].decode("utf-16le", errors="ignore")
            entry_type = raw[66]
            start = struct.unpack_from("<I", raw, 116)[0]
            size = struct.unpack_from("<Q", raw, 120)[0]
            if name:
                entries.append({"name": name, "type": entry_type, "start": start, "size": size})
        return entries

    def _read_mini_fat(self) -> list[int]:
        if self.first_mini_fat_sector in (END_OF_CHAIN, FREE_SECT) or not self.num_mini_fat_sectors:
            return []
        sectors = self._sector_chain(self.first_mini_fat_sector)[: self.num_mini_fat_sectors]
        chunks = [self._sector(sector_id) for sector_id in sectors]
        raw = b"".join(chunks)
        return list(struct.unpack_from(f"<{len(raw) // 4}I", raw))

    def _read_mini_stream(self, entry: dict[str, Any]) -> bytes:
        chunks: list[bytes] = []
        for sector_id in self._sector_chain(entry["start"], self.mini_fat):
            offset = sector_id * self.mini_sector_size
            chunks.append(self.mini_stream[offset : offset + self.mini_sector_size])
        return b"".join(chunks)[: entry["size"]]

    def open_stream(self, *names: str) -> bytes:
        lowered = {name.lower() for name in names}
        entry = next((item for item in self.directory if item["name"].lower() in lowered), None)
        if not entry:
            available = ", ".join(item["name"] for item in self.directory)
            raise ValueError(f"没有找到工作簿流，可用流：{available}")
        if entry["size"] < self.mini_cutoff:
            return self._read_mini_stream(entry)
        return self._read_regular_stream(entry)


def iter_biff_records(workbook: bytes) -> Iterable[tuple[int, int, bytes]]:
    pos = 0
    while pos + 4 <= len(workbook):
        record_type, size = struct.unpack_from("<HH", workbook, pos)
        payload = workbook[pos + 4 : pos + 4 + size]
        yield pos, record_type, payload
        pos += 4 + size


def decode_boundsheet_name(payload: bytes) -> tuple[int, str]:
    offset = struct.unpack_from("<I", payload, 0)[0]
    name_len = payload[6]
    flags = payload[7]
    raw = payload[8 : 8 + name_len * (2 if flags & 1 else 1)]
    encoding = "utf-16le" if flags & 1 else "latin1"
    return offset, raw.decode(encoding, errors="replace")


class BIFFStringReader:
    def __init__(self, record_payloads: list[bytes], start_offset: int = 0):
        self.parts = record_payloads
        self.part_index = 0
        self.offset = start_offset

    def _ensure_part(self) -> bool:
        while self.part_index < len(self.parts) and self.offset >= len(self.parts[self.part_index]):
            self.part_index += 1
            self.offset = 0
        return self.part_index < len(self.parts)

    def read(self, size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = size
        while remaining > 0 and self._ensure_part():
            current = self.parts[self.part_index]
            take = min(remaining, len(current) - self.offset)
            chunks.append(current[self.offset : self.offset + take])
            self.offset += take
            remaining -= take
        if remaining:
            raise ValueError("SST 字符串记录不完整")
        return b"".join(chunks)

    def read_u8(self) -> int:
        return self.read(1)[0]

    def read_u16(self) -> int:
        return struct.unpack("<H", self.read(2))[0]

    def read_u32(self) -> int:
        return struct.unpack("<I", self.read(4))[0]

    def read_chars(self, count: int, is_wide: bool) -> str:
        chars: list[str] = []
        remaining = count
        wide = is_wide
        while remaining > 0:
            if not self._ensure_part():
                raise ValueError("SST 字符串内容不完整")
            current = self.parts[self.part_index]
            bytes_per_char = 2 if wide else 1
            available_chars = (len(current) - self.offset) // bytes_per_char
            if available_chars == 0:
                self.part_index += 1
                self.offset = 0
                if self._ensure_part():
                    wide = bool(self.read_u8() & 1)
                continue
            take_chars = min(remaining, available_chars)
            raw = self.read(take_chars * bytes_per_char)
            chars.append(raw.decode("utf-16le" if wide else "latin1", errors="replace"))
            remaining -= take_chars
            if remaining > 0 and self.offset >= len(current):
                self.part_index += 1
                self.offset = 0
                if self._ensure_part():
                    wide = bool(self.read_u8() & 1)
        return "".join(chars)


def read_biff_string(reader: BIFFStringReader) -> str:
    char_count = reader.read_u16()
    flags = reader.read_u8()
    is_wide = bool(flags & 0x01)
    has_ext = bool(flags & 0x04)
    has_rich = bool(flags & 0x08)
    rich_runs = reader.read_u16() if has_rich else 0
    ext_size = reader.read_u32() if has_ext else 0
    text = reader.read_chars(char_count, is_wide)
    if rich_runs:
        reader.read(rich_runs * 4)
    if ext_size:
        reader.read(ext_size)
    return text


def parse_sst(record_payloads: list[bytes]) -> list[str]:
    if not record_payloads:
        return []
    unique_count = struct.unpack_from("<I", record_payloads[0], 4)[0]
    reader = BIFFStringReader(record_payloads, 8)
    strings: list[str] = []
    for _ in range(unique_count):
        strings.append(read_biff_string(reader))
    return strings


def decode_rk(raw: int) -> float:
    if raw & 0x02:
        value = raw >> 2
        if value & 0x20000000:
            value -= 0x40000000
        result = float(value)
    else:
        encoded = (raw & 0xFFFFFFFC) << 32
        result = struct.unpack("<d", struct.pack("<Q", encoded))[0]
    if raw & 0x01:
        result /= 100
    return result


def clean_number(value: float) -> int | float:
    if value.is_integer():
        return int(value)
    return value


def read_inline_label(payload: bytes) -> str:
    reader = BIFFStringReader([payload], 6)
    return read_biff_string(reader)


def parse_formula_result(raw: bytes) -> Any:
    marker = raw[6:8]
    if marker in (b"\xff\xff", b"\x00\x00"):
        return None
    return clean_number(struct.unpack_from("<d", raw, 6)[0])


def set_cell(cells: dict[tuple[int, int], Any], row: int, col: int, value: Any) -> None:
    cells[(row, col)] = value


def parse_sheet(workbook: bytes, start: int, end: int, shared_strings: list[str]) -> list[list[Any]]:
    cells: dict[tuple[int, int], Any] = {}
    max_row = -1
    max_col = -1
    for _, record_type, payload in iter_biff_records(workbook[start:end]):
        if record_type == 0x000A:
            break
        if record_type == 0x00FD and len(payload) >= 10:  # LABELSST
            row, col = struct.unpack_from("<HH", payload, 0)
            string_index = struct.unpack_from("<I", payload, 6)[0]
            value = shared_strings[string_index] if string_index < len(shared_strings) else ""
            set_cell(cells, row, col, value)
        elif record_type == 0x0204 and len(payload) >= 8:  # LABEL
            row, col = struct.unpack_from("<HH", payload, 0)
            set_cell(cells, row, col, read_inline_label(payload))
        elif record_type == 0x0203 and len(payload) >= 14:  # NUMBER
            row, col = struct.unpack_from("<HH", payload, 0)
            set_cell(cells, row, col, clean_number(struct.unpack_from("<d", payload, 6)[0]))
        elif record_type == 0x027E and len(payload) >= 10:  # RK
            row, col = struct.unpack_from("<HH", payload, 0)
            set_cell(cells, row, col, clean_number(decode_rk(struct.unpack_from("<I", payload, 6)[0])))
        elif record_type == 0x00BD and len(payload) >= 8:  # MULRK
            row = struct.unpack_from("<H", payload, 0)[0]
            first_col = struct.unpack_from("<H", payload, 2)[0]
            last_col = struct.unpack_from("<H", payload, len(payload) - 2)[0]
            offset = 4
            for col in range(first_col, last_col + 1):
                if offset + 6 > len(payload) - 2:
                    break
                raw_rk = struct.unpack_from("<I", payload, offset + 2)[0]
                set_cell(cells, row, col, clean_number(decode_rk(raw_rk)))
                offset += 6
        elif record_type in (0x0006, 0x0406) and len(payload) >= 14:  # FORMULA
            row, col = struct.unpack_from("<HH", payload, 0)
            set_cell(cells, row, col, parse_formula_result(payload))
        elif record_type == 0x0205 and len(payload) >= 8:  # BOOLERR
            row, col = struct.unpack_from("<HH", payload, 0)
            set_cell(cells, row, col, bool(payload[6]) if payload[7] == 0 else None)
        elif record_type == 0x0002 and len(payload) >= 7:  # INTEGER
            row, col = struct.unpack_from("<HH", payload, 0)
            set_cell(cells, row, col, struct.unpack_from("<H", payload, 5)[0])
        if record_type in (0x00FD, 0x0204, 0x0203, 0x027E, 0x00BD, 0x0006, 0x0406, 0x0205, 0x0002):
            if cells:
                max_row = max(max_row, max(key[0] for key in cells))
                max_col = max(max_col, max(key[1] for key in cells))
    rows: list[list[Any]] = []
    for row_index in range(max_row + 1):
        row = [cells.get((row_index, col_index), "") for col_index in range(max_col + 1)]
        while row and row[-1] == "":
            row.pop()
        rows.append(row)
    while rows and not any(value != "" for value in rows[-1]):
        rows.pop()
    return rows


def read_xls(path: Path) -> list[SheetData]:
    workbook = CompoundFile(path).open_stream("Workbook", "Book")
    records = list(iter_biff_records(workbook))
    sheet_bounds: list[tuple[int, str]] = []
    shared_strings: list[str] = []
    index = 0
    while index < len(records):
        _, record_type, payload = records[index]
        if record_type == 0x0085:
            sheet_bounds.append(decode_boundsheet_name(payload))
        elif record_type == 0x00FC:
            payloads = [payload]
            next_index = index + 1
            while next_index < len(records) and records[next_index][1] == 0x003C:
                payloads.append(records[next_index][2])
                next_index += 1
            shared_strings = parse_sst(payloads)
            index = next_index - 1
        index += 1
    sheet_bounds.sort(key=lambda item: item[0])
    sheets: list[SheetData] = []
    for sheet_index, (start, name) in enumerate(sheet_bounds):
        end = sheet_bounds[sheet_index + 1][0] if sheet_index + 1 < len(sheet_bounds) else len(workbook)
        sheets.append(SheetData(name=name, rows=parse_sheet(workbook, start, end, shared_strings)))
    return sheets


def rows_to_csv(rows: list[list[Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)


def first_nonempty_row(rows: list[list[Any]]) -> list[Any]:
    for row in rows:
        if any(value != "" for value in row):
            return row
    return []


def find_title(rows: list[list[Any]]) -> str:
    row = first_nonempty_row(rows)
    for value in row:
        if value != "":
            return str(value)
    return ""


def header_and_records(rows: list[list[Any]], header_markers: set[str]) -> tuple[list[str], list[dict[str, Any]]]:
    header_index = None
    for index, row in enumerate(rows):
        values = {str(value).strip() for value in row if value != ""}
        if header_markers & values:
            header_index = index
            break
    if header_index is None:
        return [], []
    headers = [str(value).strip() for value in rows[header_index]]
    records: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        if not any(value != "" for value in row):
            continue
        item: dict[str, Any] = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            item[header] = row[idx] if idx < len(row) else ""
        records.append(item)
    return headers, records


def header_segments(row: list[Any]) -> list[tuple[int, int, list[str]]]:
    segments: list[tuple[int, int, list[str]]] = []
    index = 0
    while index < len(row):
        while index < len(row) and row[index] == "":
            index += 1
        if index >= len(row):
            break
        start = index
        while index < len(row) and row[index] != "":
            index += 1
        end = index
        headers = [str(value).strip() for value in row[start:end]]
        segments.append((start, end, headers))
    return segments


def segmented_records(rows: list[list[Any]]) -> list[dict[str, Any]]:
    """Extract horizontally separated tables from one exported WeChat sheet."""
    blocks: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        for start, end, headers in header_segments(row):
            header_set = {header for header in headers if header}
            block_type = ""
            if {"日期", "渠道", "阅读人数"} <= header_set:
                block_type = "channel_daily_reads"
            elif {"日期", "分享人数", "发表篇数"} <= header_set:
                block_type = "daily_trends"
            elif {"传播渠道", "发表日期", "内容标题", "阅读人数"} <= header_set:
                block_type = "source_overview"
            if not block_type:
                continue
            title = ""
            if row_index > 0:
                previous = rows[row_index - 1]
                if start < len(previous):
                    title = str(previous[start]).strip()
            records: list[dict[str, Any]] = []
            for source_row in rows[row_index + 1 :]:
                values = source_row[start:end]
                if not any(value != "" for value in values):
                    continue
                record: dict[str, Any] = {}
                for idx, header in enumerate(headers):
                    if not header:
                        continue
                    record[header] = values[idx] if idx < len(values) else ""
                records.append(record)
            blocks.append(
                {
                    "type": block_type,
                    "title": title,
                    "headers": headers,
                    "records": records,
                }
            )
    return blocks


def records_to_rows(headers: list[str], records: list[dict[str, Any]]) -> list[list[Any]]:
    return [headers, *[[record.get(header, "") for header in headers] for record in records]]


def to_int(value: Any) -> int | None:
    if value == "" or value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS import_batches (
            batch_id TEXT PRIMARY KEY,
            source_filename TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            export_dir TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            sheet_summary_json TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_trends (
            batch_id TEXT NOT NULL,
            row_no INTEGER NOT NULL,
            date TEXT,
            published_count INTEGER,
            read_users INTEGER,
            share_users INTEGER,
            original_read_users INTEGER,
            wechat_favorites INTEGER,
            raw_json TEXT NOT NULL,
            PRIMARY KEY(batch_id, row_no),
            FOREIGN KEY(batch_id) REFERENCES import_batches(batch_id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS channel_daily_reads (
            batch_id TEXT NOT NULL,
            row_no INTEGER NOT NULL,
            date TEXT,
            channel TEXT,
            read_users INTEGER,
            raw_json TEXT NOT NULL,
            PRIMARY KEY(batch_id, row_no),
            FOREIGN KEY(batch_id) REFERENCES import_batches(batch_id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS source_overview (
            batch_id TEXT NOT NULL,
            row_no INTEGER NOT NULL,
            channel TEXT,
            publish_date TEXT,
            title TEXT,
            read_users INTEGER,
            read_share REAL,
            raw_json TEXT NOT NULL,
            PRIMARY KEY(batch_id, row_no),
            FOREIGN KEY(batch_id) REFERENCES import_batches(batch_id) ON DELETE CASCADE
        )
        """
    )
    existing_daily_columns = {row[1] for row in cur.execute("PRAGMA table_info(daily_trends)")}
    if "share_users" not in existing_daily_columns:
        cur.execute("ALTER TABLE daily_trends ADD COLUMN share_users INTEGER")
    if "wechat_favorites" not in existing_daily_columns:
        cur.execute("ALTER TABLE daily_trends ADD COLUMN wechat_favorites INTEGER")
    existing_source_columns = {row[1] for row in cur.execute("PRAGMA table_info(source_overview)")}
    if "publish_date" not in existing_source_columns and "date" in existing_source_columns:
        # Fresh projects use publish_date. Older experimental databases can keep date in raw_json.
        pass
    if "read_share" not in existing_source_columns:
        cur.execute("ALTER TABLE source_overview ADD COLUMN read_share REAL")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_trends_date ON daily_trends(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_channel_daily_reads_date ON channel_daily_reads(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_channel_daily_reads_channel ON channel_daily_reads(channel)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_source_overview_title ON source_overview(title)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_source_overview_channel ON source_overview(channel)")
    conn.commit()


def normalize_date(value: Any) -> str:
    if value == "" or value is None:
        return ""
    text = str(value).strip()
    match = re.fullmatch(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", text)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    match = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", text)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})", text)
    if match:
        month, day = match.groups()
        return f"{int(month):02d}-{int(day):02d}"
    return text


def to_float(value: Any) -> float | None:
    if value == "" or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def import_to_db(
    db_path: Path,
    batch_id: str,
    source: Path,
    source_hash: str,
    raw_path: Path,
    export_dir: Path,
    sheets: list[SheetData],
) -> dict[str, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    create_schema(conn)
    summary = {
        sheet.name: {
            "rows": len(sheet.rows),
            "title": find_title(sheet.rows),
        }
        for sheet in sheets
    }
    with conn:
        conn.execute("DELETE FROM daily_trends WHERE batch_id = ?", (batch_id,))
        conn.execute("DELETE FROM channel_daily_reads WHERE batch_id = ?", (batch_id,))
        conn.execute("DELETE FROM source_overview WHERE batch_id = ?", (batch_id,))
        conn.execute(
            """
            INSERT INTO import_batches(
                batch_id, source_filename, source_sha256, raw_path, export_dir, imported_at, sheet_summary_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(batch_id) DO UPDATE SET
                source_filename=excluded.source_filename,
                source_sha256=excluded.source_sha256,
                raw_path=excluded.raw_path,
                export_dir=excluded.export_dir,
                imported_at=excluded.imported_at,
                sheet_summary_json=excluded.sheet_summary_json
            """,
            (
                batch_id,
                source.name,
                source_hash,
                display_path(raw_path),
                display_path(export_dir),
                now(),
                json.dumps(summary, ensure_ascii=False),
            ),
        )
        daily_count = 0
        channel_count = 0
        source_count = 0
        blocks = [block for sheet in sheets for block in segmented_records(sheet.rows)]
        total_read_by_date: dict[str, int] = {}
        for block in blocks:
            if block["type"] == "channel_daily_reads":
                for row_no, record in enumerate(block["records"], start=1):
                    date = normalize_date(record.get("日期", ""))
                    channel = str(record.get("渠道", "")).strip()
                    read_users = to_int(record.get("阅读人数"))
                    conn.execute(
                        """
                        INSERT INTO channel_daily_reads(batch_id, row_no, date, channel, read_users, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            batch_id,
                            row_no,
                            date,
                            channel,
                            read_users,
                            json.dumps(record, ensure_ascii=False),
                        ),
                    )
                    if channel == "全部" and read_users is not None:
                        total_read_by_date[date] = read_users
                    channel_count += 1
        for block in blocks:
            if block["type"] == "daily_trends":
                for row_no, record in enumerate(block["records"], start=1):
                    date = normalize_date(record.get("日期", ""))
                    conn.execute(
                        """
                        INSERT INTO daily_trends(
                            batch_id, row_no, date, published_count, read_users, share_users,
                            original_read_users, wechat_favorites, raw_json
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            batch_id,
                            row_no,
                            date,
                            to_int(record.get("发表篇数")),
                            total_read_by_date.get(date),
                            to_int(record.get("分享人数")),
                            to_int(record.get("跳转阅读原文人数")),
                            to_int(record.get("微信收藏人数")),
                            json.dumps(record, ensure_ascii=False),
                        ),
                    )
                    daily_count += 1
            elif block["type"] == "source_overview":
                for row_no, record in enumerate(block["records"], start=1):
                    conn.execute(
                        """
                        INSERT INTO source_overview(
                            batch_id, row_no, channel, publish_date, title, read_users, read_share, raw_json
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            batch_id,
                            row_no,
                            str(record.get("传播渠道", "")).strip(),
                            normalize_date(record.get("发表日期", "")),
                            str(record.get("内容标题", "")).strip(),
                            to_int(record.get("阅读人数")),
                            to_float(record.get("阅读人数占比")),
                            json.dumps(record, ensure_ascii=False),
                        ),
                    )
                    source_count += 1
    conn.close()
    return {
        "daily_trends": daily_count,
        "channel_daily_reads": channel_count,
        "source_overview": source_count,
    }


def write_summary(
    path: Path,
    batch_id: str,
    source: Path,
    raw_path: Path,
    export_dir: Path,
    db_path: Path,
    sheets: list[SheetData],
    imported_counts: dict[str, int],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 微信公众号运营数据导入记录：{batch_id}",
        "",
        "## 存放位置",
        "",
        f"- 原始后台表：`{display_path(raw_path)}`",
        f"- CSV 导出目录：`{display_path(export_dir)}`",
        f"- 核心分析库：`{display_path(db_path)}`",
        "",
        "## 本次识别结果",
        "",
    ]
    for sheet in sheets:
        lines.append(f"- `{sheet.name}`：{len(sheet.rows)} 行；标题：{find_title(sheet.rows) or '未识别'}")
    blocks = [block for sheet in sheets for block in segmented_records(sheet.rows)]
    if blocks:
        lines.extend(["", "## 已拆分数据表", ""])
        block_names = {
            "daily_trends": "每日趋势",
            "channel_daily_reads": "每日渠道阅读",
            "source_overview": "单篇来源表现",
        }
        for block in blocks:
            label = block_names.get(str(block["type"]), str(block["type"]))
            lines.append(f"- {label}：{len(block['records'])} 条；标题：{block.get('title') or '未识别'}")
    lines.extend(
        [
            "",
            "## 已写入核心库",
            "",
            f"- 每日趋势记录：{imported_counts.get('daily_trends', 0)} 条",
            f"- 每日渠道阅读记录：{imported_counts.get('channel_daily_reads', 0)} 条",
            f"- 阅读来源记录：{imported_counts.get('source_overview', 0)} 条",
            "",
            "## 后续分析用途",
            "",
            "- 用 `daily_trends` 观察整体阅读人数、发文频率与阶段趋势。",
            "- 用 `channel_daily_reads` 观察公众号消息、朋友圈、推荐、搜一搜等渠道对阅读量的贡献。",
            "- 用 `source_overview` 比较不同文章标题、渠道来源和阅读人数。",
            "- 后续可把文章标题与 `content_ideas` 选题池关联，逐步判断哪些申论/面试选题更受读者欢迎。",
            "",
            "## 下次导入",
            "",
            "```bash",
            f"python3 scripts/import_wechat_official_account_stats.py /path/to/next-export.xls",
            "```",
            "",
            f"来源文件名：`{source.name}`",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="导入微信公众号后台运营数据")
    parser.add_argument("source", help="微信公众号后台导出的 .xls 文件")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite 核心分析库路径")
    parser.add_argument("--raw-root", default=str(DEFAULT_RAW_ROOT), help="原始后台表留存目录")
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT), help="CSV 导出根目录")
    parser.add_argument("--summary-root", default=str(DEFAULT_SUMMARY_ROOT), help="导入说明根目录")
    parser.add_argument("--inspect", action="store_true", help="只读取并打印工作表概况，不写入项目")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"找不到源文件：{source}")
    sheets = read_xls(source)
    if args.inspect:
        for sheet in sheets:
            print(f"\n## {sheet.name}")
            for row in sheet.rows[:12]:
                print(row)
        return

    batch_id = batch_id_for(source)
    raw_dir = Path(args.raw_root) / batch_id
    export_dir = Path(args.export_root) / batch_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / source.name
    shutil.copy2(source, raw_path)
    for sheet in sheets:
        rows_to_csv(sheet.rows, export_dir / f"{safe_name(sheet.name)}.csv")
    block_file_counts: dict[str, int] = {}
    for sheet in sheets:
        for block in segmented_records(sheet.rows):
            block_type = str(block["type"])
            block_file_counts[block_type] = block_file_counts.get(block_type, 0) + 1
            suffix = "" if block_file_counts[block_type] == 1 else f"_{block_file_counts[block_type]}"
            rows_to_csv(
                records_to_rows(block["headers"], block["records"]),
                export_dir / f"{block_type}{suffix}.csv",
            )

    db_path = Path(args.db_path)
    imported_counts = import_to_db(
        db_path=db_path,
        batch_id=batch_id,
        source=source,
        source_hash=sha256_file(source),
        raw_path=raw_path,
        export_dir=export_dir,
        sheets=sheets,
    )
    summary_path = Path(args.summary_root) / f"{batch_id}.md"
    write_summary(summary_path, batch_id, source, raw_path, export_dir, db_path, sheets, imported_counts)
    overview_script = ROOT / "scripts" / "analyze_wechat_official_account_stats.py"
    overview_path = Path(args.summary_root).parent / "overview.md"
    subprocess.run(
        [
            sys.executable,
            str(overview_script),
            "--db-path",
            str(db_path),
            "--output",
            str(overview_path),
            "--report-dir",
            str(Path(args.summary_root)),
        ],
        cwd=ROOT,
        check=True,
    )

    print(f"已导入批次：{batch_id}")
    print(f"原始表：{display_path(raw_path)}")
    print(f"CSV：{display_path(export_dir)}")
    print(f"SQLite：{display_path(db_path)}")
    print(f"说明：{display_path(summary_path)}")
    print(f"连续分析总览：{display_path(overview_path)}")
    print(f"每日趋势记录：{imported_counts.get('daily_trends', 0)}")
    print(f"每日渠道阅读记录：{imported_counts.get('channel_daily_reads', 0)}")
    print(f"阅读来源记录：{imported_counts.get('source_overview', 0)}")


if __name__ == "__main__":
    main()
