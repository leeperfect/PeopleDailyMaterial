#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从人民日报 APP 评论库梳理官媒评论热点。

默认规则：同一事件/话题下，至少 3 个不同来源媒体发表评论，视为热点。
输出 Markdown 与 CSV，便于教学选题和后续人工复核。
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import jieba

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.article_identity import normalize_date
from modules.peopleapp_opinion import EXPORT_DIR, TIMEZONE, load_articles

HOTSPOT_DIR = EXPORT_DIR / "hotspots"

COLUMN_PREFIXES = [
    "人民锐评",
    "人民时评",
    "人民论坛",
    "今日谈",
    "钟声",
    "和音",
    "经济热点快评",
    "人民日报刊文",
    "夜读",
    "零时差",
]

STOPWORDS = {
    "人民日报",
    "人民日报客户端",
    "评论",
    "锐评",
    "刊文",
    "快评",
    "为何",
    "为什么",
    "如何",
    "不能",
    "不应",
    "就该",
    "没有",
    "不是",
    "一个",
    "一种",
    "这个",
    "这件事",
    "说开去",
    "总书记",
    "来之不易",
}

MERGE_PATTERNS = [
    ("停车计费规则", ["停车", "计费"]),
    ("教师减负", ["教师", "减负"]),
    ("高考志愿填报", ["高考", "志愿"]),
    ("开屏广告治理", ["开屏", "广告"]),
    ("研学治理", ["研学", "流量"]),
    ("算法与青年婚育观", ["算法", "婚育"]),
    ("营商环境", ["营商", "环境"]),
    ("粮食安全", ["粮食", "丰收"]),
]

