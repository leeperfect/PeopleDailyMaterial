/* 公众号运营分析报告 · 图表初始化（数据来自 assets/report-data.js，均由本地数据库导出） */
(function () {
  var D = window.REPORT_DATA;
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  function baseTooltip() {
    return { trigger: 'axis', appendToBody: true, backgroundColor: ink, borderWidth: 0, textStyle: { color: bg2, fontSize: 12 } };
  }
  function mk(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    var c = echarts.init(el, null, { renderer: 'svg' });
    window.addEventListener('resize', function () { c.resize(); });
    return c;
  }
  function shortDate(s) { return s.slice(5); }

  /* 1. 30 天阅读与分享趋势 */
  var c1 = mk('chart-daily-trend');
  if (c1) c1.setOption({
    animation: false,
    tooltip: baseTooltip(),
    legend: { data: ['阅读人数', '分享人数', '收藏人数'], textStyle: { color: muted }, top: 0 },
    grid: { left: 50, right: 20, top: 36, bottom: 30 },
    xAxis: { type: 'category', data: D.daily.map(function (r) { return shortDate(r.date); }), axisLabel: { color: muted, interval: 2 }, axisLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
    series: [
      { name: '阅读人数', type: 'line', smooth: true, symbol: 'none', data: D.daily.map(function (r) { return r.read_users; }), lineStyle: { width: 2.5, color: accent }, itemStyle: { color: accent }, areaStyle: { color: accent, opacity: 0.08 } },
      { name: '分享人数', type: 'line', smooth: true, symbol: 'none', data: D.daily.map(function (r) { return r.share_users; }), lineStyle: { width: 1.5, color: accent2 }, itemStyle: { color: accent2 } },
      { name: '收藏人数', type: 'line', smooth: true, symbol: 'none', data: D.daily.map(function (r) { return r.wechat_favorites; }), lineStyle: { width: 1.5, color: muted, type: 'dashed' }, itemStyle: { color: muted } }
    ]
  });

  /* 2. 渠道：移出区间 vs 新增区间 */
  var chans = D.channels.filter(function (c) { return c.moved_out != null || c.moved_in != null; });
  var c2 = mk('chart-channels');
  if (c2) c2.setOption({
    animation: false,
    tooltip: baseTooltip(),
    legend: { data: ['移出区间 7/31–8/7', '新增区间 8/30–9/6'], textStyle: { color: muted }, top: 0 },
    grid: { left: 70, right: 20, top: 36, bottom: 30 },
    xAxis: { type: 'category', data: chans.map(function (c) { return c.channel; }), axisLabel: { color: muted, interval: 0, rotate: 20 }, axisLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
    series: [
      { name: '移出区间 7/31–8/7', type: 'bar', data: chans.map(function (c) { return c.moved_out; }), itemStyle: { color: rule }, barGap: '10%' },
      { name: '新增区间 8/30–9/6', type: 'bar', data: chans.map(function (c) { return c.moved_in; }), itemStyle: { color: accent } }
    ]
  });

  /* 3. 91 天账号级收入 + eCPM */
  var c3 = mk('chart-income-daily');
  if (c3) c3.setOption({
    animation: false,
    tooltip: baseTooltip(),
    legend: { data: ['每日收入（元）', 'eCPM（元）'], textStyle: { color: muted }, top: 0 },
    grid: { left: 50, right: 50, top: 36, bottom: 30 },
    xAxis: { type: 'category', data: D.adDaily.map(function (r) { return shortDate(r.date); }), axisLabel: { color: muted, interval: 6 }, axisLine: { lineStyle: { color: rule } } },
    yAxis: [
      { type: 'value', name: '收入', nameTextStyle: { color: muted }, splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
      { type: 'value', name: 'eCPM', nameTextStyle: { color: muted }, splitLine: { show: false }, axisLabel: { color: muted } }
    ],
    series: [
      { name: '每日收入（元）', type: 'bar', data: D.adDaily.map(function (r) { return r.income; }), itemStyle: { color: accent, opacity: 0.75 }, barMaxWidth: 8 },
      { name: 'eCPM（元）', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'none', data: D.adDaily.map(function (r) { return r.ecpm; }), lineStyle: { width: 2, color: accent2 }, itemStyle: { color: accent2 } }
    ]
  });

  /* 4. 广告位收入结构（91 天） */
  var c4 = mk('chart-slots');
  if (c4) c4.setOption({
    animation: false,
    tooltip: { trigger: 'item', appendToBody: true, backgroundColor: ink, borderWidth: 0, textStyle: { color: bg2, fontSize: 12 }, formatter: '{b}<br/>{c} 元（{d}%）' },
    legend: { bottom: 0, textStyle: { color: muted, fontSize: 12 } },
    series: [{
      type: 'pie', radius: ['48%', '72%'], center: ['50%', '44%'],
      label: { color: ink, formatter: '{b}\n{d}%' },
      itemStyle: { borderColor: bg2, borderWidth: 2 },
      color: [accent, accent2, muted, rule],
      data: D.slots.map(function (s) { return { name: s.slot_name, value: s.income }; })
    }]
  });

  /* 5. 窗口内文章收入 TOP10 */
  var tops = D.topArticles.slice().reverse();
  var c5 = mk('chart-top-articles');
  if (c5) c5.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' }, backgroundColor: ink, borderWidth: 0, textStyle: { color: bg2, fontSize: 12 } },
    grid: { left: 10, right: 60, top: 10, bottom: 10, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
    yAxis: {
      type: 'category',
      data: tops.map(function (a) {
        var t = a.title.replace(/《人民日报》/g, '');
        return t.length > 16 ? t.slice(0, 15) + '…' : t;
      }),
      axisLabel: { color: ink, fontSize: 12 }, axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'bar', data: tops.map(function (a) { return a.win_income; }),
      itemStyle: { color: function (p) { return p.dataIndex === tops.length - 1 ? accent2 : accent; }, borderRadius: [0, 3, 3, 0] },
      label: { show: true, position: 'right', color: muted, formatter: '{c} 元' },
      barMaxWidth: 18
    }]
  });

  /* 6. 22 篇阅读 × 收入散点 */
  var c6 = mk('chart-scatter');
  if (c6) c6.setOption({
    animation: false,
    tooltip: {
      trigger: 'item', appendToBody: true, backgroundColor: ink, borderWidth: 0, textStyle: { color: bg2, fontSize: 12 },
      formatter: function (p) {
        var d = p.data.meta;
        return d.title + '<br/>阅读 ' + d.reads.toLocaleString() + ' · 收入 ' + d.income + ' 元<br/>效率 ' + d.eff + ' 元/千读 · ' + d.neg;
      }
    },
    grid: { left: 60, right: 30, top: 30, bottom: 45 },
    xAxis: { type: 'value', name: '阅读人数（30 天窗口）', nameLocation: 'middle', nameGap: 30, nameTextStyle: { color: muted }, splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
    yAxis: { type: 'value', name: '累计收入（元）', nameTextStyle: { color: muted }, splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
    series: [{
      type: 'scatter',
      data: D.scatter.map(function (a) {
        return { value: [a.reads, a.income], meta: a, itemStyle: { color: a.neg === '无否定式' ? accent2 : accent, opacity: 0.85 } };
      }),
      symbolSize: function (val, p) { return Math.max(8, Math.min(30, p.data.meta.eff * 6)); },
      labelLayout: { hideOverlap: true }
    }]
  });

  /* 7. 91 天用户增长 */
  var c7 = mk('chart-growth');
  if (c7) c7.setOption({
    animation: false,
    tooltip: baseTooltip(),
    legend: { data: ['每日新增关注', '累计关注'], textStyle: { color: muted }, top: 0 },
    grid: { left: 55, right: 60, top: 36, bottom: 30 },
    xAxis: { type: 'category', data: D.growth.map(function (r) { return shortDate(r.date); }), axisLabel: { color: muted, interval: 6 }, axisLine: { lineStyle: { color: rule } } },
    yAxis: [
      { type: 'value', name: '新增', nameTextStyle: { color: muted }, splitLine: { lineStyle: { color: rule } }, axisLabel: { color: muted } },
      { type: 'value', name: '累计', nameTextStyle: { color: muted }, splitLine: { show: false }, axisLabel: { color: muted } }
    ],
    series: [
      { name: '每日新增关注', type: 'bar', data: D.growth.map(function (r) { return r.new_followers; }), itemStyle: { color: accent, opacity: 0.75 }, barMaxWidth: 7 },
      { name: '累计关注', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'none', data: D.growth.map(function (r) { return r.cumulative_followers; }), lineStyle: { width: 2.5, color: accent2 }, itemStyle: { color: accent2 } }
    ]
  });
})();
