# 微信公众号运营数据存放说明

这份说明用于固定公众号后台导出数据的存放方式，方便后续持续分析“什么文章和选题更容易获得阅读量”。

## 一、存放分层

公众号运营数据不混入人民日报原文库，统一放在一个便于老师直接查看的目录：

```text
data/data_analysis/
  overview.md
    连续汇总所有批次，比较本周与上周

  reports/
    每次导入后生成的详细运营数据分析报告

  raw/
    后台导出的原始 .xls，作为事实留存，不直接改动

  exports/
    从原始表拆出的 CSV，方便人工查看和临时核对
```

机器连续计算仍使用 `data/core/wechat_official_account.sqlite`，不需要老师日常打开。

## 二、核心分析库表

| 表 | 用途 |
|---|---|
| `import_batches` | 每次后台导入的批次、源文件和校验信息 |
| `daily_trends` | 每日阅读总量、分享、收藏、发文数量等趋势 |
| `channel_daily_reads` | 每日不同渠道的阅读人数，如公众号消息、朋友圈、推荐、搜一搜 |
| `source_overview` | 单篇文章在不同传播渠道下的阅读表现 |
| `ad_income_daily` | 流量主账号级每日收入：拉取、曝光、点击、eCPM、收入 |
| `ad_slot_daily` | 流量主分广告位每日收入（文章中部/底部、留言区、贴图推荐流） |
| `article_income` | 窗口内发表文章的归属收入（流量主“文章收入”页抓取，仅窗口内发表，留作交叉校验） |
| `article_income_daily` | 文章级收入主口径：API 逐日全历史（494 篇、2023 年起），含 slot_id/slot_name，按收入发生日归属，不受发表窗口限制 |
| `article_detail_30d` | 高阅读文章发表后 30 天明细：阅读、完读、涨粉、分享、渠道占比、每日趋势 |
| `user_growth_daily` | 每日新增关注、取消关注、净增、累计关注 |
| `monetization_imports` | 变现数据每次导入的文件、类型和行数记录 |
| `article_content_stats` | 预留：手工导出“全部文章内容分析”Excel 时使用；接口明细优先入 `article_detail_30d` |

分析单篇文章阅读量时，优先看 `source_overview.channel = '全部'` 的记录，避免把推荐、朋友圈、会话等渠道重复相加。

分析渠道贡献时，优先看 `channel_daily_reads`；其中 `全部` 是当日总阅读，不和其他渠道相加。

分析收入时三条口径互不换算：`ad_income_daily`（账号级，等于各广告位之和）、`ad_slot_daily`（广告位结构）、`article_income_daily`（文章归属，窗口口径约为账号级的 62%，其余后台未按文章归属）。

文章级收入一律用 `article_income_daily`（API 逐日）；`article_income`（页面抓取）只列出统计窗口内发表的文章，会漏掉窗口前发表文章的长尾收入，2026-09-07 曾因此把 3 篇高阅读文章误判为零收入，仅保留作交叉校验。

## 二之一、变现与用户增长数据的采集方式

变现与用户增长数据不从“数据趋势概况” Excel 进入，而是 2026-09-07 起经浏览器直接操作公众号后台补采，原始文件固定在：

```text
data/data_analysis/raw/monetization/
  ad_slot_daily/       分广告位每日收入 CSV（文件名带广告位后缀）
  article_income/      文章收入抓取结果
  content_api/         内容分析接口原始 JSON（文章清单、详情、渠道趋势、用户增长）
```

常用脚本：

| 脚本 | 用途 |
|---|---|
| `scripts/browser_driver.py` | 远程驾驶本机 Chrome（调试端口 9222），逐步操作后台、接管“导出”下载并自动入库 |
| `scripts/collect_wechat_mp_stats.py` | 半自动采集辅助：下载文件识别、归档、`inbox` 监听 |
| `scripts/import_wechat_monetization_stats.py` | 变现类 CSV 入库（账号级/广告位/文章收入/内容分析），重复导入覆盖不重复 |
| `scripts/collect_wechat_content_api.py` | 经后台内容分析接口拉取文章清单、单篇 30 天详情、渠道趋势 |
| `scripts/import_wechat_api_stats.py` | 接口 JSON 入库：写入 `article_detail_30d`、`user_growth_daily` 等 |

注意：流量主按广告位导出的 CSV 文件名完全相同且不含广告位列，入库时必须显式指定 `--kind ad_slot_daily --slot-name <广告位名>`，否则不同广告位数据会互相覆盖。2026-09-07 曾因此把“文章底部广告”文件误作账号级汇总入库，已更正并在批次报告第十七节留痕。

## 三、导入方式

下次拿到公众号后台导出的 `.xls` 后，运行：

```bash
python3 scripts/import_wechat_official_account_stats.py /path/to/wechat-export.xls
```

脚本会自动：

1. 把原始 `.xls` 复制到 `data/data_analysis/raw/`。
2. 把后台表拆成 CSV，放入 `data/data_analysis/exports/`。
3. 写入 `data/core/wechat_official_account.sqlite`。
4. 在 `data/data_analysis/reports/` 生成本批详细运营数据分析报告。
5. 更新 `data/data_analysis/overview.md`，自动与上一批比较。

## 四、连续分析方式

以后每周导入的数据不会孤立分析，而是按以下方式组成完整数据链：

1. 每份后台原表作为一个独立快照永久保留。
2. 最新快照与上一快照自动识别重叠日期和新增日期，避免把同一天重复累计。
3. 对同一篇文章比较两次快照，观察长尾净增长。
4. 对新出现的文章单独观察起量、推荐渠道和进入高阅读榜的速度。
5. 所有批次共同更新一份长期总览，用于观察滚动周期的账号整体变化。

公众号后台导出的“数据趋势概况”通常是滚动时间窗口，不一定只包含最近一周。因此，“本周新增”以最新批次比上一批多出的日期为准；两批重叠日期只用于核对，不重复计算。

## 五、后续分析口径

后续做选题复盘时，建议同时看三类指标：

- 阅读量：判断哪些标题和选题天然更吸引读者。
- 推荐占比：判断哪些内容更容易被平台推荐。
- 收藏、分享：判断哪些内容更有教学保存价值和社交传播价值。

这些运营指标要和 `content_ideas` 选题池、人民日报文章支撑材料一起看：阅读高不代表一定适合长期做，阅读一般但收藏和分享高的内容，也可能适合沉淀为申论或面试教学产品。