# 以下规则来自对已下载正文的持续逐篇复核。
# 只使用事件或观点链中的辨识性短语，避免再用“中国”“消费者”“军事”等
# 泛词把互不相关的文章错误归并。
CURATED_TOPIC_RULES = [
    {
        "topic": "高考志愿填报治理",
        "category": "教育与青年成长",
        "angle": "从信息透明、AI辅助、家长责任和反招生诈骗四个层面，帮助考生把选择权握在自己手里。",
        "title_any": [
            "高考志愿填报",
            "高考志愿别被商业套路",
            "AI“改动”了你的高考志愿",
            "规范志愿填报市场",
            "打破功利焦虑，让专业选择",
            "高考公平需要延伸到志愿填报",
            "反招生诈骗",
        ],
    },
    {
        "topic": "教师减负落地",
        "category": "教育与青年成长",
        "angle": "教师减负不能停在文件和口号，要同步清理非教学任务、规范进校园事项并建立长效监督。",
        "title_any": ["教师减负"],
    },
    {
        "topic": "录取通知书回归育人本意",
        "category": "教育与青年成长",
        "angle": "录取通知书的价值不在豪华包装，而在信息准确、情感真挚和大学育人理念。",
        "title_any": ["录取通知书"],
    },
    {
        "topic": "研学回归教育与安全本位",
        "category": "教育与青年成长",
        "angle": "研学不能被打卡流量和冒险项目带偏，要把课程目标、风险评估和组织责任放在前面。",
        "title_any": ["研学"],
    },
    {
        "topic": "开屏广告与数字界面减负",
        "category": "数字治理与消费权益",
        "angle": "治理开屏广告不只是少看几秒广告，而是约束诱导触发、保障操作安全、把选择权还给用户。",
        "title_any": ["开屏广告", "开屏摇一摇", "导航软件追求收益"],
    },
    {
        "topic": "自动续费与隐性扣款治理",
        "category": "数字治理与消费权益",
        "angle": "平台应让开通与退出同样方便，以显著提示、便捷取消和责任追溯整治隐性扣款。",
        "title_any": ["自动续费", "开通仅一秒但退订"],
    },
    {
        "topic": "银发群体数字融入",
        "category": "数字治理与消费权益",
        "angle": "适老化不能只放大字体，还要同时解决信息骚扰、操作门槛、数字教育和安全防护。",
        "title_any": [
            "77万条未读",
            "应用适老化",
            "银发族抢着学AI",
            "数字适老化",
            "数字围猎",
            "弹窗广告困住老年",
            "手机弹窗“围猎”老人",
            "适老化，不能",
        ],
    },
    {
        "topic": "AI深度合成与人格权保护",
        "category": "数字治理与消费权益",
        "angle": "从AI偷声、换脸拟声到模型风险治理，重点是守住人格权、数据授权、平台责任和技术伦理边界。",
        "title_any": ["AI时代如何保护好声音", "别让AI偷走你的声音", "整治AI“换脸拟声”", "人工智能学会“使坏”", "人工智能“偷声”"],
    },
    {
        "topic": "AI应用风险与智能向善治理",
        "category": "数字治理与消费权益",
        "angle": "AI进入教育、投资、测评、文艺和安全场景后，治理重点是防诈骗、防滥用、守真实、明边界、促向善。",
        "title_any": [
            "AI时代的教育",
            "AI智能荐股",
            "AI荐股",
            "AI时代，我们还需要",
            "AI研学",
            "境外AI“后门”",
            "AI生成“种草”",
            "校准智能向善",
            "青年演员无戏可拍",
            "AI时代，为何还要翻字词典",
        ],
    },
    {
        "topic": "AI辅助决策与责任边界",
        "category": "数字治理与消费权益",
        "angle": "AI可以辅助判断，但不能代替专业审查和人的最终负责；要用风险提示、场景分级和责任追溯防止算法建议变成免责借口。",
        "title_any": ["人工智能不能成商家避责", "AI开药方毁了", "轻信AI被困野山"],
    },
    {
        "topic": "AI客服规范与人工服务兜底",
        "category": "数字治理与消费权益",
        "angle": "智能客服降本不能牺牲消费者体验，要畅通转人工渠道、明确答复效力，并为特殊和紧急场景保留人工兜底。",
        "title_any": ["为AI客服立规矩", "莫让AI客服给消费者"],
    },
    {
        "topic": "AI文艺创作与内容质量",
        "category": "文化建设与社会心态",
        "angle": "AI进入影视创作后，评价重点不能停在技术奇观，而要回到原创能力、真实表演、审美质量和人的主体性。",
        "title_any": ["AI剧攻破", "AI短剧，站在", "AI时代演员可", "AI短剧需降虚火", "AI剧上卫视", "AI短剧要跳出"],
    },
    {
        "topic": "AI仿冒名人与平台治理",
        "category": "数字治理与消费权益",
        "angle": "AI仿冒名人不是普通娱乐，要压实平台核验、显著标识和侵权处置责任，保护人格权益与内容信任。",
        "title_any": ["余华一月两次打假", "余华再次“打假”", "“假余华”泛滥"],
    },
    {
        "topic": "骑手“红灯停表”与算法向善",
        "category": "数字治理与消费权益",
        "angle": "把等红灯时间从配送考核中剔除只是起点，还要推动配送时限合理化、安全与效率平衡，让算法治理落到新就业群体权益保障上。",
        "title_any": ["红灯停表", "红灯“停表”", "等红灯不扣时", "等红灯不计入配送时间", "让骑手“等得起”"],
    },
    {
        "topic": "停车计费规则透明化",
        "category": "城市治理与公共服务",
        "angle": "停车收费要从模糊取整转向按规则精细计费，让小额公共服务也经得起公平检验。",
        "title_any": ["停车费叫停", "停车计费"],
    },
    {
        "topic": "新就业群体服务驿站提质",
        "category": "城市治理与公共服务",
        "angle": "服务驿站不能重建设轻使用，要跟着劳动者的时间、路线和真实需求调整服务。",
        "title_any": ["新就业群体服务驿站", "城市驿站遇冷", "快递小哥对一些驿站无感"],
    },
    {
        "topic": "正确政绩观与主动治理",
        "category": "城市治理与公共服务",
        "angle": "把为民造福落到实事求是、前置谋划、接诉即办、类案治理和小处着手的行动链。",
        "title_any": [
            "实干的三重意涵",
            "弘扬实事求是",
            "最终要落到为民造福",
            "较真书记",
            "谋在先、干在前",
            "发展的主动性从何而来",
            "正确政绩观",
            "接诉即办",
            "政绩观“近和远”",
            "政绩观中的“轻”与“重”",
            "硬政绩",
        ],
    },
    {
        "topic": "基层减负与治理效能",
        "category": "城市治理与公共服务",
        "angle": "基层减负要从压减报表催报、清理隐形负担入手，把干部的时间还给调查研究、科学决策和服务群众。",
        "title_any": ["“上午要，下午交”式催报", "填表留痕", "基层报表“瘦身”", "为基层减负莫忽视", "基层干部留些“踱方步”"],
    },
    {
        "topic": "政务热线诉求边界与公共资源",
        "category": "城市治理与公共服务",
        "angle": "既要防止奇葩诉求挤占公共资源，也不能轻率给群众贴上“滥用”标签，要靠分类受理、精准转办和耐心回应守住服务初心。",
        "title_any": ["月亮太亮影响睡觉", "月亮太亮”，政务热线", "慎言“12345滥用”"],
    },
    {
        "topic": "科学家登上城市C位",
        "category": "文化建设与社会心态",
        "angle": "把城市公共传播资源留给科学家，体现崇尚创新、尊重知识的价值导向，也要推动短期流量转化为稳定的科学文化建设。",
        "title_any": ["科学家成为闹市商圈C位", "科学家登上商圈大屏", "城市商圈何以将C位留给科学家", "将商圈“C位”留给科研先辈", "科学家登上城市“C位”"],
    },
    {
        "topic": "防汛救灾与涉灾谣言治理",
        "category": "公共安全与监管",
        "angle": "把防汛救灾写成风险预警、底线思维、基层落实、信息公开和网络辟谣共同发力的治理考题。",
        "title_any": [
            "打赢防汛救灾硬仗",
            "防灾救灾",
            "抗汛关头",
            "防汛减灾",
            "防住谣言",
            "灾情面前",
            "深刻汲取教训 抓实抓细落实",
            "谣言因汛而生",
            "无人机投入广西救援",
            "科技实力也是救援底气",
            "保生命安全 护百姓生计",
            "宁可十防九空",
            "手搓”防汛APP",
            "解放军来了",
            "担当如磐 众志成城",
        ],
    },
    {
        "topic": "灭火器纸面维保治理",
        "category": "公共安全与监管",
        "angle": "消防维保不能只贴合格证，要打通检测、维保、抽查和责任追究的真实闭环。",
        "title_any": ["灭火器“纸面维保”", "灭火器合格证"],
    },
    {
        "topic": "“甲醛白菜”与食品安全全链条监管",
        "category": "公共安全与监管",
        "angle": "从个案严查延伸到农产品流通全链条：补齐批发保鲜环节的监管盲区，警惕伪科普转移焦点，以常态化抽检和溯源问责根治顽疾。",
        "title_any": ["甲醛白菜", "白菜蘸甲醛", "甲醛伪科普", "甲醛"],
    },
    {
        "topic": "中国制造出海与创新竞争力",
        "category": "产业经济与开放发展",
        "angle": "从空调等避暑产品走红欧洲，看中国制造如何靠产业链、技术迭代和市场适配形成竞争力。",
        "title_any": ["避暑神器", "一台空调看欧洲"],
    },
    {
        "topic": "粮食安全与农业现代化",
        "category": "产业经济与开放发展",
        "angle": "把粮食安全从丰收表态推进到资源节约、科技赋能和农业全产业链建设。",
        "title_any": ["这个“重中之重”", "全年粮食丰收", "农业建成现代化大产业"],
    },
    {
        "topic": "营商环境与市场秩序",
        "category": "产业经济与开放发展",
        "angle": "营商环境既要对劳动者友好，也要规范涉企检查、畅通市场退出和资源再配置。",
        "title_any": ["打工友好", "市场“新陈代谢”", "涉企检查"],
    },
    {
        "topic": "机票退改签规则透明化",
        "category": "市场监管与消费权益",
        "angle": "机票退改签不能成为一笔糊涂账，要推动费用与实际损失相匹配，强化事前告知、平台责任和争议处理。",
        "title_any": ["退张机票不该如此艰难", "机票退费贵", "机票高额退票费"],
    },
    {
        "topic": "低价游乱象与旅游市场治理",
        "category": "市场监管与消费权益",
        "angle": "低价游反复回潮，根源在畸形利益链和监管碎片化；治理要穿透低价获客、强制购物、层层转包等环节。",
        "title_any": ["“低价游”又整幺蛾子", "“低价游”屡禁不止", "“低价团”为什么总是"],
    },
    {
        "topic": "流量逐利与虚假内容治理",
        "category": "网络生态与社会信任",
        "angle": "从卖惨摆拍、付费测评到流量祛魅，治理重点是压实平台责任并修复内容公信力。",
        "title_any": ["流量祛魅", "批量化卖惨营销", "又是摆拍", "谁给钱就夸谁", "摆拍“浸猪笼”", "带娃送外卖"],
    },
    {
        "topic": "舆情敲诈与网络黑产治理",
        "category": "网络生态与社会信任",
        "angle": "以“护剧”为名的恶评威胁和有偿删帖，本质是舆情敲诈；要靠依法惩治、平台风控和行业共治斩断黑色利益链。",
        "title_any": ["遇到“护剧”黑产", "假“护剧”", "以“护剧”之名", "舆情敲诈必须", "舆情敲诈黑手"],
    },
    {
        "topic": "偷拍工具与隐私安全治理",
        "category": "公共安全与监管",
        "angle": "偷拍设备不能以普通商品名义流通，要同时追究生产、销售、平台审核和非法使用责任，保护公共空间中的人格尊严与隐私安全。",
        "title_any": ["偷拍工具何以如此嚣张", "“偷拍手机壳”热销", "能偷拍竟成产品卖点"],
    },
    {
        "topic": "儿童网络保护与童年流量化治理",
        "category": "教育与青年成长",
        "angle": "儿童不是流量工具，治理要同时管住低质内容、算法投喂、家长监护失范和平台变现冲动。",
        "title_any": ["小孩身上榨流量", "伪童书", "孩子不是“流量提款机", "小朋友不该被算法投喂", "童真本“无价”", "晒娃"],
    },
    {
        "topic": "“预制娃”与教育焦虑治理",
        "category": "教育与青年成长",
        "angle": "把孩子提前塞进标准化成长脚本，看似规划未来，实则可能放大教育焦虑；要尊重成长规律、个体差异和自主选择。",
        "title_any": ["“预制娃”背后的", "“预制娃”一词火了", "别让“预制”消耗", "“预制娃”刷屏之后", "“预制大学”训练"],
    },
    {
        "topic": "未成年人模式与AI陪伴治理",
        "category": "教育与青年成长",
        "angle": "未成年人网络保护不能停在形式开关，还要治理沉迷设计和虚拟陪伴风险，补齐平台技术、内容审核与家庭引导责任。",
        "title_any": ["未成年人模式不能还是", "未成年人模式，岂能", "AI聊天搭子", "AI聊天？别让孩子"],
    },
    {
        "topic": "博物馆公共服务精细化",
        "category": "文化建设与社会心态",
        "angle": "面对持续升温的文博需求，博物馆既要优化预约和客流服务，也要守住内容审核、专业管理和公共教育底线。",
        "title_any": ["博物馆做好应对", "博物馆“非必要不预约”", "“文博热”直面大客流", "博物馆不能总让小朋友", "博物馆不妨引入“三审三校”"],
    },
    {
        "topic": "诋毁袁隆平与无底线流量",
        "category": "网络生态与社会信任",
        "angle": "农业科普不能沦为流量生意，要用事实核验、平台治理和依法追责守住公共认知底线。",
        "title_any": ["诋毁袁老成果", "诋毁袁隆平"],
    },
    {
        "topic": "世界杯中的体育精神与人文价值",
        "category": "体育文化与社会心态",
        "angle": "把赛场胜负延伸到尊重弱者、全球流动、文化多样性和昂扬精神等公共价值。",
        "title_any": ["世界杯", "伊朗队，昂着头告别世界杯", "小国弱旅", "CR7"],
    },
    {
        "topic": "文化遗产传承与公共创意边界",
        "category": "体育文化与社会心态",
        "angle": "从传统纹样、公共创意母题和网络表情包争议，看知识产权保护如何兼顾原创激励、文化传承和公共共享。",
        "title_any": ["LV“老花”", "一朵“老花”", "经典创意母题", "鸭血粉丝店", "表情包确权", "老祖宗的审美被抢注"],
    },
    {
        "topic": "理解中国发展与世界机遇",
        "category": "国际观察与中国叙事",
        "angle": "用制度优势、创新红利、市场竞争和历史纵深解释中国发展，而不是停留在抽象赞美。",
        "title_any": [
            "中国全球领导力",
            "“创新红利”",
            "“中国冲击2.0”",
            "“全球最硬核的健身房”",
            "中国发展的“制度密码”",
            "理解当代中国",
        ],
    },
    {
        "topic": "“好好吃饭”与中国和平叙事",
        "category": "国际观察与中国叙事",
        "angle": "一句朴素的生活表达成为最动人的反战宣言，展示以共情语言和生活细节传递中国和平立场的国际传播路径。",
        "title_any": ["好好吃饭"],
    },
    {
        "topic": "历史正义与日本军事化警示",
        "category": "国际观察与中国叙事",
        "angle": "从二战记忆、慰安妇史实和日本军事转轨出发，说明守护历史真相也是维护和平秩序。",
        "title_any": ["安保三文件", "守望历史正义", "慰安妇", "日本右翼"],
    },
]


