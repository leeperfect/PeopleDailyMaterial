#!/usr/bin/env python3
"""公众号后台数据采集器（半自动版）。

为什么做成"你点导出、我来接管"的半自动，而不是全自动点页面：
- 公众号后台页面结构经常调整，写死的自动点击最脆弱；
- 后台每一页都有"导出/下载"按钮，导出文件格式反而稳定；
- 所以本脚本只做三件确定能做好的事：
  1) 用你本机 Chrome 打开后台并保住登录态（登录态存在本地，不进 Git）；
  2) 监听浏览器下载，任何导出文件一落盘就被接住；
  3) 按文件内容自动识别数据类型，立即归档 raw/ 并写入 SQLite。

用法：
    python3 scripts/collect_wechat_mp_stats.py

首次运行会停在扫码页，扫码登录后按终端清单逐页点"导出"即可。
以后登录态不过期就不用再扫码。结束时在终端按 Ctrl+C 关闭。
"""

from __future__ import annotations

import argparse
import shutil
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "data_analysis"
PROFILE_DIR = DATA_ROOT / ".collector_profile"
INBOX_DIR = DATA_ROOT / "raw" / "inbox"
RAW_MONETIZATION_DIR = DATA_ROOT / "raw" / "monetization"

# 让采集器直接复用入库脚本的识别与读取逻辑，两套规则只有一份事实源。
sys.path.insert(0, str(ROOT / "scripts"))
from import_wechat_monetization_stats import (  # noqa: E402
    build_header_map,
    detect_kind,
    read_rows,
)

HOME_URL = "https://mp.weixin.qq.com/"

# 打印给老师的逐页操作清单。只描述"在哪里点导出"，不依赖页面内部结构。
EXPORT_CHECKLIST = [
    ("文章收入", "左侧「收入变现 → 流量主」→ 上方「数据报表」→ 切到「文章收入」→ 选好时间范围后点「导出」"),
    ("广告位数据", "同一页切到「广告位数据」→ 点「导出」"),
    ("流量主每日汇总", "同一页切到「每日数据」（或「汇总数据」）→ 点「导出」"),
    ("全部文章内容分析", "左侧「数据 → 内容分析」→ 选「全部」内容 → 时间范围尽量拉长 → 点「导出/下载数据明细」"),
    ("用户增长", "左侧「数据 → 用户分析」→ 「用户增长」→ 时间范围选最近 90 天 → 点「下载表格」"),
    ("（可选）原有六份表", "「数据 → 内容分析」的「数据趋势/数据来源」、搜一搜的「热门搜索词/热门文章/热门服务菜单」、粉丝来源、关键数据"),
]

# 文件名识别兜底：内容识别失败时按文件名关键词归类。
# 原有的六类批次文件不自动入库（它们要走批次流程），只提示人工命令。
FILENAME_HINTS = [
    ("收入明细", "ad_income_daily"),
    ("广告位", "ad_slot_daily"),
    ("文章收入", "article_income"),
    ("用户增长", "user_growth_daily"),
    ("用户分析", "user_growth_daily"),
    ("内容分析", "article_content_stats"),
    ("全部", "article_content_stats"),
]

LEGACY_HINTS = ["关键数据", "粉丝来源", "热门搜索词", "热门文章数据", "热门服务菜单", "tendency"]

STOP_REQUESTED = False


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(message: str) -> None:
    print(f"[{ts()}] {message}", flush=True)


def request_stop(signum: int, _frame: object) -> None:
    # Ctrl+C 或外部终止都只置标志位，让主循环干净地关闭浏览器，
    # 避免 Chrome 配置文件被写坏导致下次登录态丢失。
    global STOP_REQUESTED
    STOP_REQUESTED = True
    log("收到结束信号，正在关闭浏览器……")


def classify_file(path: Path) -> str | None:
    """先按文件内容（表头）识别类型，识别不了再按文件名关键词兜底。"""
    try:
        rows = read_rows(path)
    except Exception:
        rows = []
    if rows:
        kind = detect_kind([str(key) for key in rows[0].keys()])
        if kind:
            return kind
    name = path.name
    for keyword, kind in FILENAME_HINTS:
        if keyword in name:
            return kind
    return None


