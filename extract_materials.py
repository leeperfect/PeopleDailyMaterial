#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民日报素材提取器 v1.0

功能：
1. 基于规则的智能提取（不需要 API）
2. 收集人工 Callout 标注
3. 输出到 Obsidian _素材库

用法：
  python extract_materials.py                     # 处理所有文章
  python extract_materials.py --date 2026-04-01   # 处理指定日期
  python extract_materials.py --limit 10          # 只处理前10篇
  python extract_materials.py --collect-annotations  # 仅收集人工标注
"""

import os
import re
import sys
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ==================== 配置 ====================
VAULT_PATH = Path("data/vault")
OUTPUT_PATH = VAULT_PATH / "_素材库"
GOLDEN_QUOTES_DIR = OUTPUT_PATH / "金句"
CASES_DIR = OUTPUT_PATH / "案例"
WRITING_METHODS_DIR = OUTPUT_PATH / "写作方法"
TOPICS_DIR = OUTPUT_PATH / "热点专题"
ANNOTATIONS_DIR = OUTPUT_PATH / "我的标注"

# ==================== 提取规则 ====================

# 金句特征模式
QUOTE_PATTERNS = [
    # 1. 习近平引用
    re.compile(r'["""](.*?(?:习近平|总书记).*?)["""]', re.DOTALL),
    # 2. 引号包裹的短句（15-100字）
    re.compile(r'(?<![说道称表示])["""]([\u4e00-\u9fff，、；：！？…—]{15,100})["""]'),
    # 3. 让...更加/让...成为...
    re.compile(r'(让[\u4e00-\u9fff，、]{4,30}(?:更加|成为)[\u4e00-\u9fff，、。！]{4,30}[。！])'),
    # 4. 排比三句式：X的Y，X的Y，X的Y。
    re.compile(r'([\u4e00-\u9fff]{2,8}的[\u4e00-\u9fff]{2,8}[，,][\u4e00-\u9fff]{2,8}的[\u4e00-\u9fff]{2,8}[，,][\u4e00-\u9fff]{2,8}的[\u4e00-\u9fff]{2,8}[。！])'),
    # 5. 政策指令句：以/把/要/必须/始终/坚持 + 动作
    re.compile(r'((?:要|必须|始终|坚持|坚定不移|深入推进|全面)[\u4e00-\u9fff，、]{10,60}[。！])'),
    # 6. 四字短语链（至少3组四字词语）
    re.compile(r'([\u4e00-\u9fff]{4}[，、][\u4e00-\u9fff]{4}[，、][\u4e00-\u9fff]{4}[\u4e00-\u9fff，、。！]{0,20}[。！])'),
    # 7. 比喻/类比句：如/像/是...的...
    re.compile(r'([\u4e00-\u9fff]{2,15}(?:如同|好比|犹如|正如|恰似|是[\u4e00-\u9fff]{2,6}的[\u4e00-\u9fff]{2,6})[\u4e00-\u9fff，、]{5,40}[。！])'),
    # 8. 短句收尾（段落最后一句，20-60字，有文采的）
    re.compile(r'[。！]([\u4e00-\u9fff，、；：""]{15,60}[。！])$', re.MULTILINE),
    # 9. 不仅...而且/更.../也... 递进句
    re.compile(r'((?:不仅|不只|不但)[\u4e00-\u9fff，、]{5,25}(?:而且|更|也|还)[\u4e00-\u9fff，、]{5,30}[。！])'),
]

# 案例特征关键词
CASE_INDICATORS = [
    r'在(.{2,6}(?:省|市|区|县|镇|村))',  # 地名
    r'(\d+(?:\.?\d+)?%)',  # 百分比数据
    r'(\d+(?:\.\d+)?(?:亿|万|千|百)(?:元|吨|亩|人|户|家|个|台))',  # 具体数字
]

# 修辞手法特征
RHETORIC_PATTERNS = {
    '排比': re.compile(r'([\u4e00-\u9fff]{2,6}[，,][\u4e00-\u9fff]{2,6}[，,][\u4e00-\u9fff]{2,6}[。！])'),
    '对仗': re.compile(r'([\u4e00-\u9fff]{4,8}[，,][\u4e00-\u9fff]{4,8}[。；])'),
    '设问': re.compile(r'([\u4e00-\u9fff]{5,30}[？?](?:\n|\s)*[\u4e00-\u9fff]{5,50}[。！])'),
}

# Callout 标注解析
CALLOUT_PATTERN = re.compile(
    r'> \[!(quote|example|tip|abstract|info)\]\s*(.*?)(?:\n)((?:> .*(?:\n|$))*)',
    re.MULTILINE
)

CALLOUT_TYPE_MAP = {
    'quote': '金句',
    'example': '案例',
    'tip': '修辞',
    'abstract': '框架',
    'info': '专题',
}

# 高亮标注
HIGHLIGHT_PATTERN = re.compile(r'==(.*?)==')


# ==================== 工具函数 ====================

def parse_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}
    return {}


def get_body(content: str) -> str:
    """获取文章正文（去掉 frontmatter）"""
    match = re.match(r'^---\s*\n.*?\n---\s*\n(.*)$', content, re.DOTALL)
    return match.group(1) if match else content


def split_paragraphs(text: str) -> list:
    """将正文拆分为段落"""
    return [p.strip() for p in text.split('\n\n') if p.strip() and not p.strip().startswith('#') and not p.strip().startswith('>')]


def escape_yaml_string(s: str) -> str:
    """转义 YAML 字符串"""
    return s.replace('"', '\\"')


# 热点专题关键词体系（更细粒度的子主题）
TOPIC_KEYWORDS = {
    '生态文明': {
        'keywords': ['生态', '绿色', '环境', '碳', '植树', '造林', '治沙', '污染', '节能', '低碳', '双碳', '气候'],
        'subtopics': {
            '碳达峰碳中和': ['碳达峰', '碳中和', '双碳', '碳排放', '碳交易', '低碳'],
            '生物多样性': ['生物多样性', '物种', '保护区', '国家公园', '野生动物', '濒危'],
            '水资源保护': ['水资源', '河长制', '长江保护', '黄河', '治水', '水污染'],
            '绿色发展': ['绿色发展', '清洁能源', '新能源', '光伏', '风电', '节能减排'],
        }
    },
    '科技创新': {
        'keywords': ['科技', '创新', '数字', '量子', '人工智能', 'AI', '芯片', '技术', '大数据', '5G', '算力'],
        'subtopics': {
            '人工智能': ['人工智能', 'AI', '大模型', '深度学习', '机器人', '智能'],
            '数字经济': ['数字经济', '数字化', '数字中国', '数据要素', '大数据', '算力'],
            '芯片半导体': ['芯片', '半导体', '集成电路', '光刻', '晶圆'],
            '航天科技': ['航天', '卫星', '火箭', '空间站', '嫦娥', '天问', '北斗'],
        }
    },
    '改革开放': {
        'keywords': ['改革', '开放', '制度', '体制', '营商环境', '自贸区', '对外开放'],
        'subtopics': {
            '营商环境': ['营商环境', '放管服', '审批', '简政放权'],
            '国企改革': ['国企改革', '混合所有制', '央企', '国资'],
            '金融改革': ['金融改革', '资本市场', '注册制', '利率'],
        }
    },
    '乡村振兴': {
        'keywords': ['乡村', '农业', '农村', '农民', '脱贫', '振兴', '粮食', '三农'],
        'subtopics': {
            '粮食安全': ['粮食', '耕地', '种子', '农田', '粮食安全'],
            '乡村产业': ['乡村产业', '电商', '直播带货', '农产品', '特色产业'],
            '乡村治理': ['乡村治理', '村规民约', '基层', '村委'],
        }
    },
    '民生保障': {
        'keywords': ['民生', '就业', '教育', '医疗', '养老', '住房', '社保', '生育'],
        'subtopics': {
            '教育改革': ['教育', '双减', '高考', '职业教育', '学前教育', '义务教育'],
            '医疗健康': ['医疗', '医保', '公立医院', '药品', '疫苗', '中医药'],
            '养老服务': ['养老', '老龄化', '适老', '养老金', '退休'],
            '住房保障': ['住房', '保障房', '租赁', '房地产', '棚改'],
        }
    },
    '高质量发展': {
        'keywords': ['高质量', '发展', '经济', '产业', '转型', '新质生产力', '消费'],
        'subtopics': {
            '新质生产力': ['新质生产力', '新动能', '新赛道'],
            '消费升级': ['消费', '内需', '扩大内需', '消费升级', '促消费'],
            '产业升级': ['产业链', '供应链', '制造业', '产业升级', '转型升级'],
            '区域协调': ['区域协调', '京津冀', '长三角', '粤港澳', '西部', '东北振兴', '中部崛起'],
        }
    },
    '党的建设': {
        'keywords': ['党', '从严', '纪律', '作风', '初心', '使命', '反腐', '巡视'],
        'subtopics': {
            '反腐倡廉': ['反腐', '廉政', '巡视', '纪检', '查处'],
            '基层党建': ['基层党建', '支部', '党员', '组织建设'],
            '干部作风': ['作风', '形式主义', '官僚主义', '为民服务'],
        }
    },
    '法治建设': {
        'keywords': ['法治', '法律', '法典', '司法', '依法', '立法', '执法'],
        'subtopics': {
            '司法改革': ['司法改革', '公正', '审判', '检察'],
            '法治政府': ['法治政府', '行政执法', '依法行政'],
        }
    },
    '文化自信': {
        'keywords': ['文化', '文明', '传承', '非遗', '中华', '文旅', '博物馆'],
        'subtopics': {
            '非遗传承': ['非遗', '非物质文化遗产', '传统工艺', '传承人'],
            '文旅融合': ['文旅', '旅游', '文化产业', '博物馆', '景区'],
            '文明实践': ['文明实践', '新时代文明', '志愿服务', '公共文化'],
        }
    },
    '国际合作': {
        'keywords': ['国际', '全球', '合作', '一带一路', '人类命运', '外交', '贸易'],
        'subtopics': {
            '一带一路': ['一带一路', '丝绸之路', '互联互通'],
            '多边合作': ['联合国', 'G20', '金砖', '上合', 'APEC', 'RCEP'],
            '中美关系': ['中美', '美国', '贸易战', '中美关系'],
        }
    },
}


def classify_theme(text: str) -> list:
    """根据内容判断主题分类"""
    themes = []
    for theme, config in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in config['keywords']):
            themes.append(theme)
    return themes[:3] if themes else ['综合']


def classify_subtopics(text: str, themes: list) -> dict:
    """根据内容判断子专题，返回 {theme: [subtopic_names]}"""
    result = {}
    for theme in themes:
        subs = []
        if theme in TOPIC_KEYWORDS and 'subtopics' in TOPIC_KEYWORDS[theme]:
            for sub_name, sub_kws in TOPIC_KEYWORDS[theme]['subtopics'].items():
                if any(kw in text for kw in sub_kws):
                    subs.append(sub_name)
        result[theme] = subs[:3]
    return result


# ==================== 提取器 ====================

class MaterialExtractor:
    """素材提取器"""

    def __init__(self):
        self.stats = {'files': 0, 'quotes': 0, 'cases': 0, 'methods': 0, 'topics': 0, 'annotations': 0}
        self.all_quotes = defaultdict(list)  # theme -> [quote_dict, ...]
        self.all_cases = []
        self.all_methods = defaultdict(list)  # type -> [method_dict, ...]
        # 热点专题数据
        self.topic_articles = defaultdict(list)  # theme -> [article_info, ...]
        self.topic_quotes = defaultdict(list)    # theme -> [quote, ...]
        self.topic_cases = defaultdict(list)      # theme -> [case, ...]

    def process_file(self, filepath: Path):
        """处理单个文件"""
        try:
            content = filepath.read_text('utf-8')
        except Exception as e:
            print(f"  ⚠️ 读取失败: {filepath.name} - {e}")
            return

        meta = parse_frontmatter(content)
        body = get_body(content)
        title = meta.get('title', filepath.stem)
        date = str(meta.get('date', ''))
        section = meta.get('section_name', '')

        self.stats['files'] += 1

        # 分类文章主题
        themes = classify_theme(body + ' ' + title)
        theme_subtopics = classify_subtopics(body + ' ' + title, themes)

        # 记录文章到热点专题
        for theme in themes:
            self.topic_articles[theme].append({
                'title': title,
                'date': date,
                'section': section,
                'subtopics': theme_subtopics.get(theme, []),
                'source_file': str(filepath.relative_to(VAULT_PATH)),
            })
        self.stats['topics'] += len(themes)

        # 提取金句
        self._extract_quotes(body, title, date, section, filepath)
        # 提取案例
        self._extract_cases(body, title, date, section, filepath)
        # 提取写作方法
        self._extract_methods(body, title, date, section, filepath)

        # 金句和案例也同时按专题归档
        for theme in themes:
            for q in self.all_quotes.get(theme, []):
                if q not in self.topic_quotes[theme]:
                    self.topic_quotes[theme].append(q)
            for c in self.all_cases:
                if theme in c.get('themes', []) and c not in self.topic_cases[theme]:
                    self.topic_cases[theme].append(c)

    def _extract_quotes(self, body: str, title: str, date: str, section: str, filepath: Path):
        """提取金句"""
        paragraphs = split_paragraphs(body)
        seen = set()

        for para in paragraphs:
            for pattern in QUOTE_PATTERNS:
                matches = pattern.findall(para)
                for match in matches:
                    text = match.strip()
                    # 过滤：长度合理、不是标题、不重复
                    if len(text) < 10 or len(text) > 150:
                        continue
                    if text in seen:
                        continue
                    # 过滤掉纯数字或非中文为主的
                    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
                    if chinese_chars < 8:
                        continue

                    seen.add(text)
                    themes = classify_theme(text)
                    primary_theme = themes[0]

                    self.all_quotes[primary_theme].append({
                        'text': text,
                        'themes': themes,
                        'source_title': title,
                        'date': date,
                        'section': section,
                        'source_file': str(filepath.relative_to(VAULT_PATH)),
                    })
                    self.stats['quotes'] += 1

    def _extract_cases(self, body: str, title: str, date: str, section: str, filepath: Path):
        """提取事实案例（包含地名+数据的段落）"""
        paragraphs = split_paragraphs(body)

        for para in paragraphs:
            has_location = bool(re.search(r'(?:省|市|区|县|镇|村|自治区)', para))
            has_data = bool(re.search(r'\d+(?:\.\d+)?(?:%|亿|万|千|百|元|吨|亩|人|户|家|个|台|篇|件|项|条)', para))

            if has_location and has_data and len(para) > 30:
                # 提取地名
                location_match = re.search(r'(?:在)?([\u4e00-\u9fff]{2,8}(?:省|市|区|县|镇|村|自治区))', para)
                location = location_match.group(1) if location_match else ''

                # 提取关键数据
                data_matches = re.findall(r'\d+(?:\.\d+)?(?:%|亿|万|千|百|元|吨|亩|人|户|家|个|台|篇|件|项|条)', para)
                key_data = '、'.join(data_matches[:3])

                themes = classify_theme(para)

                # 截取合理长度
                summary = para[:200] + ('...' if len(para) > 200 else '')

                self.all_cases.append({
                    'summary': summary,
                    'location': location,
                    'key_data': key_data,
                    'themes': themes,
                    'source_title': title,
                    'date': date,
                    'section': section,
                    'source_file': str(filepath.relative_to(VAULT_PATH)),
                })
                self.stats['cases'] += 1

    def _extract_methods(self, body: str, title: str, date: str, section: str, filepath: Path):
        """提取写作方法"""
        # 检测文章结构（小标题模式）
        headings = re.findall(r'^##\s+(.+)$', body, re.MULTILINE)
        bold_headings = re.findall(r'^\*\*(.+?)\*\*$', body, re.MULTILINE)

        if len(headings) >= 2 or len(bold_headings) >= 2:
            structure_items = headings if headings else bold_headings
            structure_desc = ' → '.join(structure_items[:5])
            self.all_methods['起承转合'].append({
                'type': '文章结构',
                'description': f'本文采用分段式结构：{structure_desc}',
                'example': '',
                'source_title': title,
                'date': date,
                'source_file': str(filepath.relative_to(VAULT_PATH)),
            })
            self.stats['methods'] += 1

        # 检测排比句
        paragraphs = split_paragraphs(body)
        for para in paragraphs:
            # 模式：X的Y，X的Y，X的Y
            parallel = re.findall(r'([\u4e00-\u9fff]{2,6}(?:的|了|着|过)[\u4e00-\u9fff]{2,10}[，,]){2,}', para)
            if parallel:
                self.all_methods['排比句式'].append({
                    'type': '排比',
                    'description': '排比句式',
                    'example': para[:150] + ('...' if len(para) > 150 else ''),
                    'source_title': title,
                    'date': date,
                    'source_file': str(filepath.relative_to(VAULT_PATH)),
                })
                self.stats['methods'] += 1
                break  # 每篇最多一个排比示例

            # 模式：越...越...
            yue_pattern = re.findall(r'越[\u4e00-\u9fff]+越[\u4e00-\u9fff]+', para)
            if len(yue_pattern) >= 2:
                self.all_methods['排比句式'].append({
                    'type': '排比-递进',
                    'description': '越…越…递进排比',
                    'example': para[:150],
                    'source_title': title,
                    'date': date,
                    'source_file': str(filepath.relative_to(VAULT_PATH)),
                })
                self.stats['methods'] += 1
                break

    def save_results(self):
        """保存提取结果到 Obsidian"""
        # 1. 保存金句（按主题分文件）
        for theme, quotes in self.all_quotes.items():
            filepath = GOLDEN_QUOTES_DIR / f"{theme}-金句.md"
            lines = [
                f"---",
                f"type: golden_quote_collection",
                f"theme: \"{theme}\"",
                f"count: {len(quotes)}",
                f"updated: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                f"---\n",
                f"# {theme} · 金句集\n",
                f"> 共收录 {len(quotes)} 条金句，来源于人民日报 {min(q['date'] for q in quotes if q['date'])} ~ {max(q['date'] for q in quotes if q['date'])}\n",
            ]

            # 按日期倒序
            quotes.sort(key=lambda x: x['date'], reverse=True)

            for i, q in enumerate(quotes, 1):
                lines.append(f"## {i}. {q['date']}\n")
                lines.append(f"> {q['text']}\n")
                lines.append(f"- 📰 来源：[[{q['source_title']}]]")
                lines.append(f"- 📅 日期：{q['date']}　|　版面：{q['section']}")
                lines.append(f"- 🏷️ 主题：{'、'.join(q['themes'])}")
                lines.append("")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  📝 写入金句文件: {theme}-金句.md ({len(quotes)} 条)")

        # 2. 保存案例
        if self.all_cases:
            filepath = CASES_DIR / "案例汇总.md"
            lines = [
                f"---",
                f"type: case_collection",
                f"count: {len(self.all_cases)}",
                f"updated: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                f"---\n",
                f"# 事实案例汇总\n",
                f"> 共收录 {len(self.all_cases)} 个案例\n",
            ]

            self.all_cases.sort(key=lambda x: x['date'], reverse=True)

            for i, c in enumerate(self.all_cases, 1):
                lines.append(f"## {i}. {c['location']} ({c['date']})\n")
                lines.append(f"{c['summary']}\n")
                lines.append(f"- 📊 关键数据：{c['key_data']}")
                lines.append(f"- 📰 来源：[[{c['source_title']}]]")
                lines.append(f"- 🏷️ 适用主题：{'、'.join(c['themes'])}")
                lines.append("")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  📝 写入案例文件: 案例汇总.md ({len(self.all_cases)} 条)")

        # 3. 保存写作方法
        for method_type, methods in self.all_methods.items():
            filepath = WRITING_METHODS_DIR / f"{method_type}.md"
            lines = [
                f"---",
                f"type: writing_method_collection",
                f"method_type: \"{method_type}\"",
                f"count: {len(methods)}",
                f"updated: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                f"---\n",
                f"# {method_type} · 写作方法\n",
                f"> 共收录 {len(methods)} 个示例\n",
            ]

            for i, m in enumerate(methods, 1):
                lines.append(f"## {i}. {m['source_title']} ({m['date']})\n")
                lines.append(f"**类型**：{m['type']}\n")
                lines.append(f"**说明**：{m['description']}\n")
                if m.get('example'):
                    lines.append(f"> {m['example']}\n")
                lines.append(f"- 📰 来源：[[{m['source_title']}]]")
                lines.append("")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  📝 写入写作方法文件: {method_type}.md ({len(methods)} 条)")

        # 4. 保存热点专题
        self._save_topics()

    def _save_topics(self):
        """保存热点专题索引"""
        for theme, articles in self.topic_articles.items():
            if not articles:
                continue

            filepath = TOPICS_DIR / f"{theme}.md"

            # 统计子专题
            sub_counter = defaultdict(int)
            for a in articles:
                for s in a.get('subtopics', []):
                    sub_counter[s] += 1

            # 统计日期范围
            dates = [a['date'] for a in articles if a['date']]
            date_range = f"{min(dates)} ~ {max(dates)}" if dates else ''

            # 收集该主题下的金句（取前20条最佳）
            theme_quotes = self.topic_quotes.get(theme, [])[:20]
            # 收集该主题下的案例（取前15条）
            theme_cases = self.topic_cases.get(theme, [])[:15]

            lines = [
                f"---",
                f"type: hot_topic",
                f"theme: \"{theme}\"",
                f"article_count: {len(articles)}",
                f"quote_count: {len(self.topic_quotes.get(theme, []))}",
                f"case_count: {len(self.topic_cases.get(theme, []))}",
                f"updated: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                f"---\n",
                f"# 🔥 {theme} · 热点专题\n",
                f"> 收录 **{len(articles)}** 篇相关文章 | **{len(self.topic_quotes.get(theme, []))}** 条金句 | **{len(self.topic_cases.get(theme, []))}** 个案例",
                f"> 时间跨度：{date_range}\n",
            ]

            # 子专题标签
            if sub_counter:
                lines.append("## 📌 子专题\n")
                for sub, count in sorted(sub_counter.items(), key=lambda x: -x[1]):
                    lines.append(f"- **{sub}**（{count} 篇）")
                lines.append("")

            # 精选金句（前10条）
            if theme_quotes:
                lines.append("## 🏷️ 精选金句\n")
                for i, q in enumerate(theme_quotes[:10], 1):
                    lines.append(f"{i}. > {q['text']}")
                    lines.append(f"   — [[{q['source_title']}]] ({q['date']})")
                    lines.append("")
                if len(theme_quotes) > 10:
                    lines.append(f"*→ 更多金句见 [[{theme}-金句]]*\n")

            # 精选案例（前5条）
            if theme_cases:
                lines.append("## 📋 典型案例\n")
                for i, c in enumerate(theme_cases[:5], 1):
                    lines.append(f"### {i}. {c.get('location', '')} ({c['date']})\n")
                    lines.append(f"{c['summary']}\n")
                    lines.append(f"- 📊 关键数据：{c['key_data']}")
                    lines.append(f"- 📰 来源：[[{c['source_title']}]]")
                    lines.append("")
                if len(theme_cases) > 5:
                    lines.append(f"*→ 更多案例见 [[案例汇总]]*\n")

            # 相关文章列表（按日期倒序，最近20篇）
            lines.append("## 📰 相关文章\n")
            articles_sorted = sorted(articles, key=lambda x: x['date'], reverse=True)
            lines.append("| 日期 | 文章 | 版面 | 子专题 |")
            lines.append("|------|------|------|--------|")
            for a in articles_sorted[:30]:
                subs = '、'.join(a.get('subtopics', [])) if a.get('subtopics') else '-'
                lines.append(f"| {a['date']} | [[{a['title']}]] | {a['section']} | {subs} |")
            if len(articles_sorted) > 30:
                lines.append(f"\n*（仅显示最近30篇，共 {len(articles_sorted)} 篇）*")
            lines.append("")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  📝 写入热点专题: {theme}.md ({len(articles)} 篇文章)")


# ==================== 标注收集器 ====================

class AnnotationCollector:
    """收集人工 Callout 标注"""

    def __init__(self):
        self.annotations = defaultdict(list)  # category -> [annotation_dict, ...]
        self.highlights = []
        self.stats = {'files_with_annotations': 0, 'total_annotations': 0}

    def process_file(self, filepath: Path):
        """扫描单个文件的标注"""
        try:
            content = filepath.read_text('utf-8')
        except Exception:
            return

        meta = parse_frontmatter(content)
        title = meta.get('title', filepath.stem)
        date = str(meta.get('date', ''))

        found = False

        # 收集 Callout 标注
        for match in CALLOUT_PATTERN.finditer(content):
            callout_type = match.group(1)
            label = match.group(2).strip()
            body = match.group(3)
            # 去掉 Callout 行首的 "> "
            body_clean = re.sub(r'^> ?', '', body, flags=re.MULTILINE).strip()

            category = CALLOUT_TYPE_MAP.get(callout_type, '其他')

            self.annotations[category].append({
                'label': label,
                'content': body_clean,
                'source_title': title,
                'date': date,
                'source_file': str(filepath.relative_to(VAULT_PATH)),
            })
            self.stats['total_annotations'] += 1
            found = True

        # 收集高亮标注
        highlights = HIGHLIGHT_PATTERN.findall(content)
        for h in highlights:
            if len(h) >= 4:  # 至少4个字符的高亮才算有意义
                self.highlights.append({
                    'content': h,
                    'source_title': title,
                    'date': date,
                    'source_file': str(filepath.relative_to(VAULT_PATH)),
                })
                self.stats['total_annotations'] += 1
                found = True

        if found:
            self.stats['files_with_annotations'] += 1

    def save_results(self):
        """保存标注到文件"""
        if not self.annotations and not self.highlights:
            print("  ℹ️ 未找到任何人工标注")
            return

        for category, items in self.annotations.items():
            filepath = ANNOTATIONS_DIR / f"我的{category}.md"
            lines = [
                f"---",
                f"type: my_annotation",
                f"category: \"{category}\"",
                f"count: {len(items)}",
                f"updated: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                f"---\n",
                f"# 我的{category}标注\n",
                f"> 共 {len(items)} 条标注\n",
            ]

            for i, item in enumerate(items, 1):
                lines.append(f"## {i}. {item['source_title']} ({item['date']})\n")
                if item['label']:
                    lines.append(f"**标签**：{item['label']}\n")
                lines.append(f"{item['content']}\n")
                lines.append(f"- 📰 来源：[[{item['source_title']}]]")
                lines.append("")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  📝 写入标注文件: 我的{category}.md ({len(items)} 条)")

        if self.highlights:
            filepath = ANNOTATIONS_DIR / "我的高亮.md"
            lines = [
                f"---",
                f"type: my_highlights",
                f"count: {len(self.highlights)}",
                f"updated: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                f"---\n",
                f"# 我的高亮标注\n",
            ]
            for h in self.highlights:
                lines.append(f"- =={h['content']}== — [[{h['source_title']}]] ({h['date']})")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  📝 写入高亮文件: 我的高亮.md ({len(self.highlights)} 条)")


# ==================== 主函数 ====================

def find_articles(date_filter=None, limit=None) -> list:
    """查找文章文件"""
    articles = []
    for md_file in sorted(VAULT_PATH.rglob("*.md")):
        # 跳过素材库自身
        if "_素材库" in str(md_file):
            continue
        # 跳过 .obsidian
        if ".obsidian" in str(md_file):
            continue

        if date_filter:
            if date_filter not in str(md_file):
                continue

        articles.append(md_file)

    if limit:
        articles = articles[:limit]

    return articles


def main():
    parser = argparse.ArgumentParser(description='人民日报素材提取器')
    parser.add_argument('--date', help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, help='限制处理文章数')
    parser.add_argument('--collect-annotations', action='store_true',
                        help='仅收集人工标注')
    args = parser.parse_args()

    # 确保输出目录存在
    for d in [GOLDEN_QUOTES_DIR, CASES_DIR, WRITING_METHODS_DIR, TOPICS_DIR, ANNOTATIONS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    articles = find_articles(date_filter=args.date, limit=args.limit)

    if not articles:
        print("❌ 未找到任何文章")
        return

    print(f"\n{'='*60}")
    print(f"  📰 人民日报素材提取器 v1.0")
    print(f"{'='*60}")
    print(f"  📁 文章数量: {len(articles)}")
    print(f"  📂 输出目录: {OUTPUT_PATH}\n")

    if args.collect_annotations:
        # 仅收集人工标注
        print("  🔍 模式: 收集人工标注\n")
        collector = AnnotationCollector()
        for i, fp in enumerate(articles, 1):
            if i % 100 == 0:
                print(f"  处理进度: {i}/{len(articles)}...")
            collector.process_file(fp)

        print(f"\n  📊 扫描完成:")
        print(f"     有标注的文章: {collector.stats['files_with_annotations']} 篇")
        print(f"     标注总数: {collector.stats['total_annotations']} 条\n")

        collector.save_results()
    else:
        # AI 规则提取
        print("  🤖 模式: 规则提取（金句 + 案例 + 写作方法 + 热点专题）\n")
        extractor = MaterialExtractor()
        for i, fp in enumerate(articles, 1):
            if i % 100 == 0:
                print(f"  处理进度: {i}/{len(articles)}...")
            extractor.process_file(fp)

        print(f"\n  📊 提取完成:")
        print(f"     处理文章: {extractor.stats['files']} 篇")
        print(f"     金句: {extractor.stats['quotes']} 条")
        print(f"     案例: {extractor.stats['cases']} 个")
        print(f"     写作方法: {extractor.stats['methods']} 个")
        print(f"     热点专题: {len(extractor.topic_articles)} 个\n")

        extractor.save_results()

        # 同时收集人工标注
        print("\n  🔍 同时扫描人工标注...\n")
        collector = AnnotationCollector()
        for fp in articles:
            collector.process_file(fp)

        if collector.stats['total_annotations'] > 0:
            print(f"  📊 发现 {collector.stats['total_annotations']} 条人工标注\n")
            collector.save_results()
        else:
            print("  ℹ️ 暂未发现人工标注（你可以在文章中用 Callout 语法标注后重新运行）\n")

    print(f"\n{'='*60}")
    print(f"  ✅ 完成！请在 Obsidian 中查看 _素材库 文件夹")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
