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
REPORT_PATH = ROOT / "data" / "articles" / "选题库-精筛说明.md"
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
        "status": "已完成",
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
    {
        "idea_id": "idea_refined_20260611_six_networks",
        "date": "2026-06-11",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + PPT",
        "title": "“六张网”怎么写：不是大基建清单，而是发展底座重塑",
        "angle": "六张网要写成有效投资、基础设施补短板和新质生产力底座的组合，而不是简单罗列水网、电网、算力网。",
        "outline": ["看底线：水网、地下管网、物流网补安全和民生短板", "看上限：新型电网、算力网、新一代通信网支撑未来产业", "看方法：统筹建设、动态推进，让投资转化为长期动能"],
        "support_article_ids": [
            "people_daily_20260518_30157445",
            "people_daily_20260525_30158964",
            "people_daily_20260525_30158967",
            "people_daily_20260528_30159576",
            "people_daily_20260529_30159837",
            "people_daily_20260601_30160073",
            "people_daily_20260603_30160589",
            "people_daily_20260608_30161733",
            "people_daily_20260608_30161697",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_anti_involution",
        "date": "2026-06-11",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + PPT + 小红书",
        "title": "反内卷不是反竞争：让竞争回到价值创造",
        "angle": "反内卷不是限制竞争，而是纠偏低水平、同质化、内耗型竞争，让市场竞争转向创新、质量、服务和价值创造。",
        "outline": ["反什么：低价低质、平台规则滥用、同质化内耗和地方保护", "靠什么反：法治、标准、监管、统一市场和知识产权保护", "立什么：从卷价格到优价值，从拼消耗到拼创新"],
        "support_article_ids": [
            "people_daily_20260122_30134730",
            "people_daily_20260225_30141939",
            "people_daily_20260225_30141897",
            "people_daily_20260225_30141896",
            "people_daily_20260228_30142730",
            "people_daily_20260320_30146246",
            "people_daily_20260403_30148982",
            "people_daily_20260507_30155329",
            "people_daily_20260527_30159424",
            "people_daily_20260528_30159614",
            "people_daily_20260603_30160602",
            "people_daily_20260604_30160963",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_ocean_economy",
        "date": "2026-06-11",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "向海图强怎么写：不是“靠海吃海”，而是科技、生态和产业链",
        "angle": "海洋经济要从资源利用升级为科技装备、生态修复、港产城联动和海洋产业链协同。",
        "outline": ["科技向海：深海装备、智慧航运、海洋科技守护蓝色空间", "产业向海：港口枢纽、海盐、育苗、渔业形成全链条", "生态向海：海湾治理和资源恢复让海岸线变幸福线"],
        "support_article_ids": [
            "people_daily_20260511_30156007",
            "people_daily_20260517_30157297",
            "people_daily_20260518_30157359",
            "people_daily_20260520_30157829",
            "people_daily_20260521_30158094",
            "people_daily_20260523_30158639",
            "people_daily_20260601_30160075",
            "people_daily_20260605_30161067",
            "people_daily_20260608_30161715",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_silver_economy",
        "date": "2026-06-11",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 面试题卡",
        "title": "银发经济不是养老负担：把老龄化写成服务供给和人力资源",
        "angle": "老龄化不能只写兜底保障，还要写社区服务、长护险、互助养老、老年教育和老年人力资源开发。",
        "outline": ["兜底：长护险、互助养老、社区服务托住基本生活", "发展：老年教育、适老化产品和康养消费拓展需求", "参与：高能量老年人和老年人力资源让老有所为"],
        "support_article_ids": [
            "people_daily_20260519_30157745",
            "people_daily_20260522_30158443",
            "people_daily_20260528_30159599",
            "people_daily_20260602_30160421",
            "people_daily_20260602_30160422",
            "people_daily_20260604_30161019",
            "people_daily_20260604_30161021",
            "people_daily_20260609_30161974",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_service_consumption",
        "date": "2026-06-11",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "服务消费怎么写：不是发券促销，而是把好服务嵌入生活半径",
        "angle": "提振消费要从商品刺激转向优质服务供给，用一刻钟便民生活圈、康养、文旅、体验经济和情绪消费承接新需求。",
        "outline": ["空间：一刻钟便民生活圈让服务靠近人", "场景：康养、文旅、主题乐园、超级周末创造体验价值", "质量：扩大优质商品和服务供给，推动消费从流量转向留量"],
        "support_article_ids": [
            "people_daily_20260527_30159425",
            "people_daily_20260601_30160125",
            "people_daily_20260602_30160380",
            "people_daily_20260603_30160660",
            "people_daily_20260607_30161518",
            "people_daily_20260608_30161697",
            "people_daily_20260609_30161966",
            "people_daily_20260609_30161967",
            "people_daily_20260609_30161977",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_ai_education",
        "date": "2026-06-11",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "AI时代教育怎么写：不是人人学工具，而是重塑思维和终身学习",
        "angle": "人工智能进入教育后，关键不只是会用工具，而是培养思维能力、数字阅读能力、终身学习能力和技能更新能力。",
        "outline": ["学生端：AI浪潮下更要培养问题意识、判断力和思维能力", "成人端：终身教育和职业技能培训应对结构性就业变化", "社会端：新质生产力创造就业新空间，也倒逼学习体系更新"],
        "support_article_ids": [
            "people_daily_20260531_30160049",
            "people_daily_20260603_30160612",
            "people_daily_20260603_30160613",
            "people_daily_20260605_30161066",
            "people_daily_20260607_30161512",
            "people_daily_20260609_30161974",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_low_altitude",
        "date": "2026-06-11",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "低空经济别只追风口：先把“飞得起来”和“管得住”写清楚",
        "angle": "低空经济既是新兴产业，也是治理能力题，要同时写产业应用、基础设施、安全航路和场景落地。",
        "outline": ["产业：无人机、通用航空、农业和物流场景打开空间", "治理：为无人机画出安全的路，空天地海通信网提供支撑", "落地：低空经济最终要服务生产、生活和公共安全"],
        "support_article_ids": [
            "people_daily_20260224_30141620",
            "people_daily_20260410_30150301",
            "people_daily_20260527_30159307",
            "people_daily_20260605_30161066",
            "people_daily_20260608_30161733",
            "people_daily_20260608_30161734",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_accounts_confidence",
        "date": "2026-06-11",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 面试题卡",
        "title": "清欠账款怎么写：账款链也是信心链",
        "angle": "解决拖欠企业账款不是财务小事，而是稳企业、稳就业、稳预期和优化营商环境的重要抓手。",
        "outline": ["政绩观：新官要理旧账，旧账不清就会损害政府公信力", "营商环境：账款兑现关系企业现金流和市场信心", "治理链：信用体系、规范执行、小微金融和公平诚信共同发力"],
        "support_article_ids": [
            "people_daily_20260317_30145559",
            "people_daily_20260429_30153791",
            "people_daily_20260511_30156047",
            "people_daily_20260521_30158123",
            "people_daily_20260602_30160444",
            "people_daily_20260603_30160558",
            "people_daily_20260608_30161667",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_resource_circulation",
        "date": "2026-06-11",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "资源循环怎么写：不是回收旧物，而是绿色消费和产业链再造",
        "angle": "资源循环要写成消费更新、绿色生产、再生资源利用和产业链延伸的系统工程。",
        "outline": ["消费端：以旧换新激活需求，也推动产品升级", "生产端：绿色链条和零碳场景倒逼企业转型", "产业端：再生资源和资源型产业升级形成新增长点"],
        "support_article_ids": [
            "people_daily_20260513_30156581",
            "people_daily_20260513_30156582",
            "people_daily_20260522_30158395",
            "people_daily_20260531_30160026",
            "people_daily_20260603_30160659",
            "people_daily_20260605_30161156",
        ],
    },
    {
        "idea_id": "idea_refined_20260611_westward_development",
        "date": "2026-06-11",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + PPT",
        "title": "大国向西怎么写：不是区域口号，而是通道、算力、产业和安全腹地",
        "angle": "西部发展要从补短板升级为开放通道、算力布局、产业承接、生态安全和战略腹地建设。",
        "outline": ["通道：交通物流和陆海联动打通开放新空间", "产业：算力、能源、制造和特色产业塑造新增长极", "安全：生态屏障、边疆发展和战略腹地共同托底大国韧性"],
        "support_article_ids": [
            "people_daily_20260521_30158083",
            "people_daily_20260526_30159178",
            "people_daily_20260528_30159575",
            "people_daily_20260603_30160556",
            "people_daily_20260603_30160589",
            "people_daily_20260603_30160656",
            "people_daily_20260603_30160657",
            "people_daily_20260608_30161711",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_old_accounts_achievement",
        "date": "2026-06-12",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "正确政绩观怎么写：新官理旧账，才是真担当",
        "angle": "正确政绩观不能只看新项目、新口号，也要看敢不敢接住历史遗留问题、纠偏无效工程、把群众账和长远账算明白。",
        "outline": ["接旧账：历史遗留问题不能一推了之", "纠偏账：项目建成后更要看能不能用、群众认不认", "长远账：克服大干快上冲动，把制度和生态账算进去"],
        "support_article_ids": [
            "people_daily_20260612_30162628",
            "people_daily_20260612_30162670",
            "people_daily_20260612_30162671",
            "people_daily_20260612_30162685",
            "people_daily_20260612_30162683",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_services_follow_people",
        "date": "2026-06-12",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "新型城镇化怎么写：不是进城落脚，而是服务跟着人走",
        "angle": "以人为本的新型城镇化，核心不是人口统计口径变化，而是让教育、就业、养老、权益保障等公共服务跟着常住人口和真实需求走。",
        "outline": ["对象跟着人走：从户籍人口转向常住人口和新职业人群", "资源跟着需求走：教育、养老、就业、住房进入生活半径", "治理跟着风险走：权益保障和数智服务把新市民真正接住"],
        "support_article_ids": [
            "people_daily_20260608_30161752",
            "people_daily_20260612_30162695",
            "people_daily_20260612_30162696",
            "people_daily_20260612_30162633",
            "people_daily_20260614_30162849",
            "people_daily_20260614_30162873",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_tech_transfer_chain",
        "date": "2026-06-12",
        "priority": "S",
        "status": "备选",
        "platform": "公众号 + PPT",
        "title": "科技成果转化别只写“产学研”：关键是打通最后一公里",
        "angle": "科技成果转化不是论文自然变产品，而是政策松绑、平台服务、金融保险、技术经理人、市场需求和人才培养一起接上。",
        "outline": ["从实验室到生产线：成果要有场景、有企业、有需求", "从政策到服务链：平台、金融、保险、技术经理人协同发力", "从创新到就业：微专业、创业服务和AI应用把成果转成产业机会"],
        "support_article_ids": [
            "people_daily_20260612_30162631",
            "people_daily_20260613_30162793",
            "people_daily_20260612_30162667",
            "people_daily_20260612_30162693",
            "people_daily_20260614_30162874",
            "people_daily_20260614_30162873",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_employment_chain",
        "date": "2026-06-12",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 面试题卡",
        "title": "破解就业难，不能只写“多给岗位”：产业、技能、服务和创业一起成链",
        "angle": "破解就业难要把产业造岗、技能练岗、服务送岗、创业带岗连成就业链，而不是只停留在招聘和求职建议。",
        "outline": ["产业端造岗：新质生产力、生产性服务业、数字经济创造新岗位", "教育端练岗：职业教育、技能培训、微专业精准对接岗位需求", "服务端送岗：国聘行动、岗位归集、AI匹配提高就业服务效率", "创业端带岗：陪跑服务、资金支持、订单对接让创业带动就业"],
        "support_article_ids": [
            "people_daily_20260529_30159831",
            "people_daily_20260531_30159994",
            "people_daily_20260601_30160088",
            "people_daily_20260604_30160972",
            "people_daily_20260605_30161066",
            "people_daily_20260607_30161512",
            "people_daily_20260608_30161711",
            "people_daily_20260610_30162263",
            "people_daily_20260611_30162450",
            "people_daily_20260611_30162384",
            "people_daily_20260612_30162655",
            "people_daily_20260612_30162667",
            "people_daily_20260614_30162873",
            "people_daily_20260614_30162874",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_modern_agri_service",
        "date": "2026-06-12",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "现代农业不是只靠苦干：科技体检、田保姆和青年农机手一起上",
        "angle": "农业现代化要写出科技下田、社会化服务和新农人队伍，不只是写农民辛苦、粮食增产。",
        "outline": ["技术下田：给黑土地做体检，让施肥和管护更精准", "服务入田：田保姆、社会化服务把小农户接入现代农业", "青年到田：青年农机手、新农人让农业有技术也有人才"],
        "support_article_ids": [
            "people_daily_20260612_30162661",
            "people_daily_20260612_30162613",
            "people_daily_20260613_30162801",
            "people_daily_20260614_30162853",
        ],
    },
    {
        "idea_id": "idea_refined_20260613_cultural_heritage_life",
        "date": "2026-06-13",
        "priority": "A",
        "status": "备选",
        "platform": "公众号 + 小红书",
        "title": "文化遗产保护高分写法：先保护好，再让它回到日常",
        "angle": "文化遗产不是静态摆设，也不是过度商业化的流量道具，而是要在保护第一的基础上进入生活、教育、消费和共同体记忆。",
        "outline": ["保护第一：整体性、系统性保护守住文化根脉", "表达更新：用不同视角打开文化遗产，让公众看得懂、愿意亲近", "回到日常：文旅融合、门口文物和生活美学让文化成为共同记忆"],
        "support_article_ids": [
            "people_daily_20260613_30162792",
            "people_daily_20260612_30162684",
            "people_daily_20260613_30162786",
            "people_daily_20260613_30162787",
            "people_daily_20260613_30162788",
            "people_daily_20260613_30162789",
            "people_daily_20260614_30162845",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_green_common_prosperity",
        "date": "2026-06-12",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + 课堂讲解",
        "title": "绿色发展别只写生态好：要写出保护、转化和富民闭环",
        "angle": "生态文明的可用写法，是把资源约束、系统保护、生态产品价值转化和群众增收连成一条链。",
        "outline": ["先保护：水资源、绿水青山和生态系统是发展底座", "再转化：生态产品价值要进入产业、服务和市场", "能富民：绿色发展最终要让群众从保护中受益"],
        "support_article_ids": [
            "people_daily_20260612_30162654",
            "people_daily_20260613_30162797",
            "people_daily_20260612_30162683",
            "people_daily_20260614_30162865",
            "people_daily_20260612_30162661",
        ],
    },
    {
        "idea_id": "idea_refined_20260612_media_fusion_governance",
        "date": "2026-06-12",
        "priority": "B",
        "status": "备选",
        "platform": "公众号 + PPT",
        "title": "主流媒体融合：不是多开账号，而是重构内容、技术和服务",
        "angle": "媒体融合的重点不是形式相加，而是内容创新、机制再造、数智赋能、政务服务和国际传播能力同步提升。",
        "outline": ["内容重构：主流表达要适配新传播场景", "技术赋能：数智建设提升生产、分发和互动能力", "服务延伸：媒体融合要连接政务、文化产业和国际传播"],
        "support_article_ids": [
            "people_daily_20260612_30162698",
            "people_daily_20260612_30162605",
            "people_daily_20260613_30162833",
            "people_daily_20260614_30162884",
            "people_daily_20260612_30162653",
            "people_daily_20260612_30162686",
        ],
    },
    {'idea_id': 'idea_20260615_21_health_nearby_service',
     'date': '2026-06-15',
     'priority': 'S',
     'status': '备选',
     'platform': '公众号 + 课堂讲解',
     'title': '健康中国怎么写：不是医院越大越好，而是优质服务离群众更近',
     'angle': '健康中国的高分写法，不是堆医院、设备和投入，而是把医改、医共体、基层服务、儿童健康和预防关口连成一条可及可感的服务链。',
     'outline': ['破误区：健康不是医疗资源简单堆大堆强',
                 '总纲：人民健康是现代化的重要指标',
                 '机制：三医联动、医共体和优质医疗资源下沉',
                 '延伸：儿童健康、适儿化空间和预防关口前移',
                 '考场迁移：健康中国=公平可及+基层能力+全周期守护'],
     'support_article_ids': ['people_daily_20260615_30163051',
                             'people_daily_20260621_30164023',
                             'people_daily_20260617_30163386',
                             'people_daily_20260621_30164032',
                             'people_daily_20260616_30163294']},
    {'idea_id': 'idea_20260615_21_edu_tech_talent_chain',
     'date': '2026-06-15',
     'priority': 'S',
     'status': '备选',
     'platform': '公众号 + PPT',
     'title': '教育科技人才一体怎么写：不是三个词并列，而是一条创新链',
     'angle': '教育、科技、人才不是三个政策名词并列，而是“基础研究出源头、教育育人才、金融和制度促转化、产业接场景”的创新链。',
     'outline': ['总纲：教育科技人才是现代化基础性、战略性支撑',
                 '源头：基础研究和原始创新决定创新后劲',
                 '土壤：科普和创新文化扩大高素质创新大军',
                 '转化：赋权改革、科技金融、融资租赁把成果接到产业',
                 '表达公式：基础研究 -> 人才培养 -> 制度供给 -> 金融支撑 -> 场景落地'],
     'support_article_ids': ['people_daily_20260616_30163258',
                             'people_daily_20260615_30163002',
                             'people_daily_20260616_30163263',
                             'people_daily_20260615_30163004',
                             'people_daily_20260620_30163929',
                             'people_daily_20260615_30163036',
                             'people_daily_20260619_30163844',
                             'people_daily_20260618_30163743']},
    {'idea_id': 'idea_20260615_21_service_experience_brand',
     'date': '2026-06-15',
     'priority': 'S',
     'status': '备选',
     'platform': '公众号 + 小红书',
     'title': '服务业高质量发展：从“卖产品”到“卖体验、卖品牌、卖信任”',
     'angle': '服务业不是第三产业泛泛而谈，而是支撑产业升级、扩大就业、释放消费和提升开放水平的关键能力。',
     'outline': ['政策层：服务业扩能提质，培育中国服务品牌',
                 '产业层：生产性服务业向专业化和价值链高端延伸',
                 '消费层：文旅、户外、邮轮、AI伴游从看景转向体验',
                 '开放层：入境游和中欧班列体现中国服务的国际可信度',
                 '考场迁移：服务业=就业容量+消费场景+产业支撑+开放品牌'],
     'support_article_ids': ['people_daily_20260617_30163384',
                             'people_daily_20260617_30163369',
                             'people_daily_20260620_30163924',
                             'people_daily_20260619_30163870',
                             'people_daily_20260616_30163300',
                             'people_daily_20260618_30163761',
                             'people_daily_20260619_30163868',
                             'people_daily_20260621_30164052',
                             'people_daily_20260621_30164053']},
    {'idea_id': 'idea_20260615_21_ai_real_scenes_rules',
     'date': '2026-06-15',
     'priority': 'A',
     'status': '备选',
     'platform': '公众号 + 课堂讲解',
     'title': 'AI应用别只写“赋能”：真实场景、合理定价和安全规则要一起跟上',
     'angle': 'AI进入现实世界后，考点不只是技术先进，还包括场景是否真实、价格是否合理、隐私和安全是否守得住。',
     'outline': ['应用端：物理AI、人机协同学车、AI旅游、钢铁定制化生产',
                 '定价端：大模型收费要看成本、价值和用户权益',
                 '风险端：智能眼镜偷拍、AI诈骗说明技术越近身越要治理',
                 '方法端：因地制宜做场景建设，规则与应用同步生长'],
     'support_article_ids': ['people_daily_20260615_30162995',
                             'people_daily_20260616_30163243',
                             'people_daily_20260620_30163930',
                             'people_daily_20260620_30163931',
                             'people_daily_20260621_30164025',
                             'people_daily_20260621_30164052',
                             'people_daily_20260621_30164053',
                             'people_daily_20260621_30164031',
                             'people_daily_20260618_30163762',
                             'people_daily_20260618_30163707']},
    {'idea_id': 'idea_20260615_21_common_prosperity_region',
     'date': '2026-06-15',
     'priority': 'A',
     'status': '备选',
     'platform': '公众号 + PPT',
     'title': '共同富裕不是平均用力：区域协作、县域工程和产业帮扶一起发力',
     'angle': '共同富裕不能写成均分资源，而要写成区域协调、东西部协作、县域工程、产业造血和公共服务改善的组合。',
     'outline': ['破误区：共同富裕不是平均分配，也不是短期输血',
                 '区域协作：闽宁协作、山海情体现优势互补和人才流动',
                 '县域工程：广东“百千万工程”把城乡区域协调落到县镇村',
                 '产业造血：物流、农业、航天、乡村水系等让发展可持续',
                 '表达公式：协作机制 -> 县域抓手 -> 产业支撑 -> 公共服务 -> 群众增收'],
     'support_article_ids': ['people_daily_20260616_30163264',
                             'people_daily_20260617_30163463',
                             'people_daily_20260618_30163720',
                             'people_daily_20260621_30164022',
                             'people_daily_20260619_30163838',
                             'people_daily_20260621_30164041',
                             'people_daily_20260621_30164045']},
    {'idea_id': 'idea_20260615_21_achievement_feedback_loop',
     'date': '2026-06-15',
     'priority': 'A',
     'status': '备选',
     'platform': '公众号 + 课堂讲解',
     'title': '正确政绩观续写：让群众看到变化，靠考核、决策和旧账闭环',
     'angle': '这周政绩观素材的重点不是再讲口号，而是把群众感受、考核指挥棒、决策责任、新官理旧账接成闭环。',
     'outline': ['群众检验：让群众看见变化、得到实惠',
                 '反面警示：公开通报政绩观偏差典型案件',
                 '制度校准：考核之变促实干担当，决策责任沉甸甸',
                 '办理闭环：理旧账、新官理旧账、诉求有着落',
                 '考场公式：群众评价 -> 问题建账 -> 决策负责 -> 考核纠偏 -> 长效治理'],
     'support_article_ids': ['people_daily_20260615_30163053',
                             'people_daily_20260616_30163289',
                             'people_daily_20260616_30163225',
                             'people_daily_20260616_30163226',
                             'people_daily_20260617_30163385',
                             'people_daily_20260617_30163387',
                             'people_daily_20260616_30163292']},
    {'idea_id': 'idea_20260615_21_city_hidden_work',
     'date': '2026-06-15',
     'priority': 'A',
     'status': '备选',
     'platform': '公众号 + 小红书',
     'title': '城市治理别只看“面子”：地下管网、适儿化空间和安全监管才是里子',
     'angle': '城市治理的高分写法，要从看得见的景观转向看不见的管网、安全、儿童友好和公共设施细节。',
     'outline': ['地下里子：管网强筋健骨，排水设施改善',
                 '安全里子：老头乐监管、道路限高、城市污水资源化',
                 '儿童里子：适儿化空间体现城市公共服务温度',
                 '协同里子：城际通勤、乡村水系和群众监督让治理可持续'],
     'support_article_ids': ['people_daily_20260615_30163061',
                             'people_daily_20260621_30164032',
                             'people_daily_20260615_30163099',
                             'people_daily_20260615_30163041',
                             'people_daily_20260621_30164045',
                             'people_daily_20260615_30163100',
                             'people_daily_20260615_30163101',
                             'people_daily_20260616_30163312']},
    {'idea_id': 'idea_20260615_21_culture_life_world',
     'date': '2026-06-15',
     'priority': 'A',
     'status': '备选',
     'platform': '公众号 + 小红书',
     'title': '文化传承新写法：既要守住根脉，也要走进生活、走向世界',
     'angle': '本周文化素材从国风审美、文物建档、文化出海、工业遗址、数字石窟共同说明：文化传承要保护、转译、体验、传播一起做。',
     'outline': ['保护：流失文物建档、遗产系统保护、田野课堂释读',
                 '转译：国风出海和东方美形成世界表达',
                 '体验：工业遗址、石窟数字展陈、县里小戏进入生活',
                 '传播：从本土记忆到国际叙事，文化更有世界范'],
     'support_article_ids': ['people_daily_20260615_30163085',
                             'people_daily_20260617_30163392',
                             'people_daily_20260617_30163393',
                             'people_daily_20260617_30163359',
                             'people_daily_20260618_30163713',
                             'people_daily_20260618_30163714',
                             'people_daily_20260618_30163715',
                             'people_daily_20260621_30164048',
                             'people_daily_20260621_30164051',
                             'people_daily_20260616_30163293']},
    {'idea_id': 'idea_20260615_21_ecology_asset_income',
     'date': '2026-06-15',
     'priority': 'B',
     'status': '备选',
     'platform': '公众号 + 课堂讲解',
     'title': '绿色发展别停在“环境变好”：生态资源要变资产、变产业、变收入',
     'angle': '绿色发展要写出从保护到转化的闭环：林下经济、碳汇交易、循环经济、防沙治沙、绿色生活共同把生态价值变成发展价值。',
     'outline': ['生态资产：公益林碳汇把保护价值货币化',
                 '生态产业：林下经济让林地从低效闲置变高效资产',
                 '循环利用：废旧电池再生形成资源闭环',
                 '全民参与：绿色生活、防沙治沙、乡村水系治理形成共同治理'],
     'support_article_ids': ['people_daily_20260620_30163953',
                             'people_daily_20260620_30163954',
                             'people_daily_20260616_30163319',
                             'people_daily_20260617_30163443',
                             'people_daily_20260617_30163372',
                             'people_daily_20260617_30163373',
                             'people_daily_20260617_30163397',
                             'people_daily_20260621_30164045',
                             'people_daily_20260616_30163317']},
    {'idea_id': 'idea_20260615_21_employment_priority_people',
     'date': '2026-06-15',
     'priority': 'A',
     'status': '备选',
     'platform': '公众号 + 面试题卡',
     'title': '就业优先战略升级：不是只保岗位，而是投资于人、匹配到岗、产业带岗',
     'angle': '《实施就业优先战略“十五五”规划》把就业题从稳岗扩容升级为投资于人、人岗匹配、产业协同和权益保障。',
     'outline': ['政策底座：就业优先战略“十五五”规划明确目标任务',
                 '投资于人：教育、技能、人才需求匹配度提升',
                 '产业带岗：服务业、物流、钢铁智能化和高端装备创造岗位',
                 '权益兜底：新就业形态健康发展和劳动者权益保障'],
     'support_article_ids': ['people_daily_20260618_30163726',
                             'people_daily_20260621_30164030',
                             'people_daily_20260621_30164031',
                             'people_daily_20260617_30163384',
                             'people_daily_20260616_30163258',
                             'people_daily_20260619_30163844',
                             'people_daily_20260618_30163743']},
    {'idea_id': 'idea_20260615_21_rule_based_governance',
     'date': '2026-06-15',
     'priority': 'B',
     'status': '备选',
     'platform': '公众号 + 课堂讲解',
     'title': '治理高效能怎么写：小快灵立法、法治营商和精准反诈一起发力',
     'angle': '治理现代化不是只靠运动式整治，而是用规则供给、专业调解、法治营商和精准防控提升治理效能。',
     'outline': ['规则供给：地方立法小快灵回应治理难题',
                 '营商环境：世界超市靠共享法庭、调解仲裁和司法服务护航',
                 '风险治理：反诈从心理防线、平台责任、技术防控一起补短板',
                 '作风治理：办事不出园、任性用权整治体现服务型政府'],
     'support_article_ids': ['people_daily_20260618_30163702',
                             'people_daily_20260618_30163706',
                             'people_daily_20260618_30163707',
                             'people_daily_20260616_30163310',
                             'people_daily_20260616_30163309',
                             'people_daily_20260616_30163311',
                             'people_daily_20260616_30163301']},
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
    existing_by_id = {row["idea_id"]: row for row in conn.execute("SELECT * FROM content_ideas")}
    conn.execute("DELETE FROM content_ideas")
    for idea in REFINED_IDEAS:
        support_ids = list(dict.fromkeys(idea["support_article_ids"]))
        existing = existing_by_id.get(idea["idea_id"])
        status = existing["status"] if existing else idea["status"]
        priority = existing["priority"] if existing and existing["priority"] in {"S", "A", "B", "C"} else idea["priority"]
        created_at = existing["created_at"] if existing else now
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
                status,
                priority,
                created_at,
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