def clean_title(title: str) -> str:
    text = str(title or "")
    for prefix in COLUMN_PREFIXES:
        text = re.sub(rf"^\s*{re.escape(prefix)}\s*[|｜：:丨-]?\s*", "", text)
    text = re.sub(r"[“”\"《》\[\]（）()]", "", text)
    return text.strip()


def normalize_source(source: str) -> str:
    text = str(source or "").strip()
    text = text.replace("微信公众号", "微信公号")
    return text or "未知来源"


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def pattern_anchor(article: Dict) -> str:
    text = compact_text(" ".join([article.get("title", ""), article.get("summary", ""), article.get("content", "")[:300]]))
    for label, words in MERGE_PATTERNS:
        if all(word in text for word in words):
            return label
    return ""


def tokens_for_article(article: Dict) -> Set[str]:
    title = clean_title(article.get("title", ""))
    base_text = f"{title} {article.get('summary', '')}"
    tokens: Set[str] = set()

    for token in jieba.lcut(base_text):
        token = token.strip()
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        if re.fullmatch(r"\d+", token):
            continue
        tokens.add(token)

    for keyword in article.get("keywords") or []:
        keyword = str(keyword).strip()
        if len(keyword) >= 2 and keyword not in STOPWORDS:
            tokens.add(keyword)

    title_words = [
        word
        for word in jieba.lcut(title)
        if len(word.strip()) >= 2 and word.strip() not in STOPWORDS and not re.fullmatch(r"\d+", word.strip())
    ]
    for left, right in zip(title_words, title_words[1:]):
        phrase = f"{left}{right}"
        if 4 <= len(phrase) <= 12:
            tokens.add(phrase)

    anchor = pattern_anchor(article)
    if anchor:
        tokens.add(anchor)
    return tokens


