#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate PPT for exam prep course"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Colors
RED_DARK = RGBColor(0xC0, 0x00, 0x00)
RED_MED = RGBColor(0xD4, 0x2A, 0x2A)
GOLD = RGBColor(0xC4, 0x9A, 0x2A)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY_DARK = RGBColor(0x33, 0x33, 0x33)
GRAY_MED = RGBColor(0x66, 0x66, 0x66)
GRAY_LIGHT = RGBColor(0xCC, 0xCC, 0xCC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x33, 0x99, 0x33)
CREAM = RGBColor(0xFF, 0xF8, 0xF0)
PINK = RGBColor(0xFF, 0xF5, 0xF5)
MINT = RGBColor(0xF5, 0xFF, 0xF5)
FN = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def set_bg(slide, color=WHITE):
    bg = slide.background; fill = bg.fill; fill.solid(); fill.fore_color.rgb = color

def add_tb(slide, l, t, w, h, text, fs=18, fc=BLACK, bold=False, align=PP_ALIGN.LEFT, fn=FN, ls=1.3):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text; p.font.size = Pt(fs)
    p.font.color.rgb = fc; p.font.bold = bold; p.font.name = fn; p.alignment = align
    p.space_after = Pt(0)
    if ls > 1: p.line_spacing = Pt(fs * ls)
    return tb

def add_ml(slide, l, t, w, h, lines, fs=18, fc=BLACK, bold=False, align=PP_ALIGN.LEFT, ls=1.5, fn=FN):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(lines):
        if isinstance(item, str):
            txt, s, c, b = item, fs, fc, bold
        else:
            txt, s, c, b = item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = txt; p.font.size = Pt(s); p.font.color.rgb = c
        p.font.bold = b; p.font.name = fn; p.alignment = align
        p.space_after = Pt(4); p.line_spacing = Pt(s * ls)
    return tb

def add_line(slide, l, t, w, h=0.04, color=RED_DARK):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    return s

def add_rect(slide, l, t, w, h, fill=WHITE, border=GRAY_LIGHT):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill; s.line.color.rgb = border; s.line.width = Pt(1)
    return s

def add_card(slide, l, t, w, h, title, body, ts=22, bs=20, tc=RED_DARK, bc=GRAY_DARK, bg=WHITE, bdr=GRAY_LIGHT):
    add_rect(slide, l, t, w, h, bg, bdr)
    add_tb(slide, l+0.2, t+0.15, w-0.4, 0.5, title, fs=ts, fc=tc, bold=True)
    add_line(slide, l+0.2, t+0.6, w-0.4, 0.02, GOLD)
    add_ml(slide, l+0.2, t+0.7, w-0.4, h-0.9, body, fs=bs, fc=bc, ls=1.4)

def header(slide, title, sub=''):
    add_line(slide, 0.6, 0.5, 12.1, 0.06, RED_DARK)
    add_tb(slide, 0.6, 0.6, 10, 0.7, title, fs=32, fc=RED_DARK, bold=True)
    if sub: add_tb(slide, 0.6, 1.25, 10, 0.5, sub, fs=18, fc=GRAY_MED)
    add_line(slide, 0.6, 1.55, 1.5, 0.03, GOLD)

def pg(slide, n):
    add_tb(slide, 12.2, 7.0, 1, 0.4, f'{n}/28', fs=12, fc=GRAY_MED, align=PP_ALIGN.RIGHT)

