#!/usr/bin/env python3
"""公众号内容数据 API 采集器：通过已登录的 Chrome 拉取内容分析与用户增长数据。

为什么用 API 而不是导出 Excel：
- 内容分析页的日历控件有"点格子即关弹层"的交互缺陷，UI 自动化不稳定；
- 页面数据本来就来自后台 JSON 接口，换日期参数即可拿全量，稳定可重复；
- 接口返回的字段比 Excel 导出更全（如文章详情页的完读率、新增关注）。

采集范围（同一统计窗口）：
1. get_article_list —— 窗口内有阅读的全部文章清单（含窗口阅读数、近30天逐日）
2. detailpage —— 每篇文章发表后30天核心指标（阅读/时长/完读率/新增关注/分享/收藏等）
3. get_article_stat_tendency_and_source —— 账号级每日分渠道阅读
4. useranalysis —— 每日新关注/取关/净增/累计

前置条件：Chrome 以调试端口运行且已登录公众号后台
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        --remote-debugging-port=9222 \
        --user-data-dir=data/data_analysis/.collector_profile

用法：
    python3 scripts/collect_wechat_content_api.py 2026-06-08 2026-09-06
产物：data/data_analysis/raw/monetization/content_api/<窗口>/ 下 4 个 JSON + 清单
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CDP_URL = "http://127.0.0.1:9222"
TZ = ZoneInfo("Asia/Shanghai")
MP = "https://mp.weixin.qq.com"

# 互动指标解析：新版详情页用 .bottom_data_tips/.data_list，
# 渠道百分比与漏斗值从 Highcharts 无障碍描述文本中提取（服务端渲染，无 XHR）。
DETAIL_EXTRACT_JS = """
() => {
  const out = {metrics: {}, interactions: [], channels: {}, raw_ranges: []};
  for (const block of document.querySelectorAll('.bottom_data_tips')) {
    const label = (block.querySelector('.tips_name') || {}).innerText || '';
    const text = (block.innerText || '').replace(/\\n/g, ' ');
    out.metrics[label.trim()] = text.replace(label, '').trim();
  }
  for (const row of document.querySelectorAll('.data_list')) {
    const labelEl = row.querySelector('.list_left');
    out.interactions.push({
      label: labelEl ? (labelEl.innerText || '').trim() : '',
      text: (row.innerText || '').replace(/\\n/g, ' ').trim(),
    });
  }
  const bodyText = document.body.innerText;
  const channelSection = bodyText.split('阅读渠道构成')[1] || '';
  const pcts = [...channelSection.matchAll(/(\\d+(?:\\.\\d+)?)%/g)].map(m => parseFloat(m[1]));
  const names = ['推荐', '朋友圈', '聊天会话', '公众号消息', '公众号主页', '搜一搜', '其它'];
  if (pcts.length >= 7) names.forEach((n, i) => { out.channels[n] = pcts[i]; });
  for (const m of bodyText.matchAll(/(订阅漏斗分析|分享扩散分析)[\\s\\S]{0,400}?Data ranges from ([\\d.]+) to ([\\d.]+)/g)) {
    out.raw_ranges.push({section: m[1], min: parseFloat(m[2]), max: parseFloat(m[3])});
  }
  return out;
}
"""


def parse_number(text: object) -> float | None:
    """从 '17,083 人' / '10%' / '1.63 分钟' 这类文本里取数字。"""
    if text is None:
        return None
    match = re.search(r"(-?[\d,]+(?:\.\d+)?)", str(text).replace(",", ""))
    return float(match.group(1)) if match else None


def connect_page() -> tuple[object, object, str, str]:
    """连上常驻 Chrome 的公众号页面，返回 (playwright, page, token, fingerprint)。"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(CDP_URL)
    pages = [pg for ctx in browser.contexts for pg in ctx.pages]
    page = next((pg for pg in pages if "mp.weixin.qq.com" in pg.url), pages[-1] if pages else None)
    if page is None:
        raise RuntimeError("Chrome 中没有可用页面")
    match = re.search(r"token=(\d+)", page.url)
    if not match:
        raise RuntimeError("当前页面未登录公众号后台（URL 无 token）")
    fingerprint = page.evaluate("""
    () => {
      for (const e of performance.getEntriesByType('resource')) {
        const m = e.name.match(/fingerprint=([0-9a-f]+)/);
        if (m) return m[1];
      }
      return '';
    }
    """)
    return playwright, page, match.group(1), fingerprint