def similarity(left: Set[str], right: Set[str]) -> float:
    if not left or not right:
        return 0.0
    shared = left & right
    if not shared:
        return 0.0
    overlap = len(shared) / max(1, min(len(left), len(right)))
    strong_shared = any(len(token) >= 4 for token in shared)
    if strong_shared and len(shared) >= 1:
        return max(overlap, 0.35)
    return overlap


def build_clusters(articles: List[Dict], min_similarity: float) -> List[List[Dict]]:
    article_tokens = {article["article_id"]: tokens_for_article(article) for article in articles}
    parent = {article["article_id"]: article["article_id"] for article in articles}

    def find(article_id: str) -> str:
        while parent[article_id] != article_id:
            parent[article_id] = parent[parent[article_id]]
            article_id = parent[article_id]
        return article_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for index, left in enumerate(articles):
        for right in articles[index + 1 :]:
            left_id = left["article_id"]
            right_id = right["article_id"]
            left_anchor = pattern_anchor(left)
            right_anchor = pattern_anchor(right)
            if left_anchor and left_anchor == right_anchor:
                union(left_id, right_id)
                continue
            if similarity(article_tokens[left_id], article_tokens[right_id]) >= min_similarity:
                union(left_id, right_id)

    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for article in articles:
        grouped[find(article["article_id"])].append(article)

    return [group for group in grouped.values() if len(group) >= 2]


