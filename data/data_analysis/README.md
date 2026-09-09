# 自媒体运营数据

这里是自媒体运营资料的统一查看入口。目前主要保存微信公众号后台数据。

## 查看顺序

1. 先看 `overview.md`，了解账号长期变化和最近一批表现。
2. 再进入 `reports/`，查看每一期详细分析。
3. 需要核对后台事实时，查看 `raw/`。
4. 需要查看拆分后的表格时，查看 `exports/`。

## 目录说明

| 位置 | 用途 |
|---|---|
| `overview.md` | 连续汇总所有批次，比较本周与上周 |
| `reports/` | 每次导入后生成一份详细运营数据分析报告 |
| `raw/` | 公众号后台导出的原始 `.xls`，不直接修改 |
| `exports/` | 从原始表拆出的 CSV，方便查看和核对 |

## 固定工作方式

以后每次收到新数据后，都会同时完成：

1. 保存本批原始表。
2. 拆分并校验数据明细。
3. 与上一批识别重叠日期和新增日期。
4. 生成本批详细运营分析报告。
5. 更新长期运营数据总览。
6. 根据新文章、长尾文章、推荐渠道、分享和收藏表现提出选题建议。

## 变现与增长数据（文章收入 / 广告位 / 全部文章 / 用户增长）

这类数据按日期全局入库，与批次解耦，同一日期重复导入只覆盖不累加。

半自动采集（推荐）：打开后台后按终端清单逐页点"导出"，文件自动归档入库。

```bash
python3 scripts/collect_wechat_mp_stats.py
```

手工导入已有导出文件（可一次传多份，类型自动识别）：

```bash
python3 scripts/import_wechat_monetization_stats.py 文件1.csv 文件2.csv
```

入库位置：`data/core/wechat_official_account.sqlite`（ad_income_daily、ad_slot_daily、
article_income、article_content_stats、user_growth_daily 五张表）；
全量明细同步导出到 `exports/monetization/`，原始表归档到 `raw/monetization/`。
采集器登录态保存在 `.collector_profile/`（已加入 .gitignore，不进 GitHub）。