def api_get(page: object, path: str, token: str, fingerprint: str) -> dict:
    """在页面上下文里发带登录态的 fetch。借页面发请求是为了沿用会话 Cookie，
    脚本本身不接触凭证，符合"敏感信息不落盘"的要求。"""
    sep = "&" if "?" in path else "?"
    url = f"{MP}{path}{sep}fingerprint={fingerprint}&token={token}&lang=zh_CN&f=json"
    return page.evaluate(
        "async (url) => { const r = await fetch(url, {credentials: 'include'}); return await r.json(); }",
        url,
    )


def fetch_article_list(page: object, token: str, fp: str, begin_ts: int, end_ts: int) -> list[dict]:
    """分页拉取窗口内有阅读的全部文章。"""
    articles: list[dict] = []
    offset = 0
    while True:
        data = api_get(page, f"/misc/appmsganalysis?action=get_article_list"
                             f"&begin_timestamp={begin_ts}&end_timestamp={end_ts}"
                             f"&article_source=9999&offset={offset}&count=20", token, fp)
        if data.get("base_resp", {}).get("ret") != 0:
            raise RuntimeError(f"get_article_list 返回错误: {data.get('base_resp')}")
        batch = data.get("article_list", [])
        articles.extend(batch)
        if len(batch) < 20:
            break
        offset += 20
        time.sleep(0.8)
    return articles


def parse_detail_modern(data: dict, record: dict) -> None:
    """解析新版详情页（互动按"人"计，含收藏）。"""
    unlabeled = []
    for row in data["interactions"]:
        label, text = row["label"], row["text"]
        if label == "分享":
            record["share_uv"] = parse_number(text)
        elif label == "赞赏":
            record["reward_yuan"] = parse_number(text)
        elif label == "留言":
            record["comment_count"] = parse_number(text)
        elif label == "收藏":
            record["collect_uv"] = parse_number(text)
        elif not label:
            unlabeled.append(parse_number(text))
    if len(unlabeled) >= 2:
        record["wow_uv"], record["like_uv"] = unlabeled[0], unlabeled[1]
    record["interaction_unit"] = "人"


def parse_detail_legacy(text: str, record: dict) -> None:
    """解析旧版详情页（互动按"次"计，无收藏指标，带商品区块）。

    旧版无标签数字的顺序不固定，在看/点赞不可靠，只取有标签的分享和留言。
    """
    seg = text[text.rfind("互动"):text.find("阅读分析")]
    share = re.search(r"分享\s*\n([\d,]+)\s*次", seg)
    comment = re.search(r"留言\s*\n([\d,]+)\s*条", seg)
    record["share_uv"] = parse_number(share.group(1)) if share else None
    record["comment_count"] = parse_number(comment.group(1)) if comment else None
    record["interaction_unit"] = "次"