def import_downloaded(path: Path, kind: str) -> bool:
    """文件归档后立即调用入库脚本，做到"边导出边入库"，不等会话结束。"""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "import_wechat_monetization_stats.py"), str(path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode == 0:
        for line in result.stdout.strip().splitlines():
            log(f"  入库：{line}")
        return True
    log(f"  入库失败：{result.stderr.strip().splitlines()[-1] if result.stderr else '未知错误'}")
    log(f"  文件已保留在 {path}，可稍后手工执行入库命令")
    return False


def handle_download(download: object) -> None:
    """Playwright 下载事件回调：接文件 → 识别 → 归档 → 入库。"""
    suggested = download.suggested_filename or f"download-{int(time.time())}.csv"
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    staging = INBOX_DIR / suggested
    try:
        download.save_as(str(staging))
    except Exception as error:  # 下载本身失败不能拖垮整个监听
        log(f"接文件失败：{suggested}（{error}）")
        return
    log(f"已接到导出文件：{suggested}")

    if any(hint in suggested for hint in LEGACY_HINTS):
        log("  这是原有批次类数据，不自动入库；请按既有流程导入（见 data/data_analysis/README.md）")
        return

    kind = classify_file(staging)
    if not kind:
        log("  暂时识别不出数据类型，文件保留在 raw/inbox/，请把它发给我确认")
        return

    destination_dir = RAW_MONETIZATION_DIR / kind
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / suggested
    if destination.exists():
        # 同名重复导出通常是误点两次，保留带时间戳的副本而不是覆盖。
        destination = destination_dir / f"{destination.stem}_{datetime.now():%H%M%S}{destination.suffix}"
    shutil.move(str(staging), str(destination))
    log(f"  识别为 {kind}，已归档到 {destination.relative_to(ROOT)}")
    import_downloaded(destination, kind)


def ensure_login(page: object, timeout_seconds: int = 600) -> None:
    """等待后台出现 token，表示扫码登录完成。"""
    if "token=" in page.url:
        log("检测到已有登录态，无需扫码")
        return
    log("请在打开的 Chrome 里扫码登录公众号后台（10 分钟内有效）……")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if "token=" in page.url:
            log("登录成功，登录态已保存在本机")
            return
        time.sleep(2)
    raise TimeoutError("等待扫码超时；请重新运行本脚本再试")


def print_checklist() -> None:
    print()
    print("=" * 72)
    print("请按下面顺序在后台逐页点「导出」，文件一落盘我会自动接管：")
    print("=" * 72)
    for index, (name, howto) in enumerate(EXPORT_CHECKLIST, start=1):
        print(f"  {index}. 【{name}】{howto}")
    print("=" * 72)
    print("全部点完后，回到这个终端按 Ctrl+C 结束。")
    print(flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号后台数据采集器（你点导出，我接管归档和入库）")
    parser.add_argument("--profile-dir", type=Path, default=PROFILE_DIR, help="Chrome 登录态目录")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    args.profile_dir.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        # 用本机真实 Chrome + 固定配置目录：登录一次，之后免扫码；
        # 配置目录在 .gitignore 里，登录态不会进 GitHub。
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(args.profile_dir),
            channel="chrome",
            headless=False,
            accept_downloads=True,
            viewport={"width": 1440, "height": 900},
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            # 后台导出常开新标签页，每个新页面都要挂下载监听，否则会漏接文件。
            context.on("page", lambda new_page: new_page.on("download", handle_download))
            page.on("download", handle_download)

            log("正在打开公众号后台……")
            for attempt in range(3):
                try:
                    page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
                    break
                except Exception as error:
                    if attempt == 2:
                        raise
                    log(f"打开后台失败，{3 - attempt - 1} 秒后重试（{error.__class__.__name__}）")
                    time.sleep(3)

            ensure_login(page)
            print_checklist()

            while not STOP_REQUESTED:
                time.sleep(0.5)
        finally:
            context.close()
    log("采集器已退出。")


if __name__ == "__main__":
    main()
