#!/usr/bin/env python3
"""中国政府网最新政策：低频、可续采的原文资料库。"""
import argparse
import csv
from collections import Counter
import hashlib
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / 'data/gov_policy'
BASE = 'https://www.gov.cn'
FEED = BASE + '/zhengce/zuixin/ZUIXINZHENGCE.json'
AGENT = 'PolicyResearchArchive/1.0'


def write_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def canonical(url):
    p = urlsplit(url)
    if p.hostname != 'www.gov.cn' or p.scheme not in ('http', 'https'):
        raise ValueError('目录出现非中国政府网链接，停止并人工检查：' + url)
    return urlunsplit(('https', p.netloc, p.path, '', ''))


def parse_body(html):
    soup = BeautifulSoup(html, 'html.parser')
    node = soup.select_one('#UCAP-CONTENT') or soup.select_one('.pages_content')
    if node is None:
        raise ValueError('未找到政策正文，需核查页面结构')
    for tag in node.select('script, style'):
        tag.decompose()
    body = node.get_text('\n', strip=True)
    if len(body) < 100 or any(x in body for x in ('访问过于频繁', '请输入验证码', '访问被拒绝')):
        raise ValueError('正文过短或疑似访问限制，停止采集')
    attachments = [{'title': a.get_text(strip=True), 'url': a['href']} for a in node.select('a[href]')]
    return body, attachments


