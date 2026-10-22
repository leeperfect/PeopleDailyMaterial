#!/usr/bin/env python3
"""仅用已保存的本地政策原文，补充官方元数据并刷新年度和主题索引。"""
import json
from pathlib import Path
from bs4 import BeautifulSoup
from collect_gov_policies import ROOT, export_index, write_json

FIELDS = {'索引号': 'official_index', '主题分类': 'official_subject', '发文机关': 'issuer',
          '成文日期': 'issued_date', '发文字号': 'document_number', '发布日期': 'official_published_date'}


def metadata(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    for table in soup.select('table.bd1'):
        for row in table.select('tr'):
            cells = row.find_all('td', recursive=False)
            for i, cell in enumerate(cells[:-1]):
                label = ''.join(cell.get_text().split()).rstrip('：:')
                if label in FIELDS:
                    result[FIELDS[label]] = cells[i+1].get_text(' ', strip=True)
    return result


def organize():
    catalog = json.loads((ROOT / 'catalog.json').read_text())
    enriched = 0
    for pid, item in catalog.items():
        raw = ROOT / 'raw' / f'{pid}.json'
        record = json.loads(raw.read_text())
        info = metadata((ROOT / 'raw' / f'{pid}.html').read_text())
        record.update(info)
        item.update(info)
        write_json(raw, record)
        lines = [f'# {item["title"]}', '', f'- 政策 ID：{pid}', f'- 栏目发布日期：{item["published_date"]}', f'- 来源：{item["url"]}', f'- 收录时间：{item["collected_at"]}']
        for label, key in FIELDS.items():
            if info.get(key):
                lines.append(f'- {label}：{info[key]}')
        lines += ['', '## 政策原文', '', record['body'], '']
        if record['attachments']:
            from urllib.parse import urljoin
            lines += ['## 正文附链', '']
            lines += [f'- [{a["title"]}]({urljoin(item["url"], a["url"])})' for a in record['attachments']]
        (ROOT / item['file']).write_text('\n'.join(lines) + '\n', encoding='utf-8')
        enriched += bool(info)
    write_json(ROOT / 'catalog.json', catalog)
    export_index(catalog)
    print(f'整理 {len(catalog)} 篇，其中 {enriched} 篇具有官网结构化发文信息；未提供的字段留空，不推测。')


if __name__ == '__main__':
    import fcntl
    with (ROOT / '.collect.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        organize()
