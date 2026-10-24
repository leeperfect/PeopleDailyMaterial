#!/usr/bin/env python3
"""串行同步一份人民日报正式版；原文、稳定编号与阅读视图一起入库。"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.article_database import ArticleStore
from modules.article_identity import build_article_id
from modules.markdown_writer import MarkdownWriter
from modules.parser import ContentParser
from modules.processor import DataProcessor


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def collect(issue: date, interval: float = 1.5):
    key = issue.strftime('%Y%m%d')
    raw = ROOT / 'data/raw' / f'articles_{key}.json'
    pages = ROOT / 'data/raw/people_daily_pages' / key
    pages.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / 'data/exports' / f'people_daily_issue_{key}.json'
    report = {'issue_date':issue.isoformat(), 'status':'in_progress', 'request_interval':interval,
              'sections':[], 'articles':[], 'excluded':[], 'errors':[]}
    if raw.exists():
        articles = json.loads(raw.read_text(encoding='utf-8'))
    else:
        articles = []
    by_id = {build_article_id(a):a for a in articles}
    parser, processor, writer = ContentParser(), DataProcessor(), MarkdownWriter(str(ROOT/'data/vault'))
    rules = RobotFileParser()
    last_request = 0.0

    def fetch(url: str, name: str, robots=False):
        nonlocal last_request
        if urlparse(url).hostname != 'paper.people.com.cn':
            raise ValueError('目录包含非正式版站点链接，停止：'+url)
        dest = pages/name
        if dest.exists() and not robots:
            return dest.read_text(encoding='utf-8')
        if not robots and not rules.can_fetch('PeopleDailyMaterial/1.0', url):
            raise RuntimeError('robots不允许采集：'+url)
        time.sleep(max(0, interval-(time.monotonic()-last_request)))
        result = subprocess.run(['curl','--location','--max-time','30','--silent','--show-error',
                                 '--user-agent','PeopleDailyMaterial/1.0 (personal research)',
                                 '--write-out','%{http_code}',url,'--output',str(dest)],
                                text=True,capture_output=True)
        last_request = time.monotonic()
        code = int(result.stdout) if result.stdout.isdigit() else 0
        if robots and code == 404:
            report['robots_status'] = '404; no robots restrictions published'
            return ''
        if result.returncode or code != 200:
            dest.unlink(missing_ok=True)
            raise RuntimeError(f'官网请求失败，停止本轮而不重试绕过：HTTP {code} {url} {result.stderr[:120]}')
        return dest.read_text(encoding='utf-8')

    store = None
    try:
        rules.parse(fetch('https://paper.people.com.cn/robots.txt','robots.txt',robots=True).splitlines())
        base = f'https://paper.people.com.cn/rmrb/pc/layout/{issue:%Y%m/%d}/'
        first = fetch(base+'node_01.html','node_01.html')
        node_ids = sorted(set(re.findall(r'node_(\d+)\.html',first)))
        if not node_ids:
            raise RuntimeError('正式版目录没有版面导航，不能按成功处理')
        targets = {}
        for node in node_ids:
            url = base+f'node_{node}.html'
            html = first if node=='01' else fetch(url,f'node_{node}.html')
            links, section = parser.parse_directory(html)
            report['sections'].append({'section_no':node,'section_name':section,'articles':len(links),'url':url})
            for info in links:
                link = f'https://paper.people.com.cn/rmrb/pc/content/{issue:%Y%m/%d}/{info["href"]}'
                targets.setdefault(link,{**info,'section_no':node,'section_name':section})
            print(f'目录 {node} {section}：{len(links)} 篇',flush=True)
        report['directory_article_count'] = len(targets)
        if not targets:
            raise RuntimeError('目录未解析出文章')
        backup = ROOT/'data/core/backups'/f'before-paper-{key}-{datetime.now():%H%M%S}.sqlite'
        backup.parent.mkdir(parents=True,exist_ok=True)
        source = sqlite3.connect(f'file:{ROOT / "data/core/articles.sqlite"}?mode=ro',uri=True)
        dest = sqlite3.connect(backup); source.backup(dest);dest.close();source.close()
        report['core_backup'] = str(backup.relative_to(ROOT))
        store = ArticleStore(str(ROOT/'data/core/articles.sqlite'))
        for index,(url,info) in enumerate(targets.items(),1):
            aid = build_article_id({'date':issue.isoformat(),'url':url})
            if re.search(r'本版责编|一版责编|欢迎赐稿',info['title']) or info['section_name']=='广告':
                fetch(url,info['href'])
                report['excluded'].append({'article_id':aid,'title':info['title'],'url':url,'reason':'版面联系信息或广告；原HTML留存，不作为文章入库'})
                continue
            existing = store.conn.execute('SELECT article_id,content,raw_path,markdown_path FROM articles WHERE article_id=?',(aid,)).fetchone()
            if existing and existing['content'] and aid in by_id:
                report['articles'].append({'article_id':aid,'url':url,'title':by_id[aid]['title'],'status':'existing'})
                continue
            html = fetch(url,info['href'])
            article = parser.parse_article(html,url)
            if not article or not article.get('title'):
                raise RuntimeError('文章结构无法解析：'+url)
            # 官网meta日期可能是旧模板值，只核对正文中的报纸日期。
            if not re.search(rf'{issue.year}年\s*{issue.month}月\s*{issue.day}日',html):
                raise RuntimeError('正文未找到预期报纸日期：'+url)
            if not article.get('content','').strip():
                if re.search(r'图片|广告|责编',info['title']) or info['section_name']=='广告':
                    report['excluded'].append({'article_id':aid,'title':info['title'],'url':url,'reason':'非文字资料，保留原HTML'})
                    continue
                raise RuntimeError('文章正文为空，需复核：'+url)
            article.update(date=issue.isoformat(),article_id=aid,source='people_daily',source_url=url,
                           section_no=info['section_no'],section_name=info['section_name'],
                           raw_path=str(raw.relative_to(ROOT)),raw_html_path=str((pages/info['href']).relative_to(ROOT)))
            article['content'] = processor.clean_content(article['content'])
            article['keywords'] = processor.extract_keywords(article['title']+' '+article['content'])
            article['summary'] = processor.extract_summary(article['content'])
            article['category'] = processor.classify_article(article)
            # 不覆盖已有人工阅读批注；本轮日期无旧文章时生成新视图。
            md = writer.save_article(article,datetime.combine(issue,datetime.min.time()),info['section_no'],info['section_name'])
            if not md:
                raise RuntimeError('阅读视图保存失败：'+aid)
            article['markdown_path'] = str(Path(md).relative_to(ROOT))
            by_id[aid] = article
            dump(raw,list(by_id.values()))
            store.upsert_article(article)
            report['articles'].append({'article_id':aid,'url':url,'title':article['title'],'word_count':len(article['content']),'status':'downloaded'})
            dump(report_path,report)
            print(f'正文 {index}/{len(targets)} {info["section_no"]} {article["title"][:45]}：{len(article["content"])}字',flush=True)
        report.update(status='complete',completed_at=datetime.now().astimezone().isoformat(timespec='seconds'),
                      stored_articles=len(report['articles']),excluded_articles=len(report['excluded']))
        assert len(report['articles'])+len(report['excluded'])==len(targets)
        dates={r[0] for r in store.conn.execute('SELECT DISTINCT date FROM articles')}
        previous=max((d for d in dates if d<issue.isoformat()),default=issue.isoformat())
        state_path=ROOT/'data/core/people_daily_collection_state.json'
        old_state=json.loads(state_path.read_text()) if state_path.exists() else {}
        missing=[d for d in old_state.get('known_missing_dates',[]) if d not in dates]
        day=date.fromisoformat(previous)+timedelta(days=1)
        while day<issue:
            if day.isoformat() not in dates: missing.append(day.isoformat())
            day+=timedelta(days=1)
        state={'updated_at':report['completed_at'],'latest_complete_issue':issue.isoformat(),
               'latest_issue_report':str(report_path.relative_to(ROOT)),'latest_issue_articles':len(report['articles']),
               'known_missing_dates':sorted(set(missing)),'previous_available_until':previous}
        if old_state.get('latest_complete_issue','') > issue.isoformat():
            state={**old_state,'updated_at':report['completed_at'],'known_missing_dates':sorted(set(missing))}
        dump(state_path,state)
    except Exception as exc:
        report.update(status='failed',error=str(exc))
        raise
    finally:
        if store: store.close()
        dump(report_path,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['articles','sections']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--date',required=True,type=date.fromisoformat)
    ap.add_argument('--interval',type=float,default=1.5)
    args=ap.parse_args()
    if args.interval<1:ap.error('串行请求间隔不能小于1秒')
    collect(args.date,args.interval)