def fetch_article_detail(page: object, token: str, article: dict) -> dict:
    """抓单篇详情页并解析全部指标。"""
    publish_date = article["ref_date"].replace("/", "-")
    url = (f"{MP}/misc/appmsganalysis?action=detailpage"
           f"&msgid={article['msg_id']}_{article['item_idx']}&publish_date={publish_date}"
           f"&type=int&pageVersion=1&token={token}&lang=zh_CN")
    record = {
        "msg_id": article["msg_id"], "item_idx": article["item_idx"],
        "title": article["title"], "ref_date": article["ref_date"],
        "window_read_uv": article["total_read_uv"],
        "tendency_30d": article.get("tendency_list", ""),
    }
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2200)
    data = page.evaluate(DETAIL_EXTRACT_JS)
    metrics = data["metrics"]
    record.update({
        "read_uv": parse_number(metrics.get("阅读")),
        "avg_read_minutes": parse_number(metrics.get("平均阅读时长")),
        "completion_rate": parse_number(metrics.get("完读率")),
        "new_followers": parse_number(metrics.get("新增关注")),
        "listen_uv": parse_number(metrics.get("听全文")),
    })
    if data["interactions"]:
        parse_detail_modern(data, record)
    else:
        # 旧版页面没有 .data_list，整页文本兜底
        body_text = page.evaluate("() => document.body.innerText")
        parse_detail_legacy(body_text, record)
    record["channel_pct"] = data["channels"]
    for rng in data["raw_ranges"]:
        if rng["section"] == "订阅漏斗分析":
            record["deliver_uv"] = rng["max"]
            record["first_share_uv"] = rng["min"]
        elif rng["section"] == "分享扩散分析":
            record["share_driven_read_uv"] = rng["max"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号内容数据 API 采集器")
    parser.add_argument("start", help="窗口开始日期 YYYY-MM-DD")
    parser.add_argument("end", help="窗口结束日期 YYYY-MM-DD")
    parser.add_argument("--skip-details", action="store_true", help="只拉清单和趋势，不逐篇抓详情页")
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=TZ)
    end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=TZ)
    begin_ts, end_ts = int(start_dt.timestamp()), int(end_dt.timestamp())

    out_dir = ROOT / "data" / "data_analysis" / "raw" / "monetization" / "content_api" / f"{args.start}_{args.end}"
    out_dir.mkdir(parents=True, exist_ok=True)

    playwright, page, token, fp = connect_page()
    print(f"已连接 Chrome，窗口 {args.start} ~ {args.end}")
    try:
        # 1. 文章清单
        articles = fetch_article_list(page, token, fp, begin_ts, end_ts)
        (out_dir / "article_list.json").write_text(
            json.dumps(articles, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"文章清单：{len(articles)} 篇")

        # 2. 逐篇详情
        if not args.skip_details:
            details = []
            for index, art in enumerate(articles):
                try:
                    rec = fetch_article_detail(page, token, art)
                    details.append(rec)
                    print(f"  [{index+1}/{len(articles)}] {art['title'][:24]} 阅读={rec.get('read_uv')}")
                except Exception as exc:
                    details.append({"msg_id": art["msg_id"], "item_idx": art["item_idx"],
                                    "title": art["title"], "ref_date": art["ref_date"],
                                    "error": str(exc)[:200]})
                    print(f"  [{index+1}/{len(articles)}] {art['title'][:24]} 失败: {exc}")
                time.sleep(1.2)
            (out_dir / "article_details.json").write_text(
                json.dumps(details, ensure_ascii=False, indent=1), encoding="utf-8")

        # 3. 账号每日分渠道趋势
        tendency = api_get(page, f"/misc/appmsganalysis?begin_timestamp={begin_ts}&end_timestamp={end_ts}"
                                 f"&action=get_article_stat_tendency_and_source", token, fp)
        (out_dir / "channel_tendency.json").write_text(
            json.dumps(tendency, ensure_ascii=False, indent=1), encoding="utf-8")
        print("渠道趋势已保存")

        # 4. 用户增长
        growth = api_get(page, f"/misc/useranalysis?&begin_date={args.start}&end_date={args.end}"
                               f"&source=99999999&ajax=1", token, fp)
        (out_dir / "user_growth.json").write_text(
            json.dumps(growth, ensure_ascii=False, indent=1), encoding="utf-8")
        print("用户增长已保存")

        # 5. 采集清单（事实留存层的自描述）
        manifest = {
            "window": {"start": args.start, "end": args.end},
            "collected_at": datetime.now(TZ).isoformat(timespec="seconds"),
            "files": {},
        }
        for path in sorted(out_dir.glob("*.json")):
            manifest["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"产物目录：{out_dir.relative_to(ROOT)}")
    finally:
        playwright.stop()


if __name__ == "__main__":
    sys.exit(main())
