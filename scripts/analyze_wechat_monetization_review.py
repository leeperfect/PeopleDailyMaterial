"""Recompute the September 8 review without changing source snapshots."""
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/data_analysis/exports/2026-09-08_review'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(f'file:{ROOT}/data/core/wechat_official_account.sqlite?mode=ro', uri=True)
    db.row_factory = sqlite3.Row

    def query(sql, args=()):
        return [dict(r) for r in db.execute(sql, args)]

    periods = []
    for label, start, end in [('前周', '2026-08-24', '2026-08-30'), ('本周', '2026-08-31', '2026-09-06'), ('最近30天', '2026-08-08', '2026-09-06'), ('连续91天', '2026-06-08', '2026-09-06')]:
        row = query('SELECT COUNT(*) days, SUM(income) income,SUM(impressions) impressions,SUM(ad_requests) requests,SUM(clicks) clicks FROM ad_income_daily WHERE date BETWEEN ? AND ?', (start, end))[0]
        row.update(query('SELECT SUM(new_followers) new_followers,SUM(unfollow_users) unfollows,SUM(net_followers) net_followers FROM user_growth_daily WHERE date BETWEEN ? AND ?', (start, end))[0])
        row.update(period=label, start=start, end=end)
        row['income'] = round(row['income'], 2)
        row['ecpm'] = 1000 * row['income'] / row['impressions']
        periods.append(row)
    prior, latest = periods[:2]
    exposure_effect = (latest['impressions'] - prior['impressions']) * (latest['ecpm'] + prior['ecpm']) / 2000
    price_effect = (latest['ecpm'] - prior['ecpm']) * (latest['impressions'] + prior['impressions']) / 2000
    assert abs(exposure_effect + price_effect - (latest['income'] - prior['income'])) < 1e-8
    ages = query('SELECT CAST(julianday(date)-julianday(send_date) AS INTEGER) age,COUNT(*) rows,ROUND(SUM(income),2) income FROM article_income_daily GROUP BY age ORDER BY age')
    articles = query("SELECT article_key,title,send_date,MIN(date) first_record,MAX(date) last_record,COUNT(DISTINCT date) recorded_days,ROUND(SUM(income),2) income,SUM(exposure) exposure FROM article_income_daily GROUP BY article_key,title,send_date ORDER BY income DESC,article_key")
    for row in articles:
        row['seven_day_mature'] = row['send_date'] <= '2026-08-31'
        row['observed_ecpm'] = 1000 * row['income'] / row['exposure'] if row['exposure'] else None
    details = query('SELECT msg_id,item_idx,title,publish_date,read_users,new_followers,completion_rate,share_users,collect_users FROM article_detail_30d ORDER BY publish_date,title')
    for row in details:
        row['thirty_day_mature'] = row['publish_date'] <= '2026-08-08'
        row['followers_per_1000_readers'] = 1000 * row['new_followers'] / row['read_users'] if row['read_users'] else None
        matches = [a for a in articles if a['send_date'] == row['publish_date'] and a['title'] == row['title']]
        row['income_match_count'] = len(matches)
        row['observed_first7_income'] = matches[0]['income'] if len(matches) == 1 else None
    slots = query("SELECT slot_name,ROUND(SUM(income),2) income,SUM(impressions) impressions FROM ad_slot_daily WHERE date BETWEEN '2026-06-08' AND '2026-09-06' GROUP BY slot_name ORDER BY income DESC")
    mismatches = query('SELECT a.date,a.income,SUM(s.income) slot_income FROM ad_income_daily a LEFT JOIN ad_slot_daily s ON s.date=a.date GROUP BY a.date HAVING ABS(a.income-SUM(s.income))>0.011 OR COUNT(s.date)=0')
    growth_errors = query('SELECT date FROM user_growth_daily WHERE new_followers-unfollow_users<>net_followers')
    growth_balance_errors = query('WITH t AS (SELECT *,LAG(cumulative_followers) OVER(ORDER BY date) prev FROM user_growth_daily) SELECT date FROM t WHERE prev IS NOT NULL AND cumulative_followers-prev<>net_followers')
    result = dict(as_of='2026-09-06',review_date='2026-09-08',periods=periods,ages=ages,slots=slots,articles=articles,details=details,checks=dict(slot_mismatches=mismatches,growth_errors=growth_errors,growth_balance_errors=growth_balance_errors),decomposition=dict(exposure_effect=exposure_effect,price_effect=price_effect))
    (OUT / 'review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    for name, rows in [('periods', periods), ('article_income_observed_first7', articles), ('content_first30', details), ('income_by_publication_age', ages)]:
        with (OUT / f'{name}.csv').open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({k: v for k, v in result.items() if k not in ('articles', 'details')}, ensure_ascii=False, indent=2))
    print('DETAILS', json.dumps(details, ensure_ascii=False))
    report_path = ROOT / 'data/data_analysis/reports/2026-09-08_monetization-topic-review.md'
    if report_path.exists():
        title = '公众号收入与选题复盘：2026年9月8日'
        blocks = [dict(id='title', type='markdown', body='# ' + title)]
        sections = report_path.read_text(encoding='utf-8').split('\n## ')[1:]
        for i, section in enumerate(sections):
            blocks.append(dict(id=f'section_{i}', type='markdown', body='## ' + section, layout='full'))
            if i in (2, 3, 4):
                blocks.append(dict(id=f'chart_block_{i}', type='chart', chartId={2:'weekly',3:'slots',4:'followers'}[i], layout='full'))
        mature = [r for r in details if r['thirty_day_mature']]
        mature.sort(key=lambda r: -r['followers_per_1000_readers'])
        leaders = [dict(row, topic=topic) for row, topic in zip(mature[:6], ['因地制宜与县域发展', '银发经济', '县域经济', '新就业群体', '就业难', '科技成果转化'])]
        sources = [dict(id='account', label='后台账号每日收入', query=dict(engine='SQLite', sql="SELECT date,income,impressions FROM ad_income_daily WHERE date BETWEEN '2026-08-24' AND '2026-09-06' ORDER BY date", description='每周求和；eCPM按总收入除以总曝光乘1000')), dict(id='slots', label='后台广告位明细', query=dict(engine='SQLite', sql="SELECT slot_name,SUM(income) income FROM ad_slot_daily WHERE date BETWEEN '2026-06-08' AND '2026-09-06' GROUP BY slot_name", description='91天收入，人民币元')), dict(id='content', label='后台22篇高阅读文章详情', query=dict(engine='SQLite', sql="SELECT title,publish_date,read_users,new_followers,1000.0*new_followers/read_users followers_per_1000_readers FROM article_detail_30d WHERE publish_date<='2026-08-08' ORDER BY followers_per_1000_readers DESC", description='仅满30天文章；高阅读选择样本，不是全部文章'))]
        charts = []
        for cid, ds, source, label, x, y in [('weekly','weekly','account','两个完整周广告收入（元）','period','income'),('slots','slots','slots','91天各广告位收入（元）','slot_name','income'),('followers','mature','content','18篇成熟样本中转粉效率前六篇（人/千名读者）','topic','followers_per_1000_readers')]:
            charts.append(dict(id=cid,dataset=ds,sourceId=source,title=label,type='bar',encodings=dict(x=dict(field=x,type='nominal'),y=dict(field=y,type='quantitative')),layout='full'))
        payload = dict(surface='report',manifest=dict(version=1,surface='report',title=title,blocks=blocks,charts=charts,sources=sources),snapshot=dict(version=1,status='ready',datasets=dict(weekly=periods[:2],slots=slots,mature=leaders)))
        (OUT / 'artifact.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