def representative_topic(group: List[Dict]) -> str:
    anchors = [pattern_anchor(article) for article in group]
    anchors = [anchor for anchor in anchors if anchor]
    if anchors:
        return max(set(anchors), key=anchors.count)

    token_counts: Dict[str, int] = defaultdict(int)
    for article in group:
        for token in tokens_for_article(article):
            token_counts[token] += 1
    candidates = [
        (token, count)
        for token, count in token_counts.items()
        if count >= 2 and len(token) >= 2 and token not in STOPWORDS
    ]
    if candidates:
        candidates.sort(key=lambda item: (-item[1], -len(item[0]), item[0]))
        return candidates[0][0]
    return clean_title(group[0].get("title", "未命名热点"))


def source_set(group: List[Dict]) -> Set[str]:
    return {normalize_source(article.get("source_name") or article.get("source")) for article in group}


def summarize_group(group: List[Dict]) -> Dict:
    group = sorted(group, key=lambda item: (item.get("date", ""), item.get("title", "")))
    sources = sorted(source_set(group))
    dates = [article.get("date", "") for article in group if article.get("date")]
    return {
        "topic": representative_topic(group),
        "media_count": len(sources),
        "article_count": len(group),
        "sources": sources,
        "start_date": min(dates) if dates else "",
        "end_date": max(dates) if dates else "",
        "articles": group,
    }


