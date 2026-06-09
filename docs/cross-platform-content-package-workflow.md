---
type: cross_platform_content_package_workflow
updated: 2026-05-26
scope: PeopleDailyMaterial
owner_ai: Codex
---

# 人民日报跨平台内容出品流程

这份流程用于把一段时间内的人民日报文章，连续转成可检索的教研资产、可发布的公众号文章、可上课的 PPT、可发小红书的图片。

核心原则：

> **Codex 负责结构化和精确排版，imagegen 负责高质视觉素材，HTML/PPTX 负责最终成品。**

不要把整页 PPT、中文标题、正文表格直接交给图像模型生成。图像模型主要用于无文字背景、插画、纹理、抽象视觉；中文信息排版必须由 Markdown、HTML、PPTX 或可控代码完成。

## 一、总流程

以后处理一个日期段，默认走这条链路：

```text
人民日报原文
  ↓
日期段梳理
  ↓
结构化素材资产
  ↓
主题筛选
  ↓
公众号文章
  ↓
文章总目录中文归档
  ↓
视觉设计 brief
  ↓
公众号配图 + 小红书 3:4 配图 + PPT
  ↓
出品包归档
```

每一步都要留下可复用文件，不只在对话里给结论。

## 二、目录与命名

### 1. 日期段目录

单日处理：

```text
data/analysis/YYYY-MM-DD/
```

跨日期段处理：

```text
data/analysis/YYYY-MM-DD_to_YYYY-MM-DD/
```

### 2. 标准文件

每个日期段建议形成：

```text
data/analysis/<period>/
  <period>-material-assets.json
  <period>-material-assets-view.md
  <period>-theme-shortlist.md
  wechat-<topic-slug>.md
  wechat-<topic-slug>-illustrated.md
  deliverables/
    <topic-slug>/
      README.md
      visual-brief.md
      source-prompts.md
```

其中：

- `material-assets.json` 是结构化素材来源，可以导入 `data/core/material_assets.sqlite`。
- `material-assets-view.md` 是方便人阅读的视图。
- `theme-shortlist.md` 是选题池和优先级说明。
- `wechat-<topic-slug>.md` 是日期段目录里的过程稿，便于机器流程和出品包复用。
- `wechat-<topic-slug>-illustrated.md` 是日期段目录里的带配图过程稿。
- `deliverables/<topic-slug>/` 只保留文字型出品说明、视觉 brief、提示词、讲稿提示和媒体清单。
- 图片、PPTX、视频、音频等真实大文件统一放 `media/`，并在 `media/_index.md` 记录位置。

多媒体资产推荐位置：

```text
media/images/<period>-<topic-slug>-xhs/
media/images/<period>-<topic-slug>-wechat/
media/courseware/<period>-<topic-slug>-class/
```

### 3. 文章总目录

公众号文章和可发布成稿，要同时集中放入：

```text
data/articles/公众号文章/
```

命名规则：

```text
《中文标题》.md
《中文标题》（插图版）.md
```

这个目录是给老师人工查找、复用和二次编辑的成稿目录。日期段目录仍然保留，用来保存素材梳理、过程稿、视觉 brief、小红书文案和课件讲稿；图片、PPTX、视频、音频等大文件放入 `media/`。

## 三、第一步：日期段梳理

输入可以是：

```text
data/vault/YYYY/MM/YYYY-MM-DD/
data/vault/YYYY/MM/YYYY-MM-DD_to_YYYY-MM-DD/
```

如果是多个日期目录，就按日期顺序读取，不要只看标题。

梳理时先回答四个问题：

1. 这段时间人民日报共同指向哪些高频主题？
2. 哪些文章有完整的“问题-做法-成效-机制”？
3. 哪些材料适合申论、面试、公众号、小红书、PPT？
4. 哪些材料只是辅助信息，不适合深挖？

输出：

```text
<period>-material-assets.json
<period>-material-assets-view.md
```

如果已经生成结构化 JSON，要导入：

```bash
python3 scripts/import_material_assets.py data/analysis/<period>/<period>-material-assets.json
```

## 四、第二步：主题筛选

主题不是从大词里随便选，而是从素材支撑度里选。

每个候选主题至少写清楚：

- 主题名称
- 支撑文章
- 核心矛盾或读者痛点
- 申论价值
- 面试价值
- 公众号价值
- 小红书价值
- PPT 教学价值
- 推荐优先级

推荐评分标准：

| 维度 | 说明 |
|---|---|
| 人民日报支撑度 | 是否有 2 到 4 篇文章互相支撑 |
| 考试迁移度 | 能否转成申论框架或面试答题步骤 |
| 读者痛点 | 是否能解决考生常见空话、套话、不会展开的问题 |
| 视觉表达度 | 是否适合做成图解、罗盘、流程、结构图 |
| 连续输出度 | 是否能扩展成公众号、小红书、课程讲解 |

输出：

```text
<period>-theme-shortlist.md
```

## 五、第三步：写公众号文章

公众号文章仍按 `docs/codex-material-production-plan.md` 的写作框架执行。

额外要求：

1. 标题中优先出现“人民日报”。
2. 开头先打中考生痛点，不先写宏观背景。
3. 中段必须完成“案例 - 逻辑 - 考场转译”。
4. 结尾必须把材料上升为一种可复用能力。
5. 文末必须有 `## 参考文章`。
6. 定稿后必须放入 `data/articles/公众号文章/`，文件名使用中文标题；日期段目录可继续保留英文过程稿。

参考文章只列实际用到的人民日报材料，不把整段时间所有文章都塞进去。

