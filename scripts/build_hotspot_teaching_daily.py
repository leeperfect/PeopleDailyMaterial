#!/usr/bin/env python3
"""Build the portable hotspot teaching-daily database and export bundle.

The three existing SQLite databases are treated as read-only fact sources:

* People App opinion articles discover and explain current hotspots.
* Curated hotspot topics provide the reviewed grouping and teaching angle.
* People's Daily newspaper articles provide policy, case and expression support.

This script writes only to ``data/hotspot_teaching``.  It deliberately keeps
generated teaching cards in ``editorial_preview`` until a later editorial
workflow marks them as reviewed or published.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
TOPIC_DB = ROOT / "data" / "peopleapp_opinion" / "core" / "hotspot_topics.sqlite"
APP_DB = ROOT / "data" / "peopleapp_opinion" / "core" / "articles.sqlite"
PAPER_DB = ROOT / "data" / "core" / "articles.sqlite"
OUTPUT_ROOT = ROOT / "data" / "hotspot_teaching"
OUTPUT_DB = OUTPUT_ROOT / "core" / "hotspot_teaching.sqlite"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
SITE_ROOT = OUTPUT_ROOT / "site"
WEB_ROOT = ROOT / "web" / "hotspot_teaching_daily"

PRIORITY_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3}
STATUS_ORDER = {"热点": 0, "候选": 1, "专题": 2}
SOURCE_KIND_APP = "peopleapp_opinion"
SOURCE_KIND_PAPER = "people_daily_newspaper"

STOPWORDS = {
    "治理", "问题", "发展", "推动", "加强", "中国", "人民日报", "评论", "热点",
    "社会", "公共", "服务", "建设", "工作", "时代", "当前", "进一步", "成为",
    "不能", "需要", "如何", "为何", "一个", "一种", "以及", "同时", "通过",
    "回归", "提升", "推进", "重点", "角度", "媒体", "文章", "青年", "文化",
}

CATEGORY_GUIDES = {
    "城市治理与公共服务": {
        "entry": "从群众身边的具体感受切入，观察公共服务如何在细节中体现治理能力。",
        "cause": "规则供给、执行协同和需求反馈之间仍可能存在脱节。",
        "impact": "既影响群众获得感，也检验基层治理的精细化和响应能力。",
        "measure": "以需求为起点完善规则、明确责任、畅通反馈，并用闭环监督推动落实。",
    },
    "数字治理与消费权益": {
        "entry": "从技术便利与权利保护的张力切入，讨论平台、监管和用户各自的责任。",
        "cause": "技术迭代快于规则完善，信息不对称与逐利冲动叠加放大风险。",
        "impact": "关系个人权益、市场信任，也影响数字经济长期健康发展。",
        "measure": "坚持技术向善，完善显著告知、授权边界、平台责任和常态监管。",
    },
    "教育与青年成长": {
        "entry": "从育人目标与现实焦虑的偏差切入，回到教育规律和青年真实需要。",
        "cause": "功利评价、流量逻辑和责任边界模糊容易让教育活动偏离本意。",
        "impact": "影响青年价值塑造、成长安全和教育公平。",
        "measure": "坚持育人为本，明确课程目标、组织责任和风险边界，形成家校社协同。",
    },
    "产业经济与开放发展": {
        "entry": "从一个产品或产业现象切入，分析创新、产业链与开放合作的关系。",
        "cause": "技术、人才、资本、市场和制度环境共同决定产业竞争力。",
        "impact": "关系发展质量、就业空间和产业链供应链韧性。",
        "measure": "以创新突破瓶颈，以实体经济夯实基础，以开放合作拓展发展空间。",
    },
    "网络生态与社会信任": {
        "entry": "从一次流量事件切入，讨论注意力经济如何影响公共信任。",
        "cause": "低成本造假、流量激励和平台把关不足形成逐利链条。",
        "impact": "透支社会善意，抬高信息辨别成本，并损害网络公共空间。",
        "measure": "压实平台责任、提高违法成本、强化事实核验，并提升公众媒介素养。",
    },
    "公共安全与监管": {
        "entry": "从风险暴露前后的治理差异切入，强调底线思维和源头预防。",
        "cause": "责任虚化、日常检查流于形式和信息传递不畅容易积累风险。",
        "impact": "直接关系群众生命财产安全和政府公信力。",
        "measure": "把风险识别、预警处置、责任追溯和公开回应连成治理闭环。",
    },
}

DEFAULT_GUIDE = {
    "entry": "从具体事件切入，追问现象背后的制度、责任与价值选择。",
    "cause": "现实需求、规则供给和执行能力之间存在需要弥合的落差。",
    "impact": "既影响个体感受，也反映公共治理和社会价值取向。",
    "measure": "坚持问题导向，明确责任边界，以制度、技术和社会协同形成长效机制。",
}

CATEGORY_DEEP_ANALYSIS = {
    "城市治理与公共服务": {
        "问题": "群众感受往往集中在收费、流程、设施和服务细节上，小问题背后反映的是治理是否精细、规则是否透明。",
        "原因": [
            "部门职责按条线划分，而群众需求具有综合性，容易出现多头管理、衔接不畅和问题空转。",
            "部分治理仍偏重建制度、做投入，缺少对实际使用率、满意度和问题解决率的持续评估。",
        ],
        "影响": [
            "如果高频小事长期得不到解决，会放大群众的不便感，并逐步消耗对公共服务的信任。",
            "服务差异还可能影响机会公平，使老年人、新就业群体等特定人群承担更高办事成本。",
        ],
        "对策": [
            "围绕群众办事和使用场景建立需求清单、责任清单、问题清单，明确牵头部门和办理时限。",
            "把满意度、实际使用率和闭环解决率纳入评价，形成发现问题、协同处置、反馈复盘的常态机制。",
        ],
    },
    "数字治理与消费权益": {
        "问题": "技术和商业模式快速进入生活场景，但显著告知、真实授权、退出机制和责任追溯没有同步跟上。",
        "原因": [
            "平台掌握技术、数据和规则优势，用户识别成本高、维权成本高，双方处于明显的信息不对称状态。",
            "流量、转化率和持续付费等商业激励容易压过权利保护，算法和界面设计可能被用于诱导选择。",
        ],
        "影响": [
            "个人信息、财产权益和人格权益可能受到侵害，消费者对数字产品的信任也会被持续透支。",
            "如果风险长期外溢，会抬高全社会交易成本，并削弱数字经济健康发展的社会基础。",
        ],
        "对策": [
            "落实最小必要、显著告知、单独同意和便捷退出，把知情权与选择权落实到具体操作界面。",
            "压实平台审核和算法治理责任，建立风险监测、投诉处置、证据留存与监管执法闭环。",
        ],
    },
    "教育与青年成长": {
        "问题": "教育活动容易被打卡、营销、排名和流量等外部目标带偏，课程目标、安全边界和育人责任被弱化。",
        "原因": [
            "学校、机构、家庭和平台之间责任分工不清，前期审核、过程监管和事后追责容易脱节。",
            "评价体系偏重短期成绩和可见成果，忽视真实学习效果、学生体验与长期成长。",
        ],
        "影响": [
            "不仅可能增加家庭焦虑和经济负担，还会影响青少年的价值塑造、成长安全与选择公平。",
            "商业包装替代教育内容，会侵蚀教育公信力，让真正有价值的课程和服务受到挤压。",
        ],
        "对策": [
            "建立课程目标、风险事项和组织责任三张清单，把教育价值和安全评估放在活动审批之前。",
            "加强对承办机构、营销宣传和收费项目的审核，形成学校、家庭、社会和监管部门协同机制。",
        ],
    },
    "产业经济与开放发展": {
        "问题": "热点表面是产品、企业或市场现象，实质反映创新能力、产业链韧性和国际竞争规则的变化。",
        "原因": [
            "技术积累、人才供给、市场规模、产业配套和制度环境共同作用，任何单一优势都难以长期支撑竞争力。",
            "外部市场波动、贸易壁垒和规则差异增加了企业出海成本，也暴露部分产业关键环节的短板。",
        ],
        "影响": [
            "产业竞争力直接关系就业、投资和发展预期，也影响产业链供应链的安全稳定。",
            "企业出海表现还会影响国际社会对中国制造、中国创新和中国市场的整体认知。",
        ],
        "对策": [
            "坚持以技术创新提升产品质量和附加值，同时补齐标准、品牌、服务与合规能力。",
            "完善企业公共服务和风险预警，支持产业链协同创新，以高水平开放拓展合作空间。",
        ],
    },
    "网络生态与社会信任": {
        "问题": "虚假摆拍、卖惨营销和低质内容借助算法扩散，把公共情绪和社会善意转化为流量收益。",
        "原因": [
            "造假成本低、流量变现快，而平台识别、事实核验和责任追究存在时间差。",
            "推荐机制偏好强刺激内容，部分创作者和机构在逐利驱动下不断突破真实性与伦理边界。",
        ],
        "影响": [
            "虚假内容会透支公众同情心、增加信息辨别成本，并损害真实求助和专业内容的传播。",
            "长期放任还会造成劣币驱逐良币，削弱平台公信力和网络公共空间的讨论质量。",
        ],
        "对策": [
            "压实账号、机构和平台的分层责任，对恶意造假、组织摆拍和违规获利实施联动惩戒。",
            "完善事实核验、风险提示和申诉纠错机制，同时提升公众媒介素养和证据意识。",
        ],
    },
    "公共安全与监管": {
        "问题": "安全风险往往不是突然出现，而是在日常检查、隐患整改、信息报告和责任落实中逐步积累。",
        "原因": [
            "责任主体存在侥幸心理，检查容易重留痕轻实效，基层风险识别和专业处置能力仍有短板。",
            "跨部门信息共享、预警发布和应急联动不够顺畅，容易错过风险处置的最佳窗口。",
        ],
        "影响": [
            "一旦风险转化为事故，将直接威胁群众生命财产安全，并对政府公信力造成持续影响。",
            "谣言和信息不透明还可能放大社会恐慌，干扰正常抢险救援和公共秩序。",
        ],
        "对策": [
            "坚持关口前移，围绕重点区域、重点设施和重点人群开展常态排查、动态监测和分级预警。",
            "明确属地、部门和经营主体责任，打通预警、处置、公开回应、复盘整改和责任追溯链条。",
        ],
    },
    "体育文化与社会心态": {
        "问题": "体育热点不只是胜负新闻，也折射规则意识、拼搏精神、文化交流和社会情绪表达。",
        "原因": [
            "竞技成绩容易成为舆论唯一标尺，商业传播和情绪化表达可能遮蔽体育的教育与文化价值。",
            "人才培养、赛事体系和基层参与之间衔接不足，使短期成绩焦虑替代长期能力建设。",
        ],
        "影响": [
            "健康的体育叙事能够凝聚社会情感、塑造青年品格，并促进不同文化之间的理解。",
            "过度功利化和饭圈化则可能制造对立，偏离尊重规则、尊重对手和超越自我的体育精神。",
        ],
        "对策": [
            "完善青训、赛事和群众体育体系，把长期人才培养与广泛社会参与结合起来。",
            "引导媒体和平台呈现多元体育价值，减少唯金牌、唯流量评价，形成理性包容的观赛文化。",
        ],
    },
    "国际观察与中国叙事": {
        "问题": "国际议题中事实、立场和叙事相互交织，片面标签和话语偏见容易遮蔽真实利益关系。",
        "原因": [
            "不同国家的发展阶段、战略利益和媒体框架存在差异，对同一事件往往形成不同解释。",
            "国际传播中信息不对称和议题设置能力不足，可能使中国实践被简化、误读甚至污名化。",
        ],
        "影响": [
            "错误叙事会影响国际社会对中国发展道路、合作倡议和全球贡献的判断。",
            "外部认知偏差也可能传导至经贸、人文和安全领域，增加沟通与合作成本。",
        ],
        "对策": [
            "坚持事实和数据支撑，用具体案例说明中国发展给世界带来的合作机会与公共产品。",
            "提升国际表达的对象感和分众化水平，既主动回应误读，也善于寻找共同利益和共同价值。",
        ],
    },
}

DEFAULT_DEEP_ANALYSIS = {
    "问题": "个别新闻现象背后通常同时存在规则供给、责任落实和价值判断问题，需要避免只看表面。",
    "原因": [
        "现实需求变化较快，而制度完善、执行协同和社会认知存在一定滞后。",
        "责任边界不够清晰，发现问题、处置问题和反馈结果之间尚未形成稳定闭环。",
    ],
    "影响": [
        "问题既影响当事人的直接感受，也可能外溢为公共信任和社会预期问题。",
        "如果长期得不到回应，个案可能演变为同类问题，进一步增加治理成本。",
    ],
    "对策": [
        "坚持问题导向和系统治理，明确主体责任、协同责任与监督责任。",
        "完善规则、执行、公开、反馈和评估机制，让治理措施可操作、可检查、可持续。",
    ],
}

# Distinctive phrases used only for the newspaper-support recall step.  They
# intentionally prefer false negatives over false positives: a hotspot may
# have no People's Daily support, but an unrelated article must never be added
# merely because it contains a broad word such as “治理” or “青年”.
TOPIC_STRONG_ANCHORS = {
    "AI应用风险与智能向善治理": ["智能向善", "AI研学", "AI荐股", "AI测评", "人工智能大考", "人工智能教育"],
    "AI深度合成与人格权保护": ["人格权", "换脸拟声", "声音保护", "深度合成", "AI生成"],
    "世界杯中的体育精神与人文价值": ["世界杯", "中国足球", "小国弱旅"],
    "中国制造出海与创新竞争力": ["中国制造", "避暑产品", "走俏海外", "产业链自主可控", "制造出海"],
    "停车计费规则透明化": ["停车收费", "停车计费", "向上取整", "停车费"],
    "儿童网络保护与童年流量化治理": ["伪童书", "儿童网络保护", "算法投喂", "童年流量", "孩子不是流量", "少儿阅读"],
    "历史正义与日本军事化警示": ["日本军国主义", "军事化", "历史正义", "军国主义", "慰安妇"],
    "开屏广告与数字界面减负": ["开屏广告", "广告跳转", "摇一摇广告", "APP广告"],
    "录取通知书回归育人本意": ["录取通知书"],
    "教师减负落地": ["教师减负", "进校园事项", "非教学任务"],
    "文化遗产传承与公共创意边界": ["文化遗产", "传统纹样", "创意边界", "表情包确权"],
    "新就业群体服务驿站提质": ["新就业群体", "服务驿站", "新就业形态劳动者"],
    "正确政绩观与主动治理": ["政绩观", "为民造福", "实事求是", "真抓实干"],
    "流量逐利与虚假内容治理": ["博流量", "虚假内容", "卖惨营销", "摆拍", "流量祛魅"],
    "灭火器纸面维保治理": ["灭火器", "消防维保", "纸面维保"],
    "理解中国发展与世界机遇": ["中国机遇", "读懂中国", "制度密码", "中国叙事"],
    "研学回归教育与安全本位": ["研学", "只游不学", "研学游"],
    "粮食安全与农业现代化": ["粮食安全", "粮食丰收", "农业现代化", "现代化大产业"],
    "自动续费与隐性扣款治理": ["自动续费", "隐性扣款", "取消续费", "退订"],
    "营商环境与市场秩序": ["营商环境", "涉企检查", "市场退出", "涉企执法"],
    "诋毁袁隆平与无底线流量": ["袁隆平", "袁老", "农业科普"],
    "银发群体数字融入": ["数字适老化", "银发力量", "老年教育", "银发群体", "公共交通更适老"],
    "防汛救灾与涉灾谣言治理": ["防汛", "防灾减灾", "涉灾谣言", "抢险救援"],
    "高考志愿填报治理": ["志愿填报", "高考志愿", "招生诈骗"],
}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"原标题[:：]?", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clip(value: Any, limit: int = 160) -> str:
    text = clean_text(value)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def split_sentences(value: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；])|\n+", clean_text(value))
    return [clean_text(part) for part in parts if 12 <= len(clean_text(part)) <= 180]


def connect_ro(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(f"缺少事实库：{path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def connect_output(path: Path | None = None) -> sqlite3.Connection:
    path = path or OUTPUT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS hotspot_topics (
            topic_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            category TEXT NOT NULL,
            angle TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            media_count INTEGER NOT NULL,
            app_article_count INTEGER NOT NULL,
            paper_support_count INTEGER NOT NULL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            sources_json TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'source_curated',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_articles (
            article_id TEXT PRIMARY KEY,
            source_kind TEXT NOT NULL,
            source_name TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT,
            section_name TEXT,
            category TEXT,
            author TEXT,
            source_url TEXT,
            summary TEXT,
            content_hash TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS topic_article_links (
            topic_id TEXT NOT NULL,
            article_id TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            relation_role TEXT NOT NULL,
            confidence REAL NOT NULL,
            match_reason TEXT NOT NULL,
            reviewed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            PRIMARY KEY(topic_id, article_id),
            FOREIGN KEY(topic_id) REFERENCES hotspot_topics(topic_id) ON DELETE CASCADE,
            FOREIGN KEY(article_id) REFERENCES source_articles(article_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS teaching_cards (
            card_id TEXT PRIMARY KEY,
            topic_id TEXT NOT NULL UNIQUE,
            version INTEGER NOT NULL DEFAULT 1,
            quick_intro TEXT NOT NULL,
            news_overview TEXT NOT NULL DEFAULT '',
            worth_teaching TEXT NOT NULL,
            key_facts_json TEXT NOT NULL,
            core_judgments_json TEXT NOT NULL,
            classroom_entry TEXT NOT NULL,
            background_json TEXT NOT NULL,
            controversy TEXT NOT NULL,
            media_viewpoints_json TEXT NOT NULL,
            paper_support_json TEXT NOT NULL,
            analysis_framework_json TEXT NOT NULL,
            standard_expressions_json TEXT NOT NULL,
            cases_json TEXT NOT NULL,
            common_mistakes_json TEXT NOT NULL,
            classroom_questions_json TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'editorial_preview',
            review_note TEXT NOT NULL DEFAULT '',
            published_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(topic_id) REFERENCES hotspot_topics(topic_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS daily_editions (
            edition_id TEXT PRIMARY KEY,
            edition_date TEXT NOT NULL UNIQUE,
            issue_no INTEGER NOT NULL,
            title TEXT NOT NULL,
            teaching_judgment TEXT NOT NULL,
            topic_ids_json TEXT NOT NULL,
            app_article_count INTEGER NOT NULL,
            paper_article_count INTEGER NOT NULL,
            reading_minutes INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS weekly_editions (
            edition_id TEXT PRIMARY KEY,
            week_start TEXT NOT NULL UNIQUE,
            week_end TEXT NOT NULL,
            title TEXT NOT NULL,
            teaching_judgment TEXT NOT NULL,
            topic_ids_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS question_links (
            topic_id TEXT NOT NULL,
            stable_question_id TEXT NOT NULL,
            relevance_score REAL NOT NULL,
            rationale TEXT NOT NULL,
            visible INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            PRIMARY KEY(topic_id, stable_question_id)
        );

        CREATE INDEX IF NOT EXISTS idx_sources_kind_date ON source_articles(source_kind, date);
        CREATE INDEX IF NOT EXISTS idx_links_topic_kind ON topic_article_links(topic_id, source_kind);
        CREATE INDEX IF NOT EXISTS idx_topics_end_priority ON hotspot_topics(end_date, priority);
        CREATE INDEX IF NOT EXISTS idx_cards_status ON teaching_cards(review_status);
        """
    )
    card_columns = {row[1] for row in conn.execute("PRAGMA table_info(teaching_cards)")}
    if "news_overview" not in card_columns:
        conn.execute("ALTER TABLE teaching_cards ADD COLUMN news_overview TEXT NOT NULL DEFAULT ''")
    conn.commit()