def canonical_title(title: str) -> str:
    text = clean_title(title)
    return re.sub(r"[\s“”\"《》|｜丨：:，,。！？!?·—\-]", "", text)


def deduplicate_reposts(group: List[Dict]) -> List[Dict]:
    """同来源、同标题的转载只保留正文更完整的一条。"""
    best: Dict[Tuple[str, str], Dict] = {}
    for article in group:
        key = (
            normalize_source(article.get("source_name") or article.get("source")),
            canonical_title(article.get("title", "")),
        )
        current = best.get(key)
        article_length = int(article.get("word_count") or len(article.get("content", "")))
        current_length = (
            int(current.get("word_count") or len(current.get("content", ""))) if current else -1
        )
        if current is None or article_length > current_length:
            best[key] = article
    return list(best.values())


def article_matches_rule(article: Dict, rule: Dict) -> bool:
    title = compact_text(article.get("title", ""))
    return any(compact_text(phrase) in title for phrase in rule["title_any"])


def has_usable_body(article: Dict) -> bool:
    """过短的跳转页或残缺正文不作为选题支撑文章。"""
    word_count = int(article.get("word_count") or 0)
    body_length = len(compact_text(article.get("content", "")))
    return max(word_count, body_length) >= 200


def build_curated_topics(articles: List[Dict]) -> List[Dict]:
    """按正文复核后的明确选题归并，未命中的素材不强行分类。"""
    topics = []
    for rule in CURATED_TOPIC_RULES:
        matched = [
            article
            for article in articles
            if has_usable_body(article) and article_matches_rule(article, rule)
        ]
        if len(matched) < 2:
            continue
        group = deduplicate_reposts(matched)
        if len(group) < 2:
            continue
        item = summarize_group(group)
        item["topic"] = rule["topic"]
        item["category"] = rule["category"]
        item["angle"] = rule["angle"]
        topics.append(item)
    return topics


def default_range(days: int) -> Tuple[str, str]:
    today = datetime.now(TIMEZONE).date()
    start = today - timedelta(days=max(1, days) - 1)
    return start.isoformat(), today.isoformat()


def select_articles(args) -> List[Dict]:
    if args.all:
        return load_articles(limit=args.limit)
    start = normalize_date(args.start) if args.start else None
    end = normalize_date(args.end) if args.end else None
    if not start and not end:
        start, end = default_range(args.days)
    return load_articles(start_date=start, end_date=end, limit=args.limit)


