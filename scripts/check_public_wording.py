#!/usr/bin/env python3
"""Preflight public-facing Markdown for configured wording risks."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    term: str
    level: str
    advice: str


BLOCK_RULES = (
    Rule("习近平", "必须改写", "非必要不写；按事实改为‘有关重要论述’或改用其他来源"),
    Rule("中共中央", "必须改写", "按事实改为‘中央有关部署’‘相关文件’或改用其他来源"),
    Rule("党中央", "必须改写", "按事实改为‘中央有关部署’或‘有关方面’"),
    Rule("中央政治局", "必须改写", "改用不造成身份或效力误认的概括表达"),
    Rule("中共中央办公厅", "必须改写", "改用其他公开来源，或在不影响事实时概括为‘有关方面’"),
    Rule("中央宣传部", "必须改写", "非必要不写机构全称；必要时交由人工判断"),
    Rule("中央网信办", "必须改写", "非必要不写机构简称；必要时交由人工判断"),
    Rule("官方指定", "必须改写", "无可核验授权不得使用，改写为具体来源和事实"),
    Rule("官方唯一", "必须改写", "删除唯一性或提供真实授权与证据后人工复核"),
    Rule("内部消息", "必须改写", "改用可追溯公开来源"),
    Rule("内部渠道", "必须改写", "改用可追溯公开来源"),
    Rule("独家授权", "必须改写", "仅在有真实授权证明时保留并人工复核"),
    Rule("包过", "必须改写", "不得承诺考试结果"),
    Rule("保过", "必须改写", "不得承诺考试结果"),
    Rule("必过", "必须改写", "不得承诺考试结果"),
    Rule("保证上岸", "必须改写", "改为可核验的教学帮助，不承诺结果"),
    Rule("提分保证", "必须改写", "改为课程内容或适用题型说明"),
    Rule("精准押题", "必须改写", "改为基于公开材料的趋势分析"),
    Rule("押中原题", "必须改写", "不得暗示掌握考试原题"),
    Rule("泄题", "必须改写", "不得传播或暗示掌握非公开试题"),
    Rule("命题人透露", "必须改写", "删除无法核验的身份和来源"),
    Rule("命题组参与", "必须改写", "不得暗示考试机构或命题人员参与"),
    Rule("内部资料", "必须改写", "改为‘依据公开材料整理’"),
    Rule("内部题库", "必须改写", "改为‘基于公开材料整理的题库’"),
    Rule("稳赚不赔", "必须改写", "不得承诺投资结果"),
    Rule("保本保收益", "必须改写", "不得明示或暗示保本、无风险或保收益"),
    Rule("保证收益", "必须改写", "改为风险边界和事实说明"),
    Rule("零风险投资", "必须改写", "不得使用无风险承诺"),
    Rule("药到病除", "必须改写", "不得作医疗效果保证"),
    Rule("无副作用", "必须改写", "不得作绝对化医疗安全承诺"),
    Rule("百分百有效", "必须改写", "不得作绝对化效果保证"),
)

REVIEW_RULES = (
    Rule("国家级", "语境复核", "法定名称可保留；宣传性表述需核验"),
    Rule("最高级", "语境复核", "避免无依据的绝对化比较"),
    Rule("最佳", "语境复核", "改为具体事实、范围或评价来源"),
    Rule("顶级", "语境复核", "改为可核验的专业能力或具体指标"),
    Rule("全网第一", "语境复核", "删除无证据排名"),
    Rule("行业第一", "语境复核", "提供可核验统计口径，否则删除"),
    Rule("全国第一", "语境复核", "提供可核验统计口径，否则删除"),
    Rule("唯一", "语境复核", "核验是否确有排他性事实依据"),
    Rule("史上最", "语境复核", "避免夸张标题"),
    Rule("永久", "语境复核", "说明适用期限和条件"),
    Rule("绝对", "语境复核", "改为有限定、可验证的表述"),
    Rule("百分之百", "语境复核", "核验数据口径，避免效果保证"),
    Rule("100%", "语境复核", "核验数据口径，避免效果保证"),
    Rule("万能", "语境复核", "避免夸大适用范围"),
    Rule("零风险", "语境复核", "说明真实风险和适用边界"),
    Rule("权威认证", "语境复核", "列明认证主体和依据，否则删除"),
    Rule("权威推荐", "语境复核", "列明推荐主体和依据，否则删除"),
    Rule("国家认可", "语境复核", "列明具体制度依据，否则删除"),
    Rule("指定教材", "语境复核", "核验指定主体和正式文件"),
    Rule("唯一标准答案", "语境复核", "改为参考框架或一种作答路径"),
    Rule("根治", "语境复核", "医疗语境不得作保证；治理语境也应避免绝对化"),
    Rule("治愈", "语境复核", "医疗语境须有专业依据并说明适用范围"),
    Rule("突发", "语境复核", "仅用于确有时效性且已核验的突发事实"),
    Rule("刚刚", "语境复核", "核验发布时间，避免制造虚假时效"),
    Rule("重磅", "语境复核", "改为具体政策变化或读者收益"),
    Rule("定了", "语境复核", "核验文件是否正式发布并生效"),
    Rule("彻底", "语境复核", "避免把阶段性结果写成终局结论"),
    Rule("一文看懂", "语境复核", "确认文章确实覆盖必要边界，否则改题"),
    Rule("不看后悔", "语境复核", "删除诱导点击表达"),
)


def public_text(markdown: str) -> str:
    """Remove non-published metadata while preserving visible reference labels."""
    text = markdown.lstrip("\ufeff")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            frontmatter = text[: end + 5]
            text = "\n" * frontmatter.count("\n") + text[end + 5 :]
    text = re.sub(
        r"<!--.*?-->",
        lambda match: "\n" * match.group(0).count("\n"),
        text,
        flags=re.DOTALL,
    )
    # Fenced content such as the public golden-sentence block remains visible;
    # remove only the fence markers, not their contents.
    text = re.sub(r"^```.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(!?\[[^\]]*\])\([^)]*\)", r"\1", text)
    return text


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def term_pattern(rule: Rule) -> str:
    if rule.term == "定了":
        # Review clickbait such as “这事定了”, but not ordinary words such as
        # “决定了”“议定了”“确定了”“制定了”.
        return r"(?<![决议商确拟制审认判])定了"
    return re.escape(rule.term)


def scan(path: Path) -> tuple[list[tuple[Rule, int]], list[tuple[Rule, int]]]:
    text = public_text(path.read_text(encoding="utf-8"))
    blocked: list[tuple[Rule, int]] = []
    review: list[tuple[Rule, int]] = []
    blocked_spans: list[tuple[int, int]] = []
    for rule in sorted(BLOCK_RULES, key=lambda item: len(item.term), reverse=True):
        for match in re.finditer(term_pattern(rule), text):
            span = match.span()
            if any(span[0] < end and start < span[1] for start, end in blocked_spans):
                continue
            blocked.append((rule, line_number(text, match.start())))
            blocked_spans.append(span)
    for rule in sorted(REVIEW_RULES, key=lambda item: len(item.term), reverse=True):
        for match in re.finditer(term_pattern(rule), text):
            span = match.span()
            if any(span[0] < end and start < span[1] for start, end in blocked_spans):
                continue
            review.append((rule, line_number(text, match.start())))
    return blocked, review


def main() -> int:
    parser = argparse.ArgumentParser(description="检查公开稿中的项目规避词和语境风险词")
    parser.add_argument("paths", nargs="+", type=Path, help="待检查的 Markdown 文件")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="将语境复核词也视为未通过",
    )
    args = parser.parse_args()

    missing = [path for path in args.paths if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[文件不存在] {path}", file=sys.stderr)
        return 2

    total_blocked = 0
    total_review = 0
    for path in args.paths:
        blocked, review = scan(path)
        total_blocked += len(blocked)
        total_review += len(review)
        print(f"\n{path}")
        if not blocked and not review:
            print("  通过：未发现已配置的风险用语。")
            continue
        for rule, line in blocked:
            print(f"  [必须改写] 第{line}行：{rule.term}。建议：{rule.advice}")
        for rule, line in review:
            print(f"  [语境复核] 第{line}行：{rule.term}。建议：{rule.advice}")

    print(f"\n汇总：必须改写 {total_blocked} 处，语境复核 {total_review} 处。")
    if total_blocked or (args.strict and total_review):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
