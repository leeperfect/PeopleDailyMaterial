#!/usr/bin/env python3
"""远程驾驶本机 Chrome 的小工具：每次执行一个动作，供 Agent 逐步操作公众号后台。

为什么不把整套流程写成一个全自动脚本一次跑完：
- 公众号后台页面结构只有"看到当前页面"后才能确定，写死的选择器一次跑不通；
- 所以 Chrome 常驻运行（带调试端口），本脚本每次连上去做一个动作——
  看页面（snapshot）、截图（shot）、点文字（click）、点导出并接管下载（export），
  由 Agent 根据每一步的真实页面决定下一步。

Chrome 启动方式（只需一次）：
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        --remote-debugging-port=9222 \
        --user-data-dir=data/data_analysis/.collector_profile
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from collect_wechat_mp_stats import (  # noqa: E402
    INBOX_DIR,
    classify_file,
    handle_download,
)

CDP_URL = "http://127.0.0.1:9222"
MP_DOMAIN = "mp.weixin.qq.com"

# 抽取页面上可见可点元素的 JS：只收集有文字、在视口附近的链接/按钮/菜单项，
# 避免整页 DOM 文本太长淹没关键信息。
SNAPSHOT_JS = """
() => {
  const pick = [];
  const nodes = document.querySelectorAll('a, button, [role=button], [role=menuitem], li, span, div, input');
  for (const el of nodes) {
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    const style = window.getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') continue;
    const tag = el.tagName.toLowerCase();
    const text = (el.innerText || el.value || el.placeholder || '').trim().replace(/\\s+/g, ' ');
    if (!text || text.length > 60) continue;
    // 只保留"叶子级"元素，父容器会重复包含同样的文字。
    if (tag !== 'input' && el.querySelector('a, button, li, span, div') &&
        el.children.length > 0 && text.length > 25) continue;
    pick.push({tag, text, cls: (el.className || '').toString().slice(0, 40)});
  }
  const seen = new Set();
  const out = [];
  for (const item of pick) {
    const key = item.tag + '|' + item.text;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(item);
    if (out.length >= 300) break;
  }
  return out;
}
"""


def connect() -> tuple[object, object, object]:
    """连上常驻 Chrome，返回 (playwright, browser, 当前公众号页面)。"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(CDP_URL)
    contexts = browser.contexts
    if not contexts:
        raise RuntimeError("Chrome 里没有可用窗口，请确认调试端口启动正常")
    pages = [page for ctx in contexts for page in ctx.pages]
    for page in pages:
        if MP_DOMAIN in page.url:
            return playwright, browser, page
    return playwright, browser, pages[-1]


def close(playwright: object, browser: object) -> None:
    # 只断开连接，不关 Chrome——浏览器必须留着，登录态和页面都在里面。
    browser.close()
    playwright.stop()


def cmd_status(page: object) -> None:
    print(f"URL: {page.url}")
    print(f"TITLE: {page.title()}")


def cmd_wait_login(page: object, timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if "token=" in page.url:
            print("已登录")
            return
        time.sleep(2)
    print("等待超时，仍未检测到登录（页面 URL 中无 token）")


def cmd_snapshot(page: object, keyword: str | None) -> None:
    items = page.evaluate(SNAPSHOT_JS)
    for index, item in enumerate(items):
        if keyword and keyword not in item["text"]:
            continue
        print(f"{index:>3} [{item['tag']}] {item['text']}  <{item['cls']}>")


def cmd_click(page: object, text: str, exact: bool) -> None:
    locator = page.get_by_text(text, exact=exact).first
    locator.scroll_into_view_if_needed(timeout=10000)
    locator.click(timeout=10000)
    page.wait_for_timeout(1500)
    print(f"已点击：{text}")
    print(f"URL: {page.url}")


def cmd_export(page: object, text: str, exact: bool, timeout: int,
               kind: str | None = None, slot_name: str | None = None) -> None:
    """点"导出"并接管下载：文件落盘后自动识别类型、归档、入库。

    流量主按广告位导出的文件名完全相同且不含广告位列，
    必须靠 --kind ad_slot_daily --slot-name 显式指定归属，
    否则不同广告位的数据会互相覆盖。
    """
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    with page.expect_download(timeout=timeout * 1000) as download_info:
        page.get_by_text(text, exact=exact).first.click()
    download = download_info.value
    print(f"接到下载：{download.suggested_filename}")
    if not kind:
        handle_download(download)
        return

    import subprocess
    from collect_wechat_mp_stats import RAW_MONETIZATION_DIR

    suffix = f"_{slot_name}" if slot_name else ""
    original = download.suggested_filename or f"download-{int(time.time())}.csv"
    stem = Path(original).stem
    ext = Path(original).suffix
    destination_dir = RAW_MONETIZATION_DIR / kind
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{stem}{suffix}{ext}"
    download.save_as(str(destination))
    command = [sys.executable, str(ROOT / "scripts" / "import_wechat_monetization_stats.py"),
               str(destination), "--kind", kind]
    if slot_name:
        command += ["--slot-name", slot_name]
    result = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
    if result.returncode == 0:
        for line in result.stdout.strip().splitlines():
            print(f"  入库：{line}")
    else:
        print(f"  入库失败：{result.stderr.strip().splitlines()[-1] if result.stderr else '未知错误'}")
        print(f"  文件保留在 {destination}")


def cmd_goto(page: object, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    print(f"URL: {page.url}")


def cmd_shot(page: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=False)
    print(f"截图已保存：{path}")


def cmd_eval(page: object, js: str) -> None:
    print(page.evaluate(js))


def main() -> None:
    parser = argparse.ArgumentParser(description="远程驾驶本机 Chrome 操作公众号后台")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    wait = sub.add_parser("wait-login")
    wait.add_argument("--timeout", type=int, default=300)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--filter", default=None, help="只显示包含该关键词的元素")
    click = sub.add_parser("click")
    click.add_argument("text")
    click.add_argument("--exact", action="store_true")
    export = sub.add_parser("export")
    export.add_argument("text", help="导出按钮上的文字，如：导出 Excel")
    export.add_argument("--exact", action="store_true")
    export.add_argument("--timeout", type=int, default=60)
    export.add_argument("--kind", default=None, help="强制入库类型，如 ad_slot_daily")
    export.add_argument("--slot-name", default=None, help="广告位名称（配 --kind ad_slot_daily）")
    goto = sub.add_parser("goto")
    goto.add_argument("url")
    shot = sub.add_parser("shot")
    shot.add_argument("path", type=Path)
    evaluate = sub.add_parser("eval")
    evaluate.add_argument("js")
    args = parser.parse_args()

    playwright, browser, page = connect()
    try:
        if args.command == "status":
            cmd_status(page)
        elif args.command == "wait-login":
            cmd_wait_login(page, args.timeout)
        elif args.command == "snapshot":
            cmd_snapshot(page, args.filter)
        elif args.command == "click":
            cmd_click(page, args.text, args.exact)
        elif args.command == "export":
            cmd_export(page, args.text, args.exact, args.timeout, args.kind, args.slot_name)
        elif args.command == "goto":
            cmd_goto(page, args.url)
        elif args.command == "shot":
            cmd_shot(page, args.path)
        elif args.command == "eval":
            cmd_eval(page, args.js)
    finally:
        close(playwright, browser)


if __name__ == "__main__":
    main()