def write_markdown(hotspots: List[Dict], candidates: List[Dict], args) -> Path:
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    path = HOTSPOT_DIR / f"peopleapp_opinion_hotspots_{timestamp}.md"
    lines = [
        "# 人民日报 APP 评论库官媒热点梳理",
        "",
        f"- 生成时间：{datetime.now(TIMEZONE).isoformat(timespec='seconds')}",
        f"- 热点标准：至少 {args.min_media} 个不同来源媒体发表评论",
        "- 归并方式：已下载正文复核后的明确选题规则",
        f"- 热点数量：{len(hotspots)}",
        f"- 候选数量：{len(candidates)}",
        "",
    ]

    lines.extend(["## 已达热点标准", ""])
    if not hotspots:
        lines.append("本次范围内暂无达到标准的热点。")
        lines.append("")
    for index, item in enumerate(hotspots, 1):
        lines.extend(
            [
                f"### {index}. {item['topic']}",
                "",
                f"- 分类：{item['category']}",
                f"- 核心角度：{item['angle']}",
                f"- 时间：{item['start_date']} 至 {item['end_date']}",
                f"- 媒体数：{item['media_count']}",
                f"- 文章数：{item['article_count']}",
                f"- 来源：{'、'.join(item['sources'])}",
                "",
            ]
        )
        for article in item["articles"]:
            lines.append(
                f"- {article.get('date', '')}｜{normalize_source(article.get('source_name') or article.get('source'))}｜"
                f"[{article.get('title', '无标题')}]({article.get('source_url') or article.get('url') or ''})"
            )
        lines.append("")

    lines.extend(["## 候选热点", ""])
    if not candidates:
        lines.append("暂无候选热点。")
        lines.append("")
    for index, item in enumerate(candidates, 1):
        lines.extend(
            [
                f"### {index}. {item['topic']}",
                "",
                f"- 分类：{item['category']}",
                f"- 核心角度：{item['angle']}",
                f"- 时间：{item['start_date']} 至 {item['end_date']}",
                f"- 媒体数：{item['media_count']}",
                f"- 文章数：{item['article_count']}",
                f"- 来源：{'、'.join(item['sources'])}",
                "",
            ]
        )
        for article in item["articles"]:
            lines.append(
                f"- {article.get('date', '')}｜{normalize_source(article.get('source_name') or article.get('source'))}｜"
                f"{article.get('title', '无标题')}"
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_csv(items: List[Dict]) -> Path:
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    path = HOTSPOT_DIR / f"peopleapp_opinion_hotspots_{timestamp}.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "topic",
                "category",
                "angle",
                "status",
                "media_count",
                "article_count",
                "start_date",
                "end_date",
                "sources",
                "article_id",
                "date",
                "source",
                "title",
                "url",
            ]
        )
        for item in items:
            for article in item["articles"]:
                writer.writerow(
                    [
                        item["topic"],
                        item["category"],
                        item["angle"],
                        item["status"],
                        item["media_count"],
                        item["article_count"],
                        item["start_date"],
                        item["end_date"],
                        "、".join(item["sources"]),
                        article.get("article_id", ""),
                        article.get("date", ""),
                        normalize_source(article.get("source_name") or article.get("source")),
                        article.get("title", ""),
                        article.get("source_url") or article.get("url") or "",
                    ]
                )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="导出人民日报 APP 评论库官媒热点")
    parser.add_argument("--days", type=int, default=7, help="默认回看最近几天，默认 7 天")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--all", action="store_true", help="分析 APP 评论库全部文章")
    parser.add_argument("--limit", type=int, help="限制参与分析的文章数量")
    parser.add_argument("--min-media", type=int, default=3, help="热点至少需要几个不同媒体，默认 3")
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.22,
        help="兼容旧命令保留；当前使用正文复核规则，不再按相似度强行聚类",
    )
    args = parser.parse_args()

    articles = select_articles(args)
    clusters = build_curated_topics(articles)
    clusters.sort(key=lambda item: (-item["media_count"], -item["article_count"], item["topic"]))

    hotspots = [item for item in clusters if item["media_count"] >= args.min_media]
    candidates = [item for item in clusters if item["media_count"] < args.min_media]
    for item in hotspots:
        item["status"] = "hotspot"
    for item in candidates:
        item["status"] = "candidate"

    markdown_path = write_markdown(hotspots, candidates, args)
    csv_path = write_csv(hotspots + candidates)

    print("官媒评论热点梳理完成")
    print(f"参与文章：{len(articles)}")
    print(f"达到热点标准：{len(hotspots)}")
    print(f"候选热点：{len(candidates)}")
    print(f"Markdown：{markdown_path.relative_to(PROJECT_ROOT)}")
    print(f"CSV：{csv_path.relative_to(PROJECT_ROOT)}")
    if hotspots:
        print("\n已达热点标准：")
        for item in hotspots:
            print(f"- {item['topic']}：{item['media_count']} 家媒体，{item['article_count']} 篇")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