def load_topics() -> list[dict[str, Any]]:
    topic_conn = connect_ro(TOPIC_DB)
    try:
        topics = [dict(row) for row in topic_conn.execute("SELECT * FROM hotspot_topics")]
        links = [dict(row) for row in topic_conn.execute(
            "SELECT * FROM hotspot_topic_articles ORDER BY date, source_name, title"
        )]
    finally:
        topic_conn.close()

    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in links:
        by_topic[row["topic_id"]].append(row)
    for topic in topics:
        topic["app_articles"] = by_topic.get(topic["topic_id"], [])
        topic["sources"] = json_loads(topic.get("sources_json"), [])
    topics.sort(
        key=lambda item: (
            STATUS_ORDER.get(item.get("status", ""), 9),
            PRIORITY_ORDER.get(item.get("priority", ""), 9),
            -int(item.get("media_count") or 0),
            -int(item.get("article_count") or 0),
            item.get("topic", ""),
        )
    )
    return topics


def load_app_articles(article_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    if not article_ids:
        return {}
    conn = connect_ro(APP_DB)
    try:
        placeholders = ",".join("?" for _ in article_ids)
        rows = conn.execute(
            f"""
            SELECT a.*, COALESCE(m.source_name, a.source) AS source_name
            FROM articles a
            LEFT JOIN peopleapp_opinion_meta m ON m.article_id = a.article_id
            WHERE a.article_id IN ({placeholders})
            """,
            list(article_ids),
        ).fetchall()
        return {row["article_id"]: dict(row) for row in rows}
    finally:
        conn.close()


def load_paper_articles() -> list[dict[str, Any]]:
    conn = connect_ro(PAPER_DB)
    try:
        rows = conn.execute(
            """
            SELECT article_id, source, source_url, title, author, date, section_name,
                   category, summary, content, content_hash, updated_at
            FROM articles
            WHERE length(content) >= 200
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def keyword_candidates(topic: dict[str, Any]) -> list[str]:
    text = " ".join(
        [topic.get("topic", ""), topic.get("angle", "")]
        + [article.get("title", "") for article in topic.get("app_articles", [])]
    )
    tokens: list[str] = []
    try:
        import jieba.analyse  # type: ignore

        tokens.extend(jieba.analyse.extract_tags(text, topK=24, withWeight=False))
    except Exception:
        tokens.extend(re.findall(r"[\u4e00-\u9fff]{2,8}", text))

    topic_text = clean_text(topic.get("topic"))
    tokens.extend(re.findall(r"[\u4e00-\u9fff]{2,6}", topic_text))
    for article in topic.get("app_articles", []):
        tokens.extend(re.findall(r"[\u4e00-\u9fff]{2,6}", clean_text(article.get("title"))))

    result: list[str] = []
    for token in tokens:
        token = clean_text(token)
        if len(token) < 2 or token in STOPWORDS or token.isdigit():
            continue
        if token not in result:
            result.append(token)
    return result[:20]


def normalized_title(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"（[^）]{0,30}）|\([^)]{0,30}\)", "", text)
    text = re.sub(
        r"^(人民日报|人民时评|人民论坛|人民日报刊文|评论员观察|经济热点快评)[:：]",
        "",
        text,
    )
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", text).lower()


def directly_related_to_app_title(topic: dict[str, Any], paper_title: str) -> bool:
    target = normalized_title(paper_title)
    if len(target) < 6:
        return False
    for item in topic.get("app_articles", []):
        app_title = normalized_title(item.get("title"))
        if len(app_title) < 6:
            continue
        if target in app_title or app_title in target:
            return True
        target_parts = {target[index : index + 3] for index in range(len(target) - 2)}
        app_parts = {app_title[index : index + 3] for index in range(len(app_title) - 2)}
        union = target_parts | app_parts
        if union and len(target_parts & app_parts) / len(union) >= 0.52:
            return True
    return False


def date_distance(article_date: str, topic_end: str) -> int:
    try:
        return abs((date.fromisoformat(article_date) - date.fromisoformat(topic_end)).days)
    except ValueError:
        return 9999


def score_paper_article(
    topic: dict[str, Any], article: dict[str, Any], keywords: Sequence[str]
) -> tuple[float, list[str]]:
    title = clean_text(article.get("title"))
    summary = clean_text(article.get("summary"))
    content = clean_text(article.get("content"))[:5000]
    strong_anchors = TOPIC_STRONG_ANCHORS.get(topic.get("topic", ""), [])
    strong_title_hits = [word for word in strong_anchors if word.lower() in title.lower()]
    strong_summary_hits = [word for word in strong_anchors if word.lower() in summary.lower()]
    direct_title_match = directly_related_to_app_title(topic, title)

    # A paper article must be anchored by its title.  Summary/content matches
    # can strengthen the explanation but cannot create a relation by themselves.
    if not direct_title_match and not strong_title_hits:
        return 0.0, []
    if not direct_title_match and all(len(word) <= 3 for word in strong_title_hits) and len(strong_title_hits) < 2:
        return 0.0, []

    title_hits = [word for word in keywords if word in title]
    summary_hits = [word for word in keywords if word in summary]
    content_hits = [word for word in keywords if word in content]
    score = 12.0 if direct_title_match else 0.0
    score += sum(7.0 if len(word) >= 4 else 3.5 for word in strong_title_hits)
    score += min(len(strong_summary_hits), 2) * 0.7
    score += min(len(title_hits), 3) * 0.6
    score += min(len(summary_hits), 3) * 0.25
    score += min(len(content_hits), 3) * 0.1
    distance = date_distance(article.get("date", ""), topic.get("end_date", ""))
    if distance <= 30:
        score += 1.8
    elif distance <= 90:
        score += 0.8
    elif distance > 240:
        score -= 1.0
    if article.get("section_name") in {"评论", "理论", "要闻", "政治", "社会", "法治", "经济"}:
        score += 0.4

    distinct = list(dict.fromkeys(strong_title_hits + strong_summary_hits + title_hits + summary_hits))
    return round(score, 2), distinct[:6]


def relation_role(article: dict[str, Any]) -> str:
    title = clean_text(article.get("title"))
    section = clean_text(article.get("section_name"))
    if any(word in title for word in ("条例", "规定", "规划", "意见", "办法", "法治", "制度")):
        return "政策依据"
    if any(word in title for word in ("调查", "探访", "一线", "故事", "观察", "实践", "经验")):
        return "治理案例"
    if section in {"评论", "理论"} or any(
        word in title for word in ("人民时评", "人民论坛", "评论员", "微观察", "大家谈")
    ):
        return "规范表达"
    return "延伸母题"


def match_paper_support(
    topic: dict[str, Any], paper_articles: Sequence[dict[str, Any]], limit: int = 5
) -> list[dict[str, Any]]:
    keywords = keyword_candidates(topic)
    candidates: list[tuple[float, dict[str, Any], list[str]]] = []
    for article in paper_articles:
        score, hits = score_paper_article(topic, article, keywords)
        if score >= 7.0:
            candidates.append((score, article, hits))
    candidates.sort(key=lambda item: (-item[0], item[1].get("date", ""), item[1].get("title", "")))

    result: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for score, article, hits in candidates:
        normalized_title = re.sub(r"\s+", "", clean_text(article.get("title")))
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)
        support = dict(article)
        support["confidence"] = min(round(score / 20, 2), 0.98)
        support["match_reason"] = "主题关键词相符：" + "、".join(hits[:4])
        support["relation_role"] = relation_role(article)
        result.append(support)
        if len(result) >= limit:
            break
    return result


def article_summary(article: dict[str, Any]) -> str:
    summary = clean_text(article.get("summary"))
    if summary:
        return clip(summary, 150)
    sentences = split_sentences(article.get("content", ""))
    return clip(sentences[0], 150) if sentences else ""


def build_key_facts(app_articles: Sequence[dict[str, Any]]) -> list[str]:
    facts: list[str] = []
    for article in sorted(app_articles, key=lambda item: item.get("date", ""), reverse=True):
        source = article.get("source_name") or article.get("source") or "人民日报 APP"
        summary = article_summary(article)
        if summary:
            facts.append(f"{article.get('date', '')}，{source}关注《{article.get('title', '')}》：{summary}")
        else:
            facts.append(f"{article.get('date', '')}，{source}围绕《{article.get('title', '')}》发表评论。")
        if len(facts) == 3:
            break
    return facts


def build_media_viewpoints(app_articles: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    viewpoints: list[dict[str, str]] = []
    seen_sources: set[str] = set()
    for article in sorted(app_articles, key=lambda item: item.get("date", ""), reverse=True):
        source = clean_text(article.get("source_name") or article.get("source") or "人民日报 APP")
        if source in seen_sources and len(seen_sources) >= 3:
            continue
        seen_sources.add(source)
        viewpoints.append(
            {
                "article_id": article.get("article_id", ""),
                "source": source,
                "title": clean_text(article.get("title")),
                "viewpoint": article_summary(article) or "该文章从事件本身出发提出观察与评论。",
                "date": article.get("date", ""),
                "url": article.get("source_url", ""),
            }
        )
        if len(viewpoints) == 6:
            break
    return viewpoints


def build_news_overview(topic: dict[str, Any], app_articles: list[dict[str, Any]]) -> str:
    """Create a source-bounded introduction of roughly 300 Chinese characters."""
    guide = CATEGORY_GUIDES.get(topic.get("category"), DEFAULT_GUIDE)
    angle = clean_text(topic.get("angle")).rstrip("。！？；")
    representatives: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for article in sorted(app_articles, key=lambda row: row.get("date", ""), reverse=True):
        source = clean_text(article.get("source_name") or article.get("source") or "人民日报APP")
        if source in seen_sources and len(representatives) < 2:
            continue
        seen_sources.add(source)
        representatives.append(article)
        if len(representatives) == 2:
            break
    if len(representatives) < 2:
        for article in sorted(app_articles, key=lambda row: row.get("date", ""), reverse=True):
            if article not in representatives:
                representatives.append(article)
            if len(representatives) == 2:
                break

    reports = "；".join(
        f"{clean_text(item.get('source_name') or item.get('source') or '人民日报APP')}围绕"
        f"《{clip(item.get('title'), 30)}》展开评论"
        for item in representatives
    )
    if not reports:
        reports = "已收录评论围绕事件经过、社会影响和治理责任展开讨论"

    return (
        f"“{clean_text(topic.get('topic'))}”是{topic.get('start_date', '')}至{topic.get('end_date', '')}期间形成的热点议题。"
        f"本地人民日报APP评论库共归集{topic.get('article_count', 0)}篇相关文章，涉及"
        f"{topic.get('media_count', 0)}家媒体。已收录报道的主要内容包括：{reports}。"
        f"综合这些材料，新闻关注点可以概括为：{angle}。"
        f"讨论并不只停留在个别现象本身，还涉及{guide['cause'].rstrip('。！？；')}。"
        f"由此带来的影响是，{guide['impact'].rstrip('。！？；')}。"
        "理解这一热点，需要区分已经发生的事实、媒体提出的判断和后续治理主张。"
    )


def build_detailed_analysis(
    topic: dict[str, Any],
    app_articles: list[dict[str, Any]],
) -> dict[str, list[str]]:
    guide = CATEGORY_GUIDES.get(topic.get("category"), DEFAULT_GUIDE)
    detail = CATEGORY_DEEP_ANALYSIS.get(topic.get("category"), DEFAULT_DEEP_ANALYSIS)
    angle = clean_text(topic.get("angle")).rstrip("。！？；")
    titles = list(
        dict.fromkeys(
            clean_text(article.get("title"))
            for article in sorted(app_articles, key=lambda row: row.get("date", ""), reverse=True)
            if clean_text(article.get("title"))
        )
    )[:2]
    evidence = (
        f"从{'、'.join(f'《{clip(title, 26)}》' for title in titles)}等报道可以看出，"
        "该热点已经由个别新闻现象延伸为责任边界、规则供给和执行效果的综合议题。"
        if titles else
        "从多家媒体的连续评论可以看出，该热点已经由个别现象延伸为责任、规则与执行问题。"
    )
    return {
        "问题": [
            angle or f"围绕“{topic.get('topic', '')}”，需要先识别新闻现象背后的公共问题。",
            detail["问题"],
            evidence,
        ],
        "原因": [
            guide["cause"].rstrip("。！？；"),
            *detail["原因"],
        ],
        "影响": [
            guide["impact"].rstrip("。！？；"),
            *detail["影响"],
        ],
        "对策": [
            guide["measure"].rstrip("。！？；"),
            *detail["对策"],
        ],
    }


def build_card(topic: dict[str, Any], app_articles: list[dict[str, Any]], supports: list[dict[str, Any]]) -> dict[str, Any]:
    guide = CATEGORY_GUIDES.get(topic.get("category"), DEFAULT_GUIDE)
    angle = clean_text(topic.get("angle"))
    key_facts = build_key_facts(app_articles)
    media_viewpoints = build_media_viewpoints(app_articles)
    detailed_analysis = build_detailed_analysis(topic, app_articles)
    paper_support = [
        {
            "article_id": item.get("article_id", ""),
            "title": clean_text(item.get("title")),
            "date": item.get("date", ""),
            "section": item.get("section_name", ""),
            "role": item.get("relation_role", "延伸母题"),
            "reason": item.get("match_reason", ""),
            "summary": article_summary(item),
            "url": item.get("source_url", ""),
            "confidence": item.get("confidence", 0),
        }
        for item in supports
    ]
    timeline = [
        {
            "date": item.get("date", ""),
            "source": item.get("source_name") or item.get("source") or "人民日报 APP",
            "title": clean_text(item.get("title")),
        }
        for item in sorted(app_articles, key=lambda row: row.get("date", ""))[-8:]
    ]
    standard_expressions = [
        angle,
        guide["impact"],
        guide["measure"],
        "治理既要回应当下问题，也要通过制度建设稳定社会预期，把群众感受作为检验成效的重要标尺。",
    ]
    tags = [topic.get("category", ""), topic.get("status", ""), f"{topic.get('priority', '')}级"]
    tags.extend(keyword_candidates(topic)[:5])

    return {
        "card_id": f"card_{topic['topic_id']}",
        "topic_id": topic["topic_id"],
        "quick_intro": angle or f"多家媒体集中关注“{topic['topic']}”，值得从治理责任与公共价值角度展开。",
        "news_overview": build_news_overview(topic, app_articles),
        "worth_teaching": (
            f"该话题在{topic.get('start_date', '')}至{topic.get('end_date', '')}之间，"
            f"已有{topic.get('media_count', 0)}家媒体、{topic.get('article_count', 0)}篇评论形成观点链，"
            "既有现实热度，也便于训练从现象走向制度分析的能力。"
        ),
        "key_facts": key_facts,
        "core_judgments": [angle, guide["impact"], guide["measure"]],
        "classroom_entry": guide["entry"],
        "background": timeline,
        "controversy": f"课堂上可重点讨论：围绕“{topic['topic']}”，现实便利、社会期待与治理责任之间应如何取得平衡？",
        "media_viewpoints": media_viewpoints,
        "paper_support": paper_support,
        "analysis_framework": detailed_analysis,
        "standard_expressions": [item for item in standard_expressions if item],
        "cases": {
            "正面案例": paper_support[:2],
            "反面警示": media_viewpoints[:2],
        },
        "common_mistakes": [
            "只复述新闻经过，没有提炼公共问题。",
            "只强调单一主体责任，没有分析制度、平台与社会协同。",
            "提出口号式对策，缺少规则、执行、监督和反馈闭环。",
        ],
        "classroom_questions": [
            f"如果把“{topic['topic']}”作为综合分析题，你会先界定哪个核心矛盾？",
            "不同媒体的关注角度有哪些共同点，又有哪些差异？",
            "怎样把对策从原则表态转化为可执行的责任链条？",
        ],
        "tags": list(dict.fromkeys(tag for tag in tags if tag)),
    }


def source_record(article: dict[str, Any], source_kind: str) -> tuple[Any, ...]:
    return (
        article.get("article_id", ""),
        source_kind,
        article.get("source_name") or article.get("source") or ("人民日报" if source_kind == SOURCE_KIND_PAPER else "人民日报 APP"),
        clean_text(article.get("title")),
        article.get("date", ""),
        article.get("section_name", ""),
        article.get("category", ""),
        article.get("author", ""),
        article.get("source_url", ""),
        article_summary(article),
        article.get("content_hash", ""),
        datetime.now().isoformat(timespec="seconds"),
    )


def upsert_source(conn: sqlite3.Connection, article: dict[str, Any], source_kind: str) -> None:
    conn.execute(
        """
        INSERT INTO source_articles(
            article_id, source_kind, source_name, title, date, section_name,
            category, author, source_url, summary, content_hash, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(article_id) DO UPDATE SET
            source_kind=excluded.source_kind,
            source_name=excluded.source_name,
            title=excluded.title,
            date=excluded.date,
            section_name=excluded.section_name,
            category=excluded.category,
            author=excluded.author,
            source_url=excluded.source_url,
            summary=excluded.summary,
            content_hash=excluded.content_hash,
            updated_at=excluded.updated_at
        """,
        source_record(article, source_kind),
    )


def refresh_database(topics: list[dict[str, Any]], paper_articles: list[dict[str, Any]]) -> dict[str, int]:
    conn = connect_output()
    now = datetime.now().isoformat(timespec="seconds")
    all_app_ids = [
        link.get("article_id", "")
        for topic in topics
        for link in topic.get("app_articles", [])
        if link.get("article_id")
    ]
    app_by_id = load_app_articles(all_app_ids)
    existing_cards = {
        row["topic_id"]: dict(row)
        for row in conn.execute("SELECT * FROM teaching_cards")
    }

    active_topic_ids: list[str] = []
    conn.execute("DELETE FROM topic_article_links")
    for topic in topics:
        active_topic_ids.append(topic["topic_id"])
        app_articles = [
            app_by_id.get(link["article_id"], link)
            for link in topic.get("app_articles", [])
        ]
        supports = match_paper_support(topic, paper_articles)
        conn.execute(
            """
            INSERT INTO hotspot_topics(
                topic_id, topic, category, angle, status, priority, media_count,
                app_article_count, paper_support_count, start_date, end_date,
                sources_json, review_status, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(topic_id) DO UPDATE SET
                topic=excluded.topic,
                category=excluded.category,
                angle=excluded.angle,
                status=excluded.status,
                priority=excluded.priority,
                media_count=excluded.media_count,
                app_article_count=excluded.app_article_count,
                paper_support_count=excluded.paper_support_count,
                start_date=excluded.start_date,
                end_date=excluded.end_date,
                sources_json=excluded.sources_json,
                updated_at=excluded.updated_at
            """,
            (
                topic["topic_id"], topic.get("topic", ""), topic.get("category", ""),
                topic.get("angle", ""), topic.get("status", ""), topic.get("priority", ""),
                int(topic.get("media_count") or 0), len(app_articles), len(supports),
                topic.get("start_date", ""), topic.get("end_date", ""),
                json_dumps(topic.get("sources", [])), "source_curated",
                topic.get("created_at") or now, now,
            ),
        )

        for article in app_articles:
            upsert_source(conn, article, SOURCE_KIND_APP)
            conn.execute(
                """
                INSERT INTO topic_article_links(
                    topic_id, article_id, source_kind, relation_role,
                    confidence, match_reason, reviewed, created_at
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    topic["topic_id"], article.get("article_id", ""), SOURCE_KIND_APP,
                    "媒体观点", 1.0, "来自人工复核后的APP评论热点归并", 1, now,
                ),
            )
        for article in supports:
            upsert_source(conn, article, SOURCE_KIND_PAPER)
            conn.execute(
                """
                INSERT INTO topic_article_links(
                    topic_id, article_id, source_kind, relation_role,
                    confidence, match_reason, reviewed, created_at
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    topic["topic_id"], article.get("article_id", ""), SOURCE_KIND_PAPER,
                    article.get("relation_role", "延伸母题"), article.get("confidence", 0),
                    article.get("match_reason", ""), 0, now,
                ),
            )

        card = build_card(topic, app_articles, supports)
        old = existing_cards.get(topic["topic_id"])
        preserve_reviewed = old and old.get("review_status") in {"reviewed", "published"}
        if preserve_reviewed:
            continue
        created_at = old.get("created_at") if old else now
        version = int(old.get("version") or 1) if old else 1
        conn.execute(
            """
            INSERT INTO teaching_cards(
                card_id, topic_id, version, quick_intro, news_overview, worth_teaching,
                key_facts_json, core_judgments_json, classroom_entry,
                background_json, controversy, media_viewpoints_json,
                paper_support_json, analysis_framework_json,
                standard_expressions_json, cases_json, common_mistakes_json,
                classroom_questions_json, tags_json, review_status, review_note,
                published_at, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(topic_id) DO UPDATE SET
                quick_intro=excluded.quick_intro,
                news_overview=excluded.news_overview,
                worth_teaching=excluded.worth_teaching,
                key_facts_json=excluded.key_facts_json,
                core_judgments_json=excluded.core_judgments_json,
                classroom_entry=excluded.classroom_entry,
                background_json=excluded.background_json,
                controversy=excluded.controversy,
                media_viewpoints_json=excluded.media_viewpoints_json,
                paper_support_json=excluded.paper_support_json,
                analysis_framework_json=excluded.analysis_framework_json,
                standard_expressions_json=excluded.standard_expressions_json,
                cases_json=excluded.cases_json,
                common_mistakes_json=excluded.common_mistakes_json,
                classroom_questions_json=excluded.classroom_questions_json,
                tags_json=excluded.tags_json,
                updated_at=excluded.updated_at
            """,
            (
                card["card_id"], card["topic_id"], version, card["quick_intro"],
                card["news_overview"], card["worth_teaching"], json_dumps(card["key_facts"]),
                json_dumps(card["core_judgments"]), card["classroom_entry"],
                json_dumps(card["background"]), card["controversy"],
                json_dumps(card["media_viewpoints"]), json_dumps(card["paper_support"]),
                json_dumps(card["analysis_framework"]), json_dumps(card["standard_expressions"]),
                json_dumps(card["cases"]), json_dumps(card["common_mistakes"]),
                json_dumps(card["classroom_questions"]), json_dumps(card["tags"]),
                "editorial_preview", old.get("review_note", "") if old else "",
                None, created_at, now,
            ),
        )

    if active_topic_ids:
        placeholders = ",".join("?" for _ in active_topic_ids)
        conn.execute(f"DELETE FROM teaching_cards WHERE topic_id NOT IN ({placeholders})", active_topic_ids)
        conn.execute(f"DELETE FROM hotspot_topics WHERE topic_id NOT IN ({placeholders})", active_topic_ids)

    conn.execute(
        "DELETE FROM source_articles WHERE article_id NOT IN (SELECT article_id FROM topic_article_links)"
    )

    build_editions(conn, topics, now)
    conn.commit()
    counts = {
        "topics": conn.execute("SELECT COUNT(*) FROM hotspot_topics").fetchone()[0],
        "sources": conn.execute("SELECT COUNT(*) FROM source_articles").fetchone()[0],
        "links": conn.execute("SELECT COUNT(*) FROM topic_article_links").fetchone()[0],
        "cards": conn.execute("SELECT COUNT(*) FROM teaching_cards").fetchone()[0],
        "daily_editions": conn.execute("SELECT COUNT(*) FROM daily_editions").fetchone()[0],
        "weekly_editions": conn.execute("SELECT COUNT(*) FROM weekly_editions").fetchone()[0],
    }
    conn.close()
    return counts


def topic_sort_key(topic: dict[str, Any]) -> tuple[Any, ...]:
    return (
        STATUS_ORDER.get(topic.get("status", ""), 9),
        PRIORITY_ORDER.get(topic.get("priority", ""), 9),
        -int(topic.get("media_count") or 0),
        -int(topic.get("article_count") or 0),
        topic.get("topic", ""),
    )


def build_editions(conn: sqlite3.Connection, topics: list[dict[str, Any]], now: str) -> None:
    # 每次刷新只重建尚未发布的预览期；已发布历史期继续保留。
    conn.execute("DELETE FROM daily_editions WHERE status='preview'")
    conn.execute("DELETE FROM weekly_editions WHERE status='preview'")
    valid_dates = [
        date.fromisoformat(value)
        for topic in topics
        for value in (topic.get("start_date"), topic.get("end_date"))
        if value
    ]
    if not valid_dates:
        return
    end = max(max(valid_dates), date.today())
    start = max(min(valid_dates), end - timedelta(days=45))
    # 历史日报只落在“热点开始／结束”这些有真实资料变化的日期上，并补充今天。
    # 避免把热点持续期内的每一天都伪装成当时已经正式发布过的一期日报。
    issue_dates = sorted(
        {
            date.fromisoformat(value)
            for topic in topics
            for value in (topic.get("start_date"), topic.get("end_date"))
            if value and start <= date.fromisoformat(value) <= end
        }
        | {end}
    )
    for issue_no, current in enumerate(issue_dates, start=1):
        current_text = current.isoformat()
        active = [
            topic for topic in topics
            if (topic.get("start_date") or current_text) <= current_text <= (topic.get("end_date") or current_text)
        ]
        if current == end and not active:
            # 如果今天尚未形成新的达标热点，优先展示最近刚获得新材料的母题。
            # 不能退回到全库中最早的高优先级热点，否则“今日教学判断”会显得过时。
            active = sorted(
                topics,
                key=lambda topic: (
                    -(date.fromisoformat(topic.get("end_date") or "1970-01-01").toordinal()),
                    *topic_sort_key(topic),
                ),
            )[:8]
        else:
            # 日报标题优先取当天新出现或当天完成一轮观察的热点，不能让一个
            # 持续时间较长的高优先级热点占满整段日期档案。
            active = sorted(
                active,
                key=lambda topic: (
                    0 if topic.get("start_date") == current_text else
                    1 if topic.get("end_date") == current_text else 2,
                    *topic_sort_key(topic),
                ),
            )[:8]
        if not active:
            continue
        topic_ids = [topic["topic_id"] for topic in active]
        app_count = sum(int(topic.get("article_count") or 0) for topic in active)
        placeholders = ",".join("?" for _ in topic_ids)
        paper_count = conn.execute(
            f"SELECT COUNT(DISTINCT article_id) FROM topic_article_links WHERE source_kind=? AND topic_id IN ({placeholders})",
            [SOURCE_KIND_PAPER, *topic_ids],
        ).fetchone()[0]
        top = active[0]
        judgment = f"今日重点从“{top['topic']}”切入，训练教师把新闻现象转化为公共问题、责任分析与治理闭环。"
        status = "preview"
        conn.execute(
            """
            INSERT INTO daily_editions(
                edition_id, edition_date, issue_no, title, teaching_judgment,
                topic_ids_json, app_article_count, paper_article_count,
                reading_minutes, status, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(edition_date) DO UPDATE SET
                issue_no=excluded.issue_no,
                title=excluded.title,
                teaching_judgment=excluded.teaching_judgment,
                topic_ids_json=excluded.topic_ids_json,
                app_article_count=excluded.app_article_count,
                paper_article_count=excluded.paper_article_count,
                reading_minutes=excluded.reading_minutes,
                status=CASE
                    WHEN daily_editions.status='published' THEN daily_editions.status
                    ELSE excluded.status
                END,
                updated_at=excluded.updated_at
            """,
            (
                f"daily_{current.strftime('%Y%m%d')}", current_text, issue_no,
                f"{current_text} 热点教学日报", judgment, json_dumps(topic_ids),
                app_count, paper_count, max(5, len(active) * 3), status, now, now,
            ),
        )

    week_groups: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for topic in topics:
        if not topic.get("end_date"):
            continue
        topic_date = date.fromisoformat(topic["end_date"])
        monday = topic_date - timedelta(days=topic_date.weekday())
        week_groups[monday].append(topic)
    for monday, week_topics in week_groups.items():
        selected = sorted(week_topics, key=topic_sort_key)[:10]
        sunday = monday + timedelta(days=6)
        topic_ids = [topic["topic_id"] for topic in selected]
        top_names = "、".join(topic["topic"] for topic in selected[:3])
        conn.execute(
            """
            INSERT INTO weekly_editions(
                edition_id, week_start, week_end, title, teaching_judgment,
                topic_ids_json, status, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(week_start) DO UPDATE SET
                week_end=excluded.week_end,
                title=excluded.title,
                teaching_judgment=excluded.teaching_judgment,
                topic_ids_json=excluded.topic_ids_json,
                status=CASE
                    WHEN weekly_editions.status='published' THEN weekly_editions.status
                    ELSE excluded.status
                END,
                updated_at=excluded.updated_at
            """,
            (
                f"weekly_{monday.strftime('%Y%m%d')}", monday.isoformat(), sunday.isoformat(),
                f"{monday.isoformat()}—{sunday.isoformat()} 教学周报",
                f"本周可围绕{top_names}等母题组织案例比较与治理框架训练。",
                json_dumps(topic_ids), "preview", now, now,
            ),
        )


def row_to_json(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    for key in list(result):
        if key.endswith("_json"):
            result[key.removesuffix("_json")] = json_loads(result.pop(key), [] if key != "analysis_framework_json" else {})
    return result


def table_rows(conn: sqlite3.Connection, table: str, order_by: str) -> list[dict[str, Any]]:
    return [row_to_json(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}")]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_site_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    topics = table_rows(conn, "hotspot_topics", "end_date DESC, priority, topic")
    cards = {row["topic_id"]: row for row in table_rows(conn, "teaching_cards", "updated_at DESC")}
    links = table_rows(conn, "topic_article_links", "topic_id, source_kind, confidence DESC")
    sources = {row["article_id"]: row for row in table_rows(conn, "source_articles", "date DESC, title")}
    daily = table_rows(conn, "daily_editions", "edition_date DESC")
    weekly = table_rows(conn, "weekly_editions", "week_start DESC")
    links_by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in links:
        article = sources.get(link["article_id"], {})
        links_by_topic[link["topic_id"]].append({**link, "article": article})
    topic_payload = []
    for topic in topics:
        topic_payload.append(
            {
                **topic,
                "card": cards.get(topic["topic_id"]),
                "sources": links_by_topic.get(topic["topic_id"], []),
            }
        )
    category_counts = Counter(topic["category"] for topic in topics)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "product": {
            "name": "热点教学日报",
            "description": "把当天热点加工成教师可直接使用的课堂补充。",
            "source_note": "人民日报APP评论发现热点，《人民日报》正式版补充政策、案例与规范表达。",
        },
        "stats": {
            "topics": len(topics),
            "app_articles": sum(1 for source in sources.values() if source["source_kind"] == SOURCE_KIND_APP),
            "paper_articles": sum(1 for source in sources.values() if source["source_kind"] == SOURCE_KIND_PAPER),
            "daily_editions": len(daily),
            "weekly_editions": len(weekly),
        },
        "categories": [{"name": key, "count": value} for key, value in sorted(category_counts.items())],
        "daily_editions": daily,
        "weekly_editions": weekly,
        "topics": topic_payload,
    }


def export_bundle(counts: dict[str, int]) -> dict[str, Any]:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    SITE_ROOT.mkdir(parents=True, exist_ok=True)
    conn = connect_output()
    exports = {
        "hotspot_topics.jsonl": table_rows(conn, "hotspot_topics", "topic_id"),
        "source_articles.jsonl": table_rows(conn, "source_articles", "article_id"),
        "teaching_cards.jsonl": table_rows(conn, "teaching_cards", "card_id"),
        "daily_editions.jsonl": table_rows(conn, "daily_editions", "edition_date"),
        "weekly_editions.jsonl": table_rows(conn, "weekly_editions", "week_start"),
    }
    for name, rows in exports.items():
        write_jsonl(EXPORT_ROOT / name, rows)

    link_rows = table_rows(conn, "topic_article_links", "topic_id, article_id")
    link_path = EXPORT_ROOT / "topic_article_links.csv"
    with link_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = [
            "topic_id", "article_id", "source_kind", "relation_role",
            "confidence", "match_reason", "reviewed", "created_at",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in link_rows)

    payload = build_site_payload(conn)
    payload_path = SITE_ROOT / "data.json"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    for asset in ("index.html", "styles.css", "app.js"):
        shutil.copy2(WEB_ROOT / asset, SITE_ROOT / asset)

    backup_path = EXPORT_ROOT / "hotspot_teaching.sqlite"
    backup_conn = sqlite3.connect(backup_path)
    conn.backup(backup_conn)
    backup_conn.close()
    conn.close()

    checksum = hashlib.sha256()
    for path in sorted(EXPORT_ROOT.glob("*")):
        if path.name == "manifest.json" or not path.is_file():
            continue
        checksum.update(path.name.encode("utf-8"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                checksum.update(chunk)
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "schema_version": 1,
        "source_databases": {
            "hotspot_topics": str(TOPIC_DB.relative_to(ROOT)),
            "peopleapp_articles": str(APP_DB.relative_to(ROOT)),
            "people_daily_articles": str(PAPER_DB.relative_to(ROOT)),
        },
        "counts": counts,
        "sha256": checksum.hexdigest(),
        "files": sorted(path.name for path in EXPORT_ROOT.glob("*") if path.is_file()),
    }
    (EXPORT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="生成热点教学日报双库融合数据")
    parser.add_argument("--paper-limit", type=int, default=0, help="调试时限制人民日报文章数量")
    args = parser.parse_args()

    topics = load_topics()
    paper_articles = load_paper_articles()
    if args.paper_limit > 0:
        paper_articles = paper_articles[-args.paper_limit :]
    counts = refresh_database(topics, paper_articles)
    manifest = export_bundle(counts)
    print(json.dumps({"status": "complete", **counts, "manifest": manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