def collect(limit, years, backfill=False):
    for folder in ('raw', 'vault', 'reports'):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    state_path = ROOT / 'catalog.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    session = requests.Session()
    session.headers['User-Agent'] = AGENT
    last_request = 0
    robots = RobotFileParser()
    delay = 6

    def get(url, check=True):
        nonlocal last_request
        if check and not robots.can_fetch(AGENT, url):
            raise RuntimeError('robots.txt 不允许采集：' + url)
        time.sleep(max(0, delay + random.uniform(0, 3) - (time.monotonic() - last_request)))
        last_request = time.monotonic()
        r = session.get(url, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError(f'HTTP {r.status_code}，本次停止，不自动重试：{url}')
        r.encoding = 'utf-8'
        return r

    rules = get(BASE + '/robots.txt', check=False).text.lstrip('\ufeff')
    robots.parse(rules.splitlines())
    delay = max(6, robots.crawl_delay(AGENT) or 0)
    rows = get(FEED).json()
    if not isinstance(rows, list) or not rows:
        raise ValueError('政策目录为空或结构变化')
    write_json(ROOT / 'reports' / 'source-list.json', rows)
    rows = [r for r in rows if r['DOCRELPUBTIME'][:4] in years]
    write_json(ROOT / 'reports' / 'target-list.json', rows)
    print(f'目标年份 {years}，目录 {len(rows)} 条，已收录 {len(state)} 条', flush=True)
    added = []
    # 目录全量比较，不以日期截断，避免漏掉补发文件；每次最多收集 limit 篇。
    for row in rows:
        url = canonical(row['URL'])
        pid = 'gov_' + hashlib.sha256(url.encode()).hexdigest()[:20]
        if pid in state:
            continue
        if len(added) >= limit:
            break
        if backfill and added and len(added) % 30 == 0:
            print('已完成30篇，休息60秒后继续。', flush=True)
            time.sleep(60)
        html = get(url).text
        body, attachments = parse_body(html)
        title = row['TITLE'].strip()
        date = row['DOCRELPUBTIME']
        record = dict(policy_id=pid, title=title, published_date=date, url=url,
                      collected_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
                      body=body, attachments=attachments)
        # 原始页面和结构化原文一起留存；附件仅登记，不自动批量下载。
        (ROOT / 'raw' / f'{pid}.html').write_text(html, encoding='utf-8')
        write_json(ROOT / 'raw' / f'{pid}.json', record)
        year = date[:4]
        (ROOT / 'vault' / year).mkdir(exist_ok=True)
        filename = f'{year}/{date}-{pid}.md'
        (ROOT / 'vault' / filename).write_text(
            f'# {title}\n\n- 政策 ID：{pid}\n- 栏目发布日期：{date}\n- 来源：{url}\n'
            f'- 收录时间：{record["collected_at"]}\n\n## 政策原文\n\n{body}\n\n'
            + ('## 正文附链\n\n' + '\n'.join(f'- [{a["title"]}]({requests.compat.urljoin(url, a["url"])})' for a in attachments) if attachments else ''), encoding='utf-8')
        state[pid] = {k: record[k] for k in ('policy_id', 'title', 'published_date', 'url', 'collected_at')}
        state[pid]['file'] = 'vault/' + filename
        write_json(state_path, state)
        export_index(state)
        added.append(title)
        print(f'已新增 {len(added)} 篇：{date} {title}', flush=True)
    export_index(state)
    return dict(status='success', years=years, target_count=len(rows), added=len(added), total=len(state), titles=added,
                remaining=sum('gov_' + hashlib.sha256(canonical(r['URL']).encode()).hexdigest()[:20] not in state for r in rows))


TOPICS = {
    '经济发展与营商环境': ('经济', '企业', '营商', '民营', '投资', '市场', '金融', '消费', '产业', '贸易', '外资', '税', '债', '价格'),
    '民生保障与公共服务': ('就业', '养老', '医疗', '医保', '药品', '卫生', '教育', '高校', '住房', '公积金', '残疾', '救助', '儿童', '生育', '托育', '社会保障', '退役军人'),
    '科技创新与数字发展': ('科技', '创新', '数字', '人工智能', '数据', '互联网', '知识产权', '新质生产力'),
    '城乡发展与乡村振兴': ('乡村', '农村', '农业', '农民', '粮食', '城市', '城镇', '土地', '区域', '县', '基础设施', '交通', '水利'),
    '生态环境与绿色转型': ('生态', '环境', '绿色', '节能', '碳', '污染', '森林', '林区', '能源', '电力', '自然保护'),
    '社会治理与安全法治': ('安全', '应急', '监管', '治理', '法治', '行政', '审计', '条例', '追究', '信访', '检查', '防灾'),
    '文化体育与文旅消费': ('文化', '体育', '旅游', '赛事', '文物', '遗产', '健身'),
}


def topics(title):
    return [name for name, words in TOPICS.items() if any(w in title for w in words)] or ['综合政策与其他']


def export_index(state):
    ordered = sorted(state.values(), key=lambda r: (r['published_date'], r['policy_id']), reverse=True)
    counts = Counter(r['published_date'][:4] for r in ordered)
    intro = ['# 国务院政策资料索引', '', '来源：中国政府网“最新政策”栏目。范围为该栏目所列文件，含联合印发文件，不代表所有部委政策。保留原题；栏目发布日期不等于施行日期。', '', f'已收录 {len(state)} 篇。', '']
    for year in sorted(counts, reverse=True):
        intro.append(f'- [{year}年政策目录]({year}.md)：{counts[year]} 篇')
    intro += ['', '- [热点分析主题索引](topics.md)', '- [结构化政策清单](catalog.csv)', '- [采集完整性核对](reports/coverage.md)', '']
    for year in sorted(counts, reverse=True):
        group = [r for r in ordered if r['published_date'].startswith(year)]
        lines = [f'# {year}年政策文件', '', f'已收录 {len(group)} 篇，按栏目发布日期倒序排列。', '']
        month = None
        for r in group:
            if r['published_date'][:7] != month:
                month = r['published_date'][:7]
                lines += [f'## {month}', '']
            lines.append(f'- {r["published_date"]} [{r["title"]}]({r["file"]}) · [官方原文]({r["url"]})')
        (ROOT / f'{year}.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (ROOT / 'index.md').write_text('\n'.join(intro) + '\n', encoding='utf-8')
    lines = ['# 热点分析主题索引', '', '以下按标题关键词辅助归类，一篇可进入多个主题，仅用于检索，不是对政策内容、效力或重要性的判断。分析前请阅读全文。', '']
    for topic in list(TOPICS) + ['综合政策与其他']:
        group = [r for r in ordered if topic in topics(r['title'])]
        lines += [f'## {topic}（{len(group)}篇）', '']
        lines += [f'- {r["published_date"]} [{r["title"]}]({r["file"]})' for r in group]
        lines.append('')
    (ROOT / 'topics.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    target_path = ROOT / 'reports' / 'target-list.json'
    if target_path.exists():
        target = json.loads(target_path.read_text())
        missing = [r for r in target if 'gov_' + hashlib.sha256(canonical(r['URL']).encode()).hexdigest()[:20] not in state]
        report = ['# 2025—2026年政策采集核对', '', '核对范围：中国政府网“最新政策”公开目录，按栏目发布日期筛选。', '', f'- 目录目标：{len(target)} 条', f'- 尚未收录：{len(missing)} 条', f'- 核对时间：{datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()}', '']
        for year in sorted({r['DOCRELPUBTIME'][:4] for r in target}):
            n = sum(r['DOCRELPUBTIME'].startswith(year) for r in target)
            left = sum(r['DOCRELPUBTIME'].startswith(year) for r in missing)
            report.append(f'- {year}年：目录 {n} 条，已收录 {n-left} 条，待收录 {left} 条')
        report += ['', '## 待收录文件', '']
        report += [f'- {r["DOCRELPUBTIME"]} [{r["TITLE"]}]({r["URL"]})' for r in missing] or ['无。']
        (ROOT / 'reports' / 'coverage.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    with (ROOT / 'catalog.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['政策ID', '标题', '栏目发布日期', '年份', '检索主题（标题辅助归类）', '发文机关', '发文字号', '成文日期', '官方主题分类', '官方链接', '阅读文件'])
        writer.writerows([r['policy_id'], r['title'], r['published_date'], r['published_date'][:4], '；'.join(topics(r['title'])), r.get('issuer', ''), r.get('document_number', ''), r.get('issued_date', ''), r.get('official_subject', ''), r['url'], r['file']] for r in ordered)


if __name__ == '__main__':
    import fcntl
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--years', nargs='+', default=[str(y) for y in range(2025, datetime.now(ZoneInfo('Asia/Shanghai')).year + 1)])
    parser.add_argument('--backfill', action='store_true', help='历史补采：允许较大总量，每30篇暂停60秒')
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT / '.collect.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('已有采集任务运行，本次退出')
        try:
            if not 1 <= args.limit <= (300 if args.backfill else 30):
                raise ValueError('日常单次最多30篇，历史补采单次最多300篇')
            if any(not re.fullmatch(r'20[0-9]{2}', y) for y in args.years):
                raise ValueError('年份格式应为四位数字')
            result = collect(args.limit, args.years, args.backfill)
            from organize_gov_policies import organize
            organize()
        except Exception as exc:
            saved = json.loads((ROOT / 'catalog.json').read_text()) if (ROOT / 'catalog.json').exists() else {}
            result = dict(status='failed', error=str(exc), total=len(saved), partial_saved=True)
        result['time'] = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
        write_json(ROOT / 'reports' / 'latest-run.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result['status'] == 'success' else 1)
