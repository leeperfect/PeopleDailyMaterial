# 微信公众号运营数据存放说明

这份说明用于固定公众号后台导出数据的存放方式，方便后续持续分析“什么文章和选题更容易获得阅读量”。

## 一、存放分层

公众号运营数据不混入人民日报原文库，单独按以下四层保存：

```text
data/raw/wechat_official_account/
  后台导出的原始 .xls，作为事实留存，不直接改动

data/exports/wechat_official_account/
  从原始表拆出的 CSV，方便人工查看和临时核对

data/core/wechat_official_account.sqlite
  公众号运营核心分析库，供后续复盘、检索和选题判断使用

data/analysis/wechat-official-account/
  每次导入的说明、人工复盘和阶段性分析结论
```

## 二、核心分析库表

| 表 | 用途 |
|---|---|
| `import_batches` | 每次后台导入的批次、源文件和校验信息 |
| `daily_trends` | 每日阅读总量、分享、收藏、发文数量等趋势 |
| `channel_daily_reads` | 每日不同渠道的阅读人数，如公众号消息、朋友圈、推荐、搜一搜 |
| `source_overview` | 单篇文章在不同传播渠道下的阅读表现 |

分析单篇文章阅读量时，优先看 `source_overview.channel = '全部'` 的记录，避免把推荐、朋友圈、会话等渠道重复相加。

分析渠道贡献时，优先看 `channel_daily_reads`；其中 `全部` 是当日总阅读，不和其他渠道相加。

## 三、导入方式

下次拿到公众号后台导出的 `.xls` 后，运行：

```bash
python3 scripts/import_wechat_official_account_stats.py /path/to/wechat-export.xls
```

脚本会自动：

1. 把原始 `.xls` 复制到 `data/raw/wechat_official_account/`。
2. 把后台表拆成 CSV，放入 `data/exports/wechat_official_account/`。
3. 写入 `data/core/wechat_official_account.sqlite`。
4. 在 `data/analysis/wechat-official-account/` 生成导入记录。

## 四、后续分析口径

后续做选题复盘时，建议同时看三类指标：

- 阅读量：判断哪些标题和选题天然更吸引读者。
- 推荐占比：判断哪些内容更容易被平台推荐。
- 收藏、分享：判断哪些内容更有教学保存价值和社交传播价值。

这些运营指标要和 `content_ideas` 选题池、人民日报文章支撑材料一起看：阅读高不代表一定适合长期做，阅读一般但收藏和分享高的内容，也可能适合沉淀为申论或面试教学产品。
