#!/usr/bin/env python3
"""Refine the central content idea pool by support strength and duplication."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
ASSET_DB = ROOT / "data" / "core" / "material_assets.sqlite"
ARTICLE_DB = ROOT / "data" / "core" / "articles.sqlite"
REPORT_PATH = ROOT / "data" / "articles" / "公众号文章" / "选题库-精筛说明.md"
MIN_SUPPORT_COUNT = 3


REFINED_IDEAS: List[Dict[str, Any]] = [
    {
        "idea_id": "idea_20260522_style_action",
        "date": "2026-05-22",
        "priority": "S",
        "status": "已完成",
        "platform": "公众号 + 课堂讲解",
        "title": "正确政绩观：从口号到办理链",
        "angle": "把正确政绩观从价值表态落到发现问题、接住问题、整改反馈、制度长效。",
        "outline": ["破误区：政绩观不是背大词", "价值立场：为民造福是最大政绩", "办理动作：查问题、接诉求、清单化、销号改", "长效机制：考核、制度、群众评价一起校准"],
        "support_article_ids": [
            "people_daily_20260203_30137897",
            "people_daily_20260213_30140614",
            "people_daily_20260317_30145571",
            "people_daily_20260320_30146238",
            "people_daily_20260420_30152024",
            "people_daily_20260506_30155009",
            "people_daily_20260514_30156795",
            "people_daily_20260518_30157357",
            "people_daily_20260522_30158427",
            "people_daily_20260524_30158697",
        ],
    },
    {
        "idea_id": "idea_20260518_24_public_service",
        "date": "2026-05-18",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "公共服务均等化：从“有没有”到“够得到”",
        "angle": "公共服务不是平均铺摊子，而是让服务跟着人、需求和生活半径走。",
        "outline": ["服务跟着人走：常住地提供基本公共服务", "资源跟着需求走：医疗、养老、教育、就业进入生活半径", "流程跟着问题走：办不成事、互联网医院、基层服务形成闭环"],
        "support_article_ids": [
            "people_daily_20260320_30146278",
            "people_daily_20260402_30148918",
            "people_daily_20260418_30151774",
            "people_daily_20260419_30151863",
            "people_daily_20260515_30156917",
            "people_daily_20260518_30157413",
            "people_daily_20260519_30157745",
            "people_daily_20260523_30158589",
            "people_daily_20260524_30158705",
        ],
    },
    {
        "idea_id": "idea_20260518_24_grassroots",
        "date": "2026-05-18",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "基层治理不是“万能基层”：权责清、群众进、部门协同",
        "angle": "基层治理不能把所有事压给基层，要把权责边界、群众参与和部门协同讲清楚。",
        "outline": ["清单定责：基层该办什么、不该背什么", "群众入题：议事会、热线、开门治堵发现真实问题", "部门协同：资源、权限和专业力量一起到位", "闭环反馈：办理结果让群众看得见"],
        "support_article_ids": [
            "people_daily_20260209_30139451",
            "people_daily_20260327_30147706",
            "people_daily_20260507_30155295",
            "people_daily_20260511_30155947",
            "people_daily_20260511_30156050",
            "people_daily_20260519_30157694",
            "people_daily_20260519_30157731",
            "people_daily_20260519_30157775",
            "people_daily_20260520_30157785",
        ],
    },
    {
        "idea_id": "idea_20260522_business_rule",
        "date": "2026-05-22",
        "priority": "S",
        "status": "已完成",
        "platform": "公众号",
        "title": "法治化营商环境：不是“不执法”，而是“规范执法”",
        "angle": "营商环境不是一味宽松，而是该管管住、该放放开、执法规范、服务前移。",
        "outline": ["破误区：营商环境不是不监管", "规范执法：减少乱检查、乱罚款、乱查封", "保护权益：依法保护民营企业合法权益", "市场有序：治理恶意索赔和失信行为"],
        "support_article_ids": [
            "people_daily_20260321_30146378",
            "people_daily_20260514_30156784",
            "people_daily_20260521_30158123",
            "people_daily_20260521_30158161",
            "people_daily_20260522_30158421",
            "people_daily_20260522_30158441",
            "people_daily_20260522_30158471",
            "people_daily_20260526_30159095",
            "people_daily_20260528_30159554",
        ],
    },
    {
        "idea_id": "idea_20260522_local_industry",
        "date": "2026-05-22",
        "priority": "S",
        "status": "已完成",
        "platform": "公众号 + PPT",
        "title": "因地制宜写县域发展：把地方优势变成产业能力",
        "angle": "因地制宜不能只写四个字，要写出禀赋识别、科技赋能、链条延伸、品牌场景。",
        "outline": ["识别真优势：资源、产业、文化、区位各不同", "补关键能力：技术、标准、品牌、人才、平台", "做强链条：从单个产品到产业生态", "落到考场：把资源优势转成组织能力和发展优势"],
        "support_article_ids": [
            "people_daily_20260408_30149820",
            "people_daily_20260413_30150722",
            "people_daily_20260511_30155999",
            "people_daily_20260513_30156493",
            "people_daily_20260515_30157008",
            "people_daily_20260522_30158395",
            "people_daily_20260522_30158444",
            "people_daily_20260522_30158482",
        ],
    },
    {
        "idea_id": "idea_refined_20260527_new_productivity",
        "date": "2026-05-27",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + PPT",
        "title": "新质生产力别写空：从词元、农机到田间大模型",
        "angle": "新质生产力要写成真实技术、真实产业和真实场景，而不是堆概念。",
        "outline": ["技术不是抽象名词：词元、算力、数据交易、机器人都有场景", "产业不是追风口：传统产业和农业也能形成新质生产力", "考场表达：技术、要素、场景、制度共同发力"],
        "support_article_ids": [
            "people_daily_20260202_30137423",
            "people_daily_20260221_30141354",
            "people_daily_20260221_30141357",
            "people_daily_20260403_30149016",
            "people_daily_20260410_30150364",
            "people_daily_20260430_30154147",
            "people_daily_20260503_30154680",
            "people_daily_20260504_30154786",
            "people_daily_20260505_30154855",
            "people_daily_20260527_30159307",
        ],
    },
    {
        "idea_id": "idea_refined_20260510_ai_governance",
        "date": "2026-05-10",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "AI治理怎么写：既给创新空间，也守伦理底线",
        "angle": "AI 主题不能只写发展，也不能只写监管，要写创新、应用、风险、审查和责任。",
        "outline": ["发展端：人工智能赋能产业、教育、科研和能源", "风险端：内容规范、伦理审查、劳动权益、能源消耗", "治理端：沙盒监管、标准规则、责任归属、全球治理"],
        "support_article_ids": [
            "people_daily_20260311_30144605",
            "people_daily_20260403_30149139",
            "people_daily_20260409_30150032",
            "people_daily_20260427_30153299",
            "people_daily_20260430_30154245",
            "people_daily_20260507_30155331",
            "people_daily_20260510_30155811",
            "people_daily_20260510_30155810",
            "people_daily_20260521_30158099",
        ],
    },
    {
        "idea_id": "idea_refined_20260530_new_employment",
        "date": "2026-05-30",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 面试题卡",
        "title": "新就业群体治理：从服务对象到城市伙伴",
        "angle": "新就业群体既要权益保障，也能参与城市治理，关键是服务、规则和共治。",
        "outline": ["保障：劳动报酬、休息、职业伤害、纠纷化解", "服务：工会驿站、零工市场、公共就业服务", "共治：小哥议事厅、随手拍、城市运行伙伴"],
        "support_article_ids": [
            "people_daily_20260323_30146641",
            "people_daily_20260323_30146660",
            "people_daily_20260427_30153336",
            "people_daily_20260430_30154272",
            "people_daily_20260517_30157307",
            "people_daily_20260519_30157694",
            "people_daily_20260520_30157814",
            "people_daily_20260530_30159963",
        ],
    },
    {
        "idea_id": "idea_refined_20260522_rural_modernization",
        "date": "2026-05-22",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "乡村振兴不要只写产业兴旺：农业现代化也要靠科技、人才和服务",
        "angle": "乡村振兴要把粮食安全、科技强农、片区推进、青年入乡和乡村服务连成一套体系。",
        "outline": ["政策底座：中央一号文件和农业农村现代化", "产业能力：科技、农机、村播、供应链进入乡村", "人才组织：新农人、青年入乡、片区化推进"],
        "support_article_ids": [
            "people_daily_20260204_30138215",
            "people_daily_20260204_30138216",
            "people_daily_20260204_30138228",
            "people_daily_20260320_30146212",
            "people_daily_20260420_30152077",
            "people_daily_20260428_30153638",
            "people_daily_20260508_30155537",
            "people_daily_20260522_30158510",
            "people_daily_20260522_30158508",
        ],
    },
    {
        "idea_id": "idea_refined_20260521_culture_consumption",
        "date": "2026-05-21",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "文化传承不是摆出来，而是连起来",
        "angle": "文化传承要进入公共空间、生活方式、消费场景和产业转化。",
        "outline": ["保护：文物和非遗要有法治、数字化、专业修复", "连接：博物馆、展演、文旅、城市礼物进入日常生活", "转化：文化消费和年轻表达激活新动能"],
        "support_article_ids": [
            "people_daily_20260224_30141615",
            "people_daily_20260226_30142274",
            "people_daily_20260228_30142691",
            "people_daily_20260321_30146404",
            "people_daily_20260329_30147956",
            "people_daily_20260331_30148383",
            "people_daily_20260403_30149028",
            "people_daily_20260423_30152689",
            "people_daily_20260521_30158157",
        ],
    },
    {
        "idea_id": "idea_refined_20260502_ecology_law",
        "date": "2026-05-02",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "生态文明怎么写：把绿色发展写成法治、治理和长期主义",
        "angle": "生态题不能只写风景，要写制度、治理成本、法治保障和长期修复。",
        "outline": ["法治：生态环境法典提供制度框架", "治理：地方生态治理要算企业账、政府账、社会账", "长期：自然保护区和生态修复体现久久为功"],
        "support_article_ids": [
            "people_daily_20260203_30137806",
            "people_daily_20260306_30143684",
            "people_daily_20260307_30143787",
            "people_daily_20260307_30143785",
            "people_daily_20260323_30146572",
            "people_daily_20260404_30149211",
            "people_daily_20260414_30150967",
            "people_daily_20260502_30154621",
        ],
    },
    {
        "idea_id": "idea_refined_20260514_resilience",
        "date": "2026-05-14",
        "priority": "B",
        "status": "备选",
        "platform": "课堂讲解 + 面试题卡",
        "title": "韧性治理怎么写：风险早识别、资源早前置、系统能联动",
        "angle": "防灾减灾不是灾后救急，而是监测预警、科普教育、物资前置和基层能力建设。",
        "outline": ["风险识别：极端天气和灾害趋势要提前研判", "资源前置：应急物资、救援力量、基层网格要到位", "系统联动：科技赋能、教育宣传、部门协同一起发力"],
        "support_article_ids": [
            "people_daily_20260512_30156306",
            "people_daily_20260513_30156523",
            "people_daily_20260513_30156524",
            "people_daily_20260514_30156818",
        ],
    },
    {
        "idea_id": "idea_refined_20260529_city_update",
        "date": "2026-05-29",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "城市更新别急着拆：先体检、再保护、再服务",
        "angle": "城市更新要把安全、文脉、儿童友好、公共空间和群众体验放在一起。",
        "outline": ["先体检：发现城市运行中的真实问题", "再保护：文物、街区、风貌进入更新规则", "再服务：儿童、居民、游客的日常体验成为治理尺度"],
        "support_article_ids": [
            "people_daily_20260515_30156954",
            "people_daily_20260517_30157300",
            "people_daily_20260517_30157301",
            "people_daily_20260517_30157305",
            "people_daily_20260526_30159203",
            "people_daily_20260528_30159550",
            "people_daily_20260529_30159827",
        ],
    },
    {
        "idea_id": "idea_refined_20260422_unified_market",
        "date": "2026-04-22",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + PPT",
        "title": "全国统一大市场怎么写具体：规则、设施和要素一起通",
        "angle": "统一大市场不是口号，而是规则统一、设施互联、要素流动和监管协同。",
        "outline": ["规则统一：破除地方保护和市场分割", "设施互联：跨省高速、算力协同、物流通道降低成本", "要素流动：让超大规模市场优势转化为发展优势"],
        "support_article_ids": [
            "people_daily_20260323_30146628",
            "people_daily_20260329_30147949",
            "people_daily_20260403_30148975",
            "people_daily_20260410_30150362",
            "people_daily_20260420_30152025",
            "people_daily_20260422_30152586",
        ],
    },
    {
        "idea_id": "idea_refined_20260523_basic_research",
        "date": "2026-05-23",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "科技强国怎么写：基础研究不是背景板",
        "angle": "科技强国不能只盯产品突破，要写源头创新、科研生态、人才培养和成果转化。",
        "outline": ["源头：基础研究决定科技创新底座", "生态：科研平台、青年人才、评价机制共同支撑", "转化：从0到1之后还要跑出加速度"],
        "support_article_ids": [
            "people_daily_20260501_30154502",
            "people_daily_20260502_30154642",
            "people_daily_20260502_30154641",
            "people_daily_20260516_30157160",
            "people_daily_20260523_30158644",
            "people_daily_20260523_30158646",
            "people_daily_20260523_30158645",
            "people_daily_20260528_30159549",
        ],
    },
    {
        "idea_id": "idea_refined_20260511_digital_governance",
        "date": "2026-05-11",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 面试题卡",
        "title": "数字治理别写成“上系统”：关键是流程再造和线下兜底",
        "angle": "数字治理不是把服务搬到线上，而是用数据重塑流程，同时保留人工服务和责任闭环。",
        "outline": ["提效率：高效办成一件事要靠数据共享和流程再造", "防形式：互联网医院、数字平台不能制造新门槛", "有兜底：线下窗口、人工帮办、特殊群体服务不能少"],
        "support_article_ids": [
            "people_daily_20260511_30155947",
            "people_daily_20260515_30156917",
            "people_daily_20260424_30152872",
            "people_daily_20260403_30149139",
            "people_daily_20260525_30158847",
        ],
    },
]


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_list(text: str | None) -> List[str]:
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in value] if isinstance(value, list) else [str(value)]


def title_key(title: str) -> str:
    return "".join(str(title).split()).lower()


def ensure_refine_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS content_ideas_refine_archive (
            run_id TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            idea_id TEXT,
            date TEXT,
            title TEXT,
            angle TEXT,
            platform TEXT,
            support_article_ids_json TEXT,
            outline_json TEXT,
            status TEXT,
            priority TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS content_idea_rejected_keys (
            title_key TEXT PRIMARY KEY,
            original_title TEXT NOT NULL,
            reason TEXT NOT NULL,
            refined_idea_id TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def article_map() -> Dict[str, sqlite3.Row]:
    conn = connect(ARTICLE_DB)
    try:
        return {row["article_id"]: row for row in conn.execute("SELECT article_id, date, title, source_url FROM articles")}
    finally:
        conn.close()


def validate_refined_ideas(articles: Dict[str, sqlite3.Row]) -> None:
    seen: set[str] = set()
    for idea in REFINED_IDEAS:
        if idea["idea_id"] in seen:
            raise ValueError(f"重复选题 ID: {idea['idea_id']}")
        seen.add(idea["idea_id"])
        support_ids = list(dict.fromkeys(idea["support_article_ids"]))
        missing = [article_id for article_id in support_ids if article_id not in articles]
        if missing:
            raise ValueError(f"{idea['title']} 有不存在的支撑文章 ID: {missing}")
        if len(support_ids) < MIN_SUPPORT_COUNT:
            raise ValueError(f"{idea['title']} 支撑文章不足 {MIN_SUPPORT_COUNT} 篇")


def current_rows(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM content_ideas ORDER BY date DESC, idea_id"))


def already_refined(rows: List[sqlite3.Row]) -> bool:
    if len(rows) != len(REFINED_IDEAS):
        return False
    by_id = {row["idea_id"]: row for row in rows}
    for idea in REFINED_IDEAS:
        row = by_id.get(idea["idea_id"])
        if not row:
            return False
        if row["title"] != idea["title"]:
            return False
        if json_list(row["support_article_ids_json"]) != list(dict.fromkeys(idea["support_article_ids"])):
            return False
    return True


def archive_rows(conn: sqlite3.Connection, rows: Iterable[sqlite3.Row], run_id: str, archived_at: str) -> int:
    count = 0
    for row in rows:
        conn.execute(
            """
            INSERT INTO content_ideas_refine_archive(
                run_id, archived_at, idea_id, date, title, angle, platform,
                support_article_ids_json, outline_json, status, priority, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                archived_at,
                row["idea_id"],
                row["date"],
                row["title"],
                row["angle"],
                row["platform"],
                row["support_article_ids_json"],
                row["outline_json"],
                row["status"],
                row["priority"] if "priority" in row.keys() else "B",
                row["created_at"],
                row["updated_at"],
            ),
        )
        count += 1
    return count