# ==================== Slide 1 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
add_line(s, 0, 0, 13.333, 0.08, RED_DARK)
add_line(s, 0, 7.42, 13.333, 0.08, RED_DARK)
add_line(s, 0.6, 2.8, 12.1, 0.03, GOLD)
add_tb(s, 1, 3.0, 11.3, 1.2, '十五五规划热点精讲', fs=52, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
add_tb(s, 1, 4.1, 11.3, 0.8, '考场能用 \u00b7 能写 \u00b7 能拿分', fs=30, fc=GOLD, bold=True, align=PP_ALIGN.CENTER)
add_line(s, 0.6, 4.8, 12.1, 0.03, GOLD)
add_tb(s, 1, 5.2, 11.3, 0.5, '7个关键词  \u00d7  5类题型  \u00d7  考场表达', fs=22, fc=GRAY_DARK, align=PP_ALIGN.CENTER)
add_tb(s, 1, 6.2, 11.3, 0.5, '国考申论 \u00b7 90分钟精讲课', fs=18, fc=GRAY_MED, align=PP_ALIGN.CENTER)
pg(s, 1)

# ==================== Slide 2 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '你是不是也这样写？')
add_ml(s, 1.2, 2.2, 11, 3.5, [
    ('①  「扩大内需」只会写四个字，后面写不下去了', 24, GRAY_DARK, False),
    ('②  「举国体制」以为就是计划经济回来了', 24, GRAY_DARK, False),
    ('③  写对策永远「加强监管、完善制度」，像没写一样', 24, GRAY_DARK, False),
], ls=2.0)
add_tb(s, 1.2, 5.8, 10, 0.6, '👇  今天一个一个解决', fs=22, fc=RED_MED, bold=True)
pg(s, 2)

# ==================== Slide 3 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '❌ 阅卷老师最怕看到的答案')
add_ml(s, 1.2, 2.0, 11, 5, [
    ('❌  「要扩大内需，促进消费，拉动经济」', 22, RED_MED, True),
    ('空话套话，零信息量', 18, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('❌  「举国体制就是集中力量办大事」', 22, RED_MED, True),
    ('只说了旧版，没说「新」在哪', 18, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('❌  「要解决就业难问题，创造更多岗位」', 22, RED_MED, True),
    ('没分清总量矛盾和结构矛盾', 18, GRAY_MED, False),
], ls=1.4)
add_tb(s, 1.2, 6.5, 10, 0.5, '写了？写了。有用？没用。', fs=22, fc=RED_DARK, bold=True)
pg(s, 3)

# ==================== Slide 4 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '今天怎么学？')
add_tb(s, 1.0, 3.0, 11.3, 2, '听懂政策词  →  记住案例故事  →  看懂真题考法  →  学会考场表达  →  能写五类题型', fs=28, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER, ls=1.5)
add_tb(s, 1.2, 5.5, 10, 0.6, '五个环节，每个环节结束后你都能拿走一样东西', fs=20, fc=GRAY_MED, align=PP_ALIGN.CENTER)
pg(s, 4)

# ==================== Slide 5 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词①：战略基点', '内需不是「临时补药」，是「长期主引擎」')
add_card(s, 0.8, 2.0, 5.8, 4.5, '政策大白话',
    ['外面风浪大 → 出口靠不住',
     '必须靠国内14亿人的市场',
     '所以叫「战略」不叫「战术」',
     '',
     '权宜之计 = 战术（临时补课）',
     '长期依靠 = 战略（主引擎换挡）'], ts=22, bs=20)
add_card(s, 6.9, 2.0, 5.8, 4.5, '考场一句话',
    ['以国内大循环的确定性',
     '对冲外部环境的不确定性'],
    ts=22, bs=26, tc=GOLD, bc=RED_DARK, bg=CREAM)
pg(s, 5)

# ==================== Slide 6 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：140万亿的体量，14.1%的物流成本')
add_card(s, 0.8, 2.2, 5.8, 3.5, '📊 经济台阶',
    ['110万亿 → 120万亿 → 130万亿 → 140万亿',
     '连续跨越4个10万亿台阶'], ts=22, bs=22, bc=RED_DARK)
add_card(s, 6.9, 2.2, 5.8, 3.5, '📦 物流差距',
    ['中国物流成本占GDP：14.1%',
     '世界平均：10.7%',
     '差3.4个百分点 = 几万亿浪费在路上'], ts=22, bs=22, bc=RED_DARK)
add_tb(s, 0.8, 6.2, 11.7, 0.6, '3.4个百分点不是小数——这就是为什么统一大市场必须建', fs=20, fc=GOLD, bold=True)
pg(s, 6)

# ==================== Slide 7 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '已考：这些题都在考「内需」')
add_ml(s, 1.2, 2.2, 11, 4.5, [
    ('✅ 2025副省级Q2：「不是产业，竟是产业」', 22, GRAY_DARK, False),
    ('   城中村慢发展 = 消费场景培育', 18, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('✅ 2025副省级Q3：老粮仓改造', 22, GRAY_DARK, False),
    ('   存量空间+多元业态 = 业态融合', 18, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('✅ 2026市地级Q2：果莲「三效共生」', 22, GRAY_DARK, False),
    ('   经济+社会+生态三合一', 18, GRAY_MED, False),
], ls=1.3)
add_tb(s, 1.2, 6.2, 11, 0.6, '考的不是「请论述扩大内需的意义」，而是给你一个故事让你自己看出内需逻辑', fs=20, fc=RED_DARK, bold=True)
pg(s, 7)

# ==================== Slide 8 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '未来可能怎么考？', '五种考法，核心一句话：写出「为什么是战略」')
add_ml(s, 1.2, 2.2, 11, 4, [
    ('概括 │ 概括某地培育消费新增长点的主要做法', 20, GRAY_DARK, False),
    ('分析 │ 为什么说扩大内需是「战略基点」而非「权宜之计」？', 20, GRAY_DARK, False),
    ('应用文 │ 为某市「一刻钟便民生活圈」拟写工作方案', 20, GRAY_DARK, False),
    ('对策 │ 针对某地服务消费供给不足，提出改善建议', 20, GRAY_DARK, False),
    ('作文 │ 「以确定性对冲不确定性」', 20, RED_DARK, True),
], ls=1.6)
pg(s, 8)

# ==================== Slide 9 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词②：投资于人', '修路建桥是「投物」，教医社保是「投人」')
add_card(s, 0.8, 2.0, 5.8, 4.5, '政策大白话',
    ['以前：花钱修路建桥（投资于物）',
     '      人有钱不敢花',
     '',
     '现在：花钱投教育、医疗、社保（投资于人）',
     '      后顾之忧少了 → 敢消费了'], ts=22, bs=20)
add_card(s, 6.9, 2.0, 5.8, 4.5, '考场一句话',
    ['以民生保障的确定性',
     '释放消费意愿'],
    ts=22, bs=26, tc=GOLD, bc=RED_DARK, bg=CREAM)
pg(s, 9)

# ==================== Slide 10 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：1万个便民生活圈 = 1万个消费释放点')
add_card(s, 2.0, 2.2, 9.3, 4, '🎯 核心数据',
    ['2030年前建成1万个一刻钟便民生活圈',
     '',
     '补齐：养老 · 托育 · 便利店 · 早餐店',
     '',
     '逻辑链：保障到位 → 后顾之忧消除 → 消费释放'],
    ts=22, bs=22, bc=GRAY_DARK)
add_tb(s, 2.0, 6.5, 9.3, 0.5, '这不是做慈善，是释放消费力——做慈善和做经济的区别，考场要分清', fs=20, fc=RED_MED, bold=True)
pg(s, 10)

# ==================== Slide 11 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词③：业态融合', '1+1>2的「混搭经济学」')
add_card(s, 0.8, 2.0, 5.8, 4.5, '政策大白话',
    ['吃饭+看展+拍照一站搞定',
     '',
     '一个业态「引流」',
     '另一个业态「变现」',
     '1 + 1 > 2'], ts=22, bs=20)
add_card(s, 6.9, 2.0, 5.8, 4.5, '考场一句话',
    ['以跨界融合拓展消费场景',
     '引流业态带动盈利业态'],
    ts=22, bs=26, tc=GOLD, bc=RED_DARK, bg=CREAM)
pg(s, 11)

# ==================== Slide 12 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：体育赚流量，商业赚利润')
add_card(s, 0.8, 2.2, 5.8, 3.0, '🏟️ 苏超',
    ['赛事引流 → 周边商业变现'], ts=22, bs=22, bc=RED_DARK)
add_card(s, 6.9, 2.2, 5.8, 3.0, '🏭 老工厂+剧场+餐饮',
    ['工业遗产引流 → 文化消费变现'], ts=22, bs=22, bc=RED_DARK)
add_rect(s, 2.0, 5.5, 9.3, 1.0, CREAM, GOLD)
add_tb(s, 2.3, 5.6, 8.7, 0.8, '引流业态 + 变现业态 = 新增长点', fs=28, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
pg(s, 12)

# ==================== Slide 13 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '已考：业态融合的三种考法')
add_ml(s, 1.2, 2.5, 11, 3, [
    ('✅ 2025副省级Q3：老粮仓改造 → 展板文稿（应用文）', 22, GRAY_DARK, False),
    ('✅ 2026副省级Q3：天文小镇 → 短评（应用文）', 22, GRAY_DARK, False),
    ('✅ 2026市地级Q2：果莲三效共生 → 分析题（概括成效）', 22, GRAY_DARK, False),
], ls=2.0)
add_tb(s, 1.2, 5.8, 11, 0.8, '同一考点三种题型：概括考「看出了什么」，应用文考「怎么介绍」，分析考「为什么有效」', fs=20, fc=RED_DARK, bold=True)
pg(s, 13)

# ==================== Slide 14 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词④：统一大市场', '全国一个规矩，不是一个省一个规矩')
add_card(s, 0.8, 2.0, 5.8, 4.5, '政策大白话',
    ['外地企业进不来 = 地方保护',
     '物流多跑冤枉路 = 标准不统一',
     '',
     '不是「要不要统一」的问题',
     '是「不统一就亏几万亿」的问题'], ts=22, bs=20)
add_card(s, 6.9, 2.0, 5.8, 4.5, '考场：四统一',
    ['推进 ────────── 全国统一',
     '规则 · 标准 · 准入 · 信用'],
    ts=22, bs=26, tc=GOLD, bc=RED_DARK, bg=CREAM)
pg(s, 14)

# ==================== Slide 15 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：3.4个百分点的账 + 40%的硬指标')
add_card(s, 0.8, 2.2, 5.8, 3.5, '📦 物流成本',
    ['中国：14.1%  vs  世界：10.7%',
     '差3.4个百分点',
     '= 几万亿成本浪费在路上'], ts=22, bs=22, bc=RED_DARK)
add_card(s, 6.9, 2.2, 5.8, 3.5, '📋 硬指标',
    ['超400万工程采购项目',
     '至少预留40%给中小企业',
     '合同预付款比例提高到30%以上'], ts=22, bs=22, bc=RED_DARK)
add_tb(s, 0.8, 6.2, 11.7, 0.6, '只写「打破地方保护」四个字，和写「推进规则、标准、准入、信用全国统一」——差了十个专业度', fs=20, fc=RED_DARK, bold=True)
pg(s, 15)

# ==================== Slide 16 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词⑤：新型举国体制', '「新」在哪？三句话讲透')
add_ml(s, 1.2, 2.0, 7, 4.5, [
    ('🆚 旧版：国家出钱出人下指令（两弹一星模式）', 22, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('✨ 新版「三新」：', 24, RED_DARK, True),
    ('① 主体新 —— 企业成创新主力', 22, GRAY_DARK, False),
    ('② 机制新 —— 市场机制参与资源配置', 22, GRAY_DARK, False),
    ('③ 环境新 —— 宽容失败 + 长期支持', 22, GRAY_DARK, False),
], ls=1.4)
add_card(s, 8.5, 2.0, 4.2, 4.5, '考场一句话',
    ['政府搭台',
     '企业唱戏',
     '有形之手与无形之手',
     '合力突破卡脖子'],
    ts=20, bs=20, tc=GOLD, bc=RED_DARK, bg=CREAM)
pg(s, 16)

# ==================== Slide 17 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：芯片攻坚的三层合力')
add_card(s, 0.8, 2.0, 3.7, 3.5, '🏛️ 国家',
    ['大基金千亿投入', '定方向配资源'], ts=22, bs=20, bc=RED_DARK)
add_card(s, 4.8, 2.0, 3.7, 3.5, '🏭 企业',
    ['龙头牵头', '链主角色', '生态构建'], ts=22, bs=20, bc=RED_DARK)
add_card(s, 8.8, 2.0, 3.7, 3.5, '🔬 科学家',
    ['包干制：自主决定经费', '离岗创业：保留编制', '浙江「科学企业家」'], ts=22, bs=20, bc=RED_DARK)
add_tb(s, 0.8, 5.8, 11.7, 0.8, '国家搭台，企业唱戏，科学家「扩权」——三方合力，企业是主角', fs=22, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
pg(s, 17)

# ==================== Slide 18 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '已考：科技题的两种考法')
add_card(s, 0.8, 2.2, 5.8, 3.0, '概括题：五维度框架',
    ['组织 · 平台 · 硬件 · 资金 · 人才', '（2025行政执法Q1）'], ts=22, bs=20, bc=GRAY_DARK)
add_card(s, 6.9, 2.2, 5.8, 3.0, '分析题：先分类再讲关系',
    ['三条「黄河」：原型+数字+模型', '（2025副省级Q1）'], ts=22, bs=20, bc=GRAY_DARK)
add_tb(s, 0.8, 5.8, 11.7, 0.6, '概括题按五维度答不漏方向，分析题先分清各是什么再讲怎么协同', fs=20, fc=RED_DARK, bold=True)
pg(s, 18)

# ==================== Slide 19 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词⑥：结构性就业矛盾', '不是没岗位，是人岗对不上')
add_card(s, 0.8, 2.0, 5.8, 4.5, '矛盾拆解',
    ['「有人没活干」≠「没岗位」',
     '「有活没人干」= 技能不匹配',
     '',
     '三条路径：',
     '① 培训 —— 终身技能培训',
     '② 转观念 —— 学历让位给技能',
     '③ 创岗位 —— 新业态新职业'], ts=22, bs=20)
add_card(s, 6.9, 2.0, 5.8, 4.5, '考场一句话',
    ['以技能提升和供需对接', '破解结构性错配'],
    ts=22, bs=26, tc=GOLD, bc=RED_DARK, bg=CREAM)
pg(s, 19)

# ==================== Slide 20 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：十年前不存在的岗位，现在最缺人')
add_card(s, 0.8, 2.0, 5.8, 3.5, '🆕 新职业',
    ['AI训练师 · 数字孪生技术员', '无人机规划员 · 养老服务师', '汉服妆造师 · 机器人操作师'], ts=22, bs=20, bc=RED_DARK)
add_card(s, 6.9, 2.0, 5.8, 3.5, '🎓 一高一低',
    ['↑ 双一流扩招（高端科研人才）', '↓ 职业本科加强（高技能蓝领）', '', '长三角职业本科投档线', '超普通本科线100+分'], ts=22, bs=20, bc=RED_DARK)
add_tb(s, 0.8, 6.0, 11.7, 0.6, '学历正在让位给技能——这个趋势考场能写，写了就是亮点', fs=20, fc=RED_DARK, bold=True)
pg(s, 20)

# ==================== Slide 21 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '关键词⑦：巩固→破除→补强', '递进！不是并列！')
add_rect(s, 0.8, 2.3, 3.5, 2.5, PINK, RED_DARK)
add_tb(s, 1.0, 2.4, 3.1, 0.5, '① 巩固优势', fs=24, fc=RED_DARK, bold=True)
add_tb(s, 1.0, 2.9, 3.1, 1.5, '守住基本盘\n超大规模市场\n完整产业链', fs=18, fc=GRAY_DARK)
add_rect(s, 4.9, 2.3, 3.5, 2.5, CREAM, GOLD)
add_tb(s, 5.1, 2.4, 3.1, 0.5, '② 破除瓶颈', fs=24, fc=GOLD, bold=True)
add_tb(s, 5.1, 2.9, 3.1, 1.5, '攻克卡点\n核心技术攻坚\n场景创新', fs=18, fc=GRAY_DARK)
add_rect(s, 9.0, 2.3, 3.5, 2.5, MINT, GREEN)
add_tb(s, 9.2, 2.4, 3.1, 0.5, '③ 补强短板', fs=24, fc=GREEN, bold=True)
add_tb(s, 9.2, 2.9, 3.1, 1.5, '补齐弱项\n三农\n民生保障', fs=18, fc=GRAY_DARK)
add_tb(s, 4.0, 3.0, 1.2, 0.6, '→', fs=36, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
add_tb(s, 8.1, 3.0, 1.2, 0.6, '→', fs=36, fc=GOLD, bold=True, align=PP_ALIGN.CENTER)
add_tb(s, 0.8, 5.5, 11.7, 1.0, '⚠️  三步是递进关系，先守后攻！不是并列清单！', fs=26, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
pg(s, 21)

# ==================== Slide 22 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '案例：守住根基才能往上走，有了试验场才能往外推')
add_card(s, 0.8, 2.2, 5.8, 3.5, '🏭 巩固→突破：武钢',
    ['从「一炉铁」到8个全球首发产品', '', '没丢钢铁根基，往上长'], ts=22, bs=22, bc=RED_DARK)
add_card(s, 6.9, 2.2, 5.8, 3.5, '🚁 瓶颈→试验场：骆岗公园',
    ['合肥骆岗公园全空间无人体系', '', '给新技术真实场景试跑'], ts=22, bs=22, bc=RED_DARK)
add_tb(s, 0.8, 6.2, 11.7, 0.6, '武钢没丢基本盘所以能转型；骆岗给技术试验场所以能推广', fs=20, fc=RED_DARK, bold=True)
pg(s, 22)

# ==================== Slide 23 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '已考：方法论作文是副省级「保留节目」')
add_ml(s, 1.2, 2.2, 11, 4, [
    ('✅ 2026副省级Q5：', 22, GRAY_DARK, True),
    ('「运用合适的章法处理好不同因素之间的关系」', 22, RED_DARK, False),
    ('→ 可直套「巩固·破除·补强」框架', 20, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('✅ 2025副省级Q5：', 22, GRAY_DARK, True),
    ('「劣势在特定条件下可转化为优势」', 22, RED_DARK, False),
    ('→ 可套「巩固优势→破除瓶颈」辩证表达', 20, GRAY_MED, False),
], ls=1.3)
add_tb(s, 1.2, 6.2, 11, 0.6, '方法论作文每年都考，换个壳子而已——「巩固·破除·补强」框架考场直接用', fs=20, fc=RED_DARK, bold=True)
pg(s, 23)

# ==================== Slide 24 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '考场作文：三层递进框架')
add_rect(s, 1.5, 2.0, 10.3, 1.3, PINK, RED_DARK)
add_tb(s, 1.8, 2.1, 9.7, 1.1, '第一段·巩固优势\n守住基本盘：超大规模市场+完整产业体系 = 确定性底盘', fs=20, fc=RED_DARK)
add_rect(s, 1.5, 3.5, 10.3, 1.3, CREAM, GOLD)
add_tb(s, 1.8, 3.6, 9.7, 1.1, '第二段·破除瓶颈\n攻克卡点：核心技术攻坚+场景创新 = 突破动力', fs=20, fc=GOLD)
add_rect(s, 1.5, 5.0, 10.3, 1.3, MINT, GREEN)
add_tb(s, 1.8, 5.1, 9.7, 1.1, '第三段·补强短板\n补齐弱项：三农民生保障 = 发展温度', fs=20, fc=GREEN)
add_tb(s, 1.5, 6.5, 10.3, 0.6, '金句收束：「以确定性的绿洲，穿越不确定的风沙」', fs=22, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
pg(s, 24)

# ==================== Slide 25 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '考场表达速查卡', '7个关键词 × 替换表达')
rows_data = [
    ['关键词', '容易写空的地方', '替换成考场表达'],
    ['战略基点', '只写「要扩大内需」', '以确定性对冲不确定性'],
    ['投资于人', '写成「要重视人」太虚', '以民生保障释放消费意愿'],
    ['业态融合', '只写「促进消费」', '引流+变现，拓展消费场景'],
    ['统一大市场', '只写「打破地方保护」', '规则·标准·准入·信用四统一'],
    ['新型举国体制', '以为=计划经济', '政府搭台、企业唱戏'],
    ['结构性矛盾', '只写「就业难」', '技能提升+供需对接'],
    ['巩固·破除·补强', '写成「要全面发展」', '先守后攻，递进发力'],
]
tbl = s.shapes.add_table(len(rows_data), 3, Inches(0.8), Inches(2.0), Inches(11.7), Inches(4.5))
table = tbl.table
table.columns[0].width = Inches(2.8)
table.columns[1].width = Inches(4.5)
table.columns[2].width = Inches(4.4)
for i, row in enumerate(rows_data):
    for j, val in enumerate(row):
        cell = table.cell(i, j); cell.text = val
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(17); p.font.name = FN
            if i == 0:
                p.font.bold = True; p.font.color.rgb = WHITE; p.font.size = Pt(18)
            elif j == 2:
                p.font.color.rgb = RED_DARK; p.font.bold = True
            elif j == 1:
                p.font.color.rgb = GRAY_MED
            else:
                p.font.color.rgb = GRAY_DARK; p.font.bold = True
        if i == 0:
            cell.fill.solid(); cell.fill.fore_color.rgb = RED_DARK
add_tb(s, 0.8, 6.7, 11.7, 0.5, '📷 拍下来，考前翻一遍', fs=20, fc=GOLD, bold=True, align=PP_ALIGN.CENTER)
pg(s, 25)

# ==================== Slide 26 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '现在就练——3分钟写一段')
add_rect(s, 2.0, 2.2, 9.3, 3.0, CREAM, GOLD)
add_ml(s, 2.3, 2.3, 8.7, 2.8, [
    ('请用「投资于人」的逻辑，', 22, GRAY_DARK, False),
    ('为某市「促进社区消费」提出3条对策。', 22, GRAY_DARK, False),
    ('', 10, GRAY_MED, False),
    ('① 每条对策要有因果链', 20, GRAY_DARK, False),
    ('② 不能只写「要促进消费」', 20, GRAY_DARK, False),
    ('③ 时间3分钟', 20, RED_DARK, True),
], ls=1.4)
add_tb(s, 2.0, 5.8, 9.3, 0.6, '3分钟写完 → 挑两份读 → 自己感受差距', fs=22, fc=RED_DARK, bold=True, align=PP_ALIGN.CENTER)
pg(s, 26)

# ==================== Slide 27 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '一张图带走：7个关键词 + 7句话')
add_ml(s, 1.2, 2.0, 11, 5, [
    ('① 战略基点 → 「以确定性对冲不确定性」', 24, RED_DARK, True),
    ('② 投资于人 → 「以民生保障释放消费意愿」', 24, RED_DARK, True),
    ('③ 业态融合 → 「引流+变现，拓展消费场景」', 24, RED_DARK, True),
    ('④ 统一大市场 → 「规则·标准·准入·信用四统一」', 24, RED_DARK, True),
    ('⑤ 新型举国体制 → 「政府搭台、企业唱戏」', 24, RED_DARK, True),
    ('⑥ 结构性矛盾 → 「技能提升+供需对接」', 24, RED_DARK, True),
    ('⑦ 巩固·破除·补强 → 「先守后攻，递进发力」', 24, RED_DARK, True),
], ls=1.6)
add_tb(s, 1.2, 6.5, 11, 0.5, '7句话，考前背一遍，考场替换你原来的「大白话」', fs=22, fc=GOLD, bold=True, align=PP_ALIGN.CENTER)
pg(s, 27)

# ==================== Slide 28 ====================
s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s)
header(s, '课后必做')
add_ml(s, 1.5, 2.2, 10.3, 4.5, [
    ('① 用「巩固·破除·补强」框架，写一篇800字作文', 24, GRAY_DARK, False),
    ('   题目：「先守后攻：中国式现代化的方法论」', 22, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('② 做2026副省级Q5真题（「章法处理关系」）', 24, GRAY_DARK, False),
    ('   对照课堂框架自评', 22, GRAY_MED, False),
    ('', 10, GRAY_MED, False),
    ('③ 背诵7句考场表达，下周抽查', 24, RED_DARK, True),
], ls=1.3)
add_line(s, 0.6, 6.5, 12.1, 0.04, RED_DARK)
add_tb(s, 1.5, 6.7, 10.3, 0.5, '第一项必做 | 第二项强烈建议 | 第三项不背别来上课', fs=20, fc=RED_MED, bold=True, align=PP_ALIGN.CENTER)
pg(s, 28)

# Save
out = '/Users/pf.macbookpro/PeopleDailyMaterial/data/通过 AI 高效备课资料包/十五五规划热点精讲PPT.pptx'
prs.save(out)
print(f'OK: {out}')