## 六、第四步：视觉设计 brief

生成配图或 PPT 之前，必须先写视觉设计 brief，不直接开始画。

位置：

```text
data/analysis/<period>/deliverables/<topic-slug>/visual-brief.md
```

固定包含：

```markdown
# 视觉设计 brief

## 主题

## 受众

## 内容目标

## 视觉风格

## 色彩与质感

## 页面规格

## 必须表达的结构

## 禁止事项

## 各平台输出
```

默认视觉原则：

- 做课程、PPT、知识卡片时，优先生成可控的 HTML/PPTX 页面。
- 中文标题、正文、表格、引用、编号，必须由 HTML/PPTX 排版。
- imagegen 只负责无文字背景、插画、抽象视觉、质感素材。
- 如果使用 imagegen，尽量要求“无文字、留出标题区、不要水印、不要生成中文”。
- 如果是信息图、流程图、罗盘、结构图，优先用 HTML/SVG/canvas 或 PPTX 原生元素绘制。

## 七、第五步：配图规格

### 1. 公众号配图

默认规格：

```text
16:9
1920×1080
```

用途：

- 公众号头图
- 文中分段图
- PPT 可复用视觉页

建议目录：

```text
media/images/<period>-<topic-slug>-wechat/
```

### 2. 小红书配图

默认规格：

```text
3:4
1080×1440 或 1440×1920
```

这是竖版图，不再使用 4:3 横图。

用途：

- 小红书封面
- 小红书多图笔记
- 竖屏课程卡片

建议目录：

```text
media/images/<period>-<topic-slug>-xhs/
```

小红书图片默认 6 到 8 张：

1. 封面：冲突标题 + 人民日报来源感 + 核心收益。
2. 案例图：用一个人民日报案例抓住问题。
3. 框架图：把主题拆成 4 到 6 个动作。
4. 考场转译图：申论怎么写，面试怎么答。
5. 反面提醒图：不要怎么写，不要怎么误用。
6. 总结图：一句总公式或关键追问。

### 3. PPT

默认规格：

```text
16:9
课堂可直接讲授
```

建议目录：

```text
media/courseware/<period>-<topic-slug>-class/
```

PPT 默认包含：

1. 封面
2. 学员痛点
3. 人民日报案例
4. 核心框架
5. 申论转译
6. 面试示范
7. 课堂练习
8. 参考文章

## 八、视觉风格优先级

以后默认不要使用幼态卡通风。

优先使用以下风格：

### 1. 工程蓝图风

适合：

- 封面
- 系统框架
- 能力模型
- PPT 章节页

特征：

- 深蓝底或米白技术纸底。
- 网格、标尺、坐标线、结构标注。
- 分层结构、工程拆解、罗盘、流程箭头。
- 克制、高级、教学感强。

### 2. 技术制图风

适合：

- 公众号文中图
- 小红书知识卡片
- 申论/面试方法图

特征：

- 米白纸面、细线网格、边框、测量线。
- 手绘线稿与结构图结合。
- 少量强调色：深蓝、锈红、金色、青蓝。
- 画面像“把一个方法拆成工程图”。

### 3. HTML 精排风

适合：

- 需要大量中文文字的页面。
- 小红书卡片。
- PPT 信息页。

特征：

- 中文文字清晰。
- 版式可复用。
- 可以批量生成一组统一风格页面。

## 九、imagegen 使用边界

可以用 imagegen 的场景：

- 生成无文字背景图。
- 生成技术蓝图质感背景。
- 生成抽象城市治理、公共服务、数据网络、社区服务等视觉素材。
- 根据参考图生成风格相近的插画或视觉元素。

不建议用 imagegen 的场景：

- 直接生成带中文正文的整页 PPT。
- 直接生成小红书多图正文。
- 生成参考文献页、表格页、答题步骤页。
- 生成需要严格准确的中文标签。

推荐组合：

```text
imagegen：生成无文字背景或主体插画
HTML/PPTX：叠加中文标题、正文、标签、引用
Playwright：截图导出 PNG
Presentations：导出可编辑 PPTX
```

## 十、最终出品包检查清单

每次完成一个主题出品包后，检查：

- 是否有结构化素材 JSON 或可读视图。
- 是否有主题筛选记录。
- 公众号文章是否有参考文章。
- 中文标题成稿是否已经放入 `data/articles/公众号文章/`。
- 插图版公众号文章是否使用 16:9 图片。
- 小红书图片是否为 3:4 竖版。
- 小红书图片是否有配套发布文案。
- PPT 是否有课堂讲稿或讲解提示。
- 图片中是否避免让 AI 直接生成大段中文。
- 事实、数据、日期、版面是否和人民日报来源一致。
- 输出目录是否有 README。

## 十一、给 Codex 的默认口径

以后用户说“梳理一段时间的人民日报，并做成文章、配图、PPT、小红书”时，默认理解为：

1. 先读日期段文章。
2. 先生成结构化素材资产。
3. 再给主题 shortlist，而不是直接写文章。
4. 用户确定主题后，再写公众号文章。
5. 文章定稿后，先写视觉 brief。
6. 再生成公众号 16:9 配图、小红书 3:4 竖图、课堂 PPT。
7. 文字说明归档到 `data/analysis/<period>/deliverables/<topic-slug>/`，图片和课件归档到 `media/`。
8. 最后在 `media/_index.md` 补一行，记录本地位置、网盘位置和关联文本。

如果用户只要求其中一步，就只做那一步，但文件命名和规格仍按这份流程执行。