def reject_old_titles(conn: sqlite3.Connection, rows: Iterable[sqlite3.Row], now: str) -> int:
    refined_ids = {idea["idea_id"] for idea in REFINED_IDEAS}
    refined_keys = {title_key(idea["title"]) for idea in REFINED_IDEAS}
    rejected = 0
    for row in rows:
        key = title_key(row["title"])
        if row["idea_id"] in refined_ids or key in refined_keys:
            continue
        support_count = len(json_list(row["support_article_ids_json"]))
        reason = "支撑文章不足3篇" if support_count < MIN_SUPPORT_COUNT else "重复度高，已合并进精筛选题"
        conn.execute(
            """
            INSERT INTO content_idea_rejected_keys(title_key, original_title, reason, refined_idea_id, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(title_key) DO UPDATE SET
                original_title = excluded.original_title,
                reason = excluded.reason,
                refined_idea_id = excluded.refined_idea_id,
                updated_at = excluded.updated_at
            """,
            (key, row["title"], reason, "", now),
        )
        rejected += 1
    return rejected


def replace_content_ideas(conn: sqlite3.Connection, now: str) -> None:
    conn.execute("DELETE FROM content_ideas")
    for idea in REFINED_IDEAS:
        support_ids = list(dict.fromkeys(idea["support_article_ids"]))
        conn.execute(
            """
            INSERT INTO content_ideas(
                idea_id, date, title, angle, platform, support_article_ids_json,
                outline_json, status, priority, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea["idea_id"],
                idea["date"],
                idea["title"],
                idea["angle"],
                idea["platform"],
                dumps(support_ids),
                dumps(idea["outline"]),
                idea["status"],
                idea["priority"],
                now,
                now,
            ),
        )


def refresh_exports() -> None:
    import export_content_ideas

    conn = export_content_ideas.connect(export_content_ideas.DEFAULT_ASSET_DB)
    try:
        article_titles = export_content_ideas.load_article_titles(conn, export_content_ideas.DEFAULT_ARTICLE_DB)
        records = [
            export_content_ideas.idea_record(row, article_titles)
            for row in export_content_ideas.fetch_ideas(conn, None, None)
        ]
    finally:
        conn.close()
    export_content_ideas.write_markdown(export_content_ideas.DEFAULT_MD_PATH, records)
    export_content_ideas.write_csv(export_content_ideas.DEFAULT_CSV_PATH, records)


def write_report(path: Path, before_rows: List[sqlite3.Row], articles: Dict[str, sqlite3.Row], result: Dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    before_count = result.get("before", len(before_rows))
    lines = [
        "# 公众号选题库精筛说明",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "> 筛选口径：每个保留选题至少绑定 3 篇人民日报文章；重复度高的标题合并到更强母题；素材不足的标题不进入主选题库。",
        "",
        "## 处理结果",
        "",
        "| 项目 | 数量 |",
        "|---|---:|",
        f"| 原选题 | {before_count} |",
        f"| 精筛后选题 | {len(REFINED_IDEAS)} |",
        f"| 归档旧选题 | {result.get('archived', 0)} |",
        f"| 写入剔除标题键 | {result.get('rejected', 0)} |",
        "",
        "## 保留选题",
        "",
        "| 优先级 | 状态 | 选题 | 支撑文章数 | 支撑文章 |",
        "|---|---|---|---:|---|",
    ]
    for idea in REFINED_IDEAS:
        titles = "；".join(articles[article_id]["title"] for article_id in idea["support_article_ids"])
        lines.append(
            f"| {idea['priority']} | {idea['status']} | {idea['title']} | "
            f"{len(idea['support_article_ids'])} | {titles} |"
        )

    lines.extend(["", "## 删除或合并原则", ""])
    lines.append("- 支撑文章少于 3 篇的，不再作为独立选题。")
    lines.append("- 标题只是同一母题的不同说法时，合并到更强的母题，例如正确政绩观、公共服务均等化、基层治理、新质生产力等。")
    lines.append("- 已完成或已精筛的重点选题尽量保留原 `idea_id`，避免丢失人工状态。")
    lines.append("- 旧选题已经写入数据库归档表 `content_ideas_refine_archive`，被剔除标题写入 `content_idea_rejected_keys`，防止自动同步时重复回流。")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def refine_content_ideas(db_path: Path = ASSET_DB, refresh: bool = True, report_path: Path = REPORT_PATH) -> Dict[str, int]:
    articles = article_map()
    validate_refined_ideas(articles)
    conn = connect(db_path)
    try:
        ensure_refine_tables(conn)
        rows = current_rows(conn)
        if already_refined(rows):
            archived = latest_archive_count(conn)
            rejected = rejected_key_count(conn)
            result = {
                "before": archived or len(rows),
                "after": len(REFINED_IDEAS),
                "archived": archived,
                "rejected": rejected,
                "changed": 0,
            }
            write_report(report_path, rows, articles, result)
            return result
        run_id = datetime.now().strftime("%Y%m%d%H%M%S")
        now = datetime.now().isoformat(timespec="seconds")
        archived = archive_rows(conn, rows, run_id, now)
        rejected = reject_old_titles(conn, rows, now)
        replace_content_ideas(conn, now)
        conn.commit()
    finally:
        conn.close()

    result = {"before": len(rows), "after": len(REFINED_IDEAS), "archived": archived, "rejected": rejected, "changed": 1}
    write_report(report_path, rows, articles, result)
    if refresh:
        refresh_exports()
    return result


def latest_archive_count(conn: sqlite3.Connection) -> int:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'content_ideas_refine_archive'"
    ).fetchone()
    if not table:
        return 0
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM content_ideas_refine_archive
        WHERE run_id = (SELECT MAX(run_id) FROM content_ideas_refine_archive)
        """
    ).fetchone()
    return int(row["count"] or 0)


def rejected_key_count(conn: sqlite3.Connection) -> int:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'content_idea_rejected_keys'"
    ).fetchone()
    if not table:
        return 0
    row = conn.execute("SELECT COUNT(*) AS count FROM content_idea_rejected_keys").fetchone()
    return int(row["count"] or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="按至少3篇支撑文章和去重规则精筛公众号选题库")
    parser.add_argument("--db-path", default=str(ASSET_DB), help="素材资产库路径")
    parser.add_argument("--no-refresh", action="store_true", help="不刷新 Markdown/CSV 总表")
    parser.add_argument("--report-path", default=str(REPORT_PATH), help="精筛说明输出路径")
    args = parser.parse_args()
    result = refine_content_ideas(Path(args.db_path), refresh=not args.no_refresh, report_path=Path(args.report_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
