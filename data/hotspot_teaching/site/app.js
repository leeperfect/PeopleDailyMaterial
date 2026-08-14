const state = {
  data: null,
  view: "today",
  archive: "daily",
  selectedDaily: null,
  selectedWeekly: null,
  selectedTopic: null,
  search: "",
};

const main = document.querySelector("#mainContent");
const archiveList = document.querySelector("#archiveList");
const searchInput = document.querySelector("#searchInput");
const toast = document.querySelector("#toast");
const archiveSidebar = document.querySelector(".archive-sidebar");

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" }).format(date);
}

function shortDate(value) {
  if (!value) return "";
  const [, month, day] = value.split("-");
  return `${Number(month)}月${Number(day)}日`;
}

function topicById(id) {
  return state.data.topics.find(topic => topic.topic_id === id);
}

function currentDaily() {
  const editions = state.data.daily_editions;
  return editions.find(item => item.edition_date === state.selectedDaily) || editions[0];
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 1800);
}

async function copyText(text, message = "已复制") {
  try {
    await navigator.clipboard.writeText(text);
    showToast(message);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    showToast(message);
  }
}

function quickText(topic) {
  const card = topic.card;
  return [
    `【${topic.topic}｜3分钟速讲】`,
    card.quick_intro,
    "",
    "一、关键事实",
    ...(card.key_facts || []).map((item, index) => `${index + 1}. ${item}`),
    "",
    "二、核心判断",
    ...(card.core_judgments || []).map((item, index) => `${index + 1}. ${item}`),
    "",
    `课堂切入：${card.classroom_entry}`,
  ].join("\n");
}

function fullCardText(topic) {
  const card = topic.card;
  const framework = card.analysis_framework || {};
  return [
    "【热点概览】",
    card.news_overview,
    "",
    "【深度教学分析】",
    ...Object.entries(framework).flatMap(([key, value]) => [
      `${key}：`,
      ...(Array.isArray(value) ? value : [value]).map((item, index) => `${index + 1}. ${item}`),
    ]),
    "",
    quickText(topic),
    "",
    "【为什么值得讲】",
    card.worth_teaching,
    "",
    "【规范表达】",
    ...(card.standard_expressions || []).map((item, index) => `${index + 1}. ${item}`),
    "",
    "【课堂问题】",
    ...(card.classroom_questions || []).map((item, index) => `${index + 1}. ${item}`),
  ].join("\n");
}

function analysisItems(value) {
  return (Array.isArray(value) ? value : [value]).filter(Boolean);
}

function analysisGridHtml(framework) {
  return Object.entries(framework || {}).map(([key, value]) => `
    <div class="framework-item">
      <strong>${escapeHtml(key)}</strong>
      <ol class="framework-list">${analysisItems(value).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
    </div>`).join("");
}

function setView(view) {
  state.view = view;
  document.querySelectorAll(".nav-item").forEach(button => button.classList.toggle("active", button.dataset.view === view));
  if (view === "daily" || view === "today") setArchive("daily", false);
  if (view === "weekly") setArchive("weekly", false);
  if (view === "themes") setArchive("themes", false);
  render();
}

function setArchive(kind, rerender = true) {
  state.archive = kind;
  document.querySelectorAll(".archive-tab").forEach(button => button.classList.toggle("active", button.dataset.archive === kind));
  renderArchive();
  if (rerender) {
    state.view = kind === "themes" ? "themes" : kind;
    render();
  }
}

function groupByMonth(editions, key) {
  return editions.reduce((groups, edition) => {
    const month = (edition[key] || "").slice(0, 7);
    (groups[month] ||= []).push(edition);
    return groups;
  }, {});
}

function dailyArchiveHeadline(edition) {
  const topic = topicById((edition.topic_ids || [])[0]);
  if (!topic) return edition.title;
  const sameDayArticles = (topic.sources || [])
    .filter(item => item.source_kind === "peopleapp_opinion" && item.article?.date === edition.edition_date)
    .map(item => item.article)
    .filter(article => article?.title)
    .sort((a, b) => a.title.length - b.title.length || a.title.localeCompare(b.title, "zh-CN"));
  return sameDayArticles[0]?.title || topic.topic;
}

function renderArchive() {
  if (!state.data) return;
  const query = state.search.trim().toLowerCase();
  if (state.archive === "themes") {
    const categories = state.data.categories.filter(item => !query || item.name.toLowerCase().includes(query));
    archiveList.innerHTML = categories.length ? `
      <div class="archive-group">
        <div class="archive-month"><span>教学主题</span><small>${categories.length}</small></div>
        ${categories.map(item => `
          <button class="archive-link" data-category="${escapeHtml(item.name)}">
            <strong>${String(item.count).padStart(2, "0")}</strong><span>${escapeHtml(item.name)}</span>
          </button>`).join("")}
      </div>` : `<div class="archive-empty">没有匹配主题</div>`;
    return;
  }

  const isDaily = state.archive === "daily";
  const key = isDaily ? "edition_date" : "week_start";
  const editions = (isDaily ? state.data.daily_editions : state.data.weekly_editions).filter(edition => {
    if (!query) return true;
    const topics = (edition.topic_ids || []).map(topicById).filter(Boolean);
    return [edition.title, edition.teaching_judgment, ...topics.map(item => `${item.topic} ${item.category}`)]
      .join(" ").toLowerCase().includes(query);
  });
  const groups = groupByMonth(editions, key);
  archiveList.innerHTML = Object.keys(groups).length ? Object.entries(groups).map(([month, items]) => `
    <div class="archive-group">
      <div class="archive-month"><span>${month.replace("-", " 年 ")} 月</span><small>${items.length}</small></div>
      ${items.map(edition => {
        const topic = topicById((edition.topic_ids || [])[0]);
        const active = isDaily ? edition.edition_date === state.selectedDaily : edition.week_start === state.selectedWeekly;
        return `<button class="archive-link ${active ? "active" : ""}" data-${isDaily ? "daily" : "weekly"}="${edition[key]}">
          <strong>${isDaily ? `${Number(edition.edition_date.slice(-2))} 日` : shortDate(edition.week_start)}</strong>
          <span>${escapeHtml(isDaily ? dailyArchiveHeadline(edition) : (topic?.topic || edition.title))}</span>
        </button>`;
      }).join("")}
    </div>`).join("") : `<div class="archive-empty">没有匹配内容</div>`;
}

function statsHtml(edition, topics) {
  return `<div class="edition-stats">
    <div class="stat"><strong>${topics.length}</strong><span>今日热点</span></div>
    <div class="stat"><strong>${edition.app_article_count ?? topics.reduce((sum, item) => sum + item.app_article_count, 0)}</strong><span>APP评论支撑</span></div>
    <div class="stat"><strong>${edition.paper_article_count ?? topics.reduce((sum, item) => sum + item.paper_support_count, 0)}</strong><span>人民日报支撑</span></div>
    <div class="stat"><strong>${edition.reading_minutes ?? Math.max(5, topics.length * 3)}</strong><span>分钟速读</span></div>
  </div>`;
}

function editionHeader(edition, topics, type = "日报") {
  const dateLabel = type === "周报" ? `${shortDate(edition.week_start)}—${shortDate(edition.week_end)}` : formatDate(edition.edition_date);
  const issue = edition.issue_no ? `VOL.${String(edition.issue_no).padStart(3, "0")}` : "WEEKLY EDITION";
  return `
    <div class="edition-kicker"><span>${issue}</span><span>·</span><span>${topics.length} TOPICS</span><span>·</span><span>TEACHING ${type === "周报" ? "WEEKLY" : "DAILY"}</span></div>
    <h1 class="edition-title">热点<em>教学</em>${type}</h1>
    <p class="edition-date">${escapeHtml(dateLabel)}</p>
    <div class="double-rule"></div>
    <div class="teaching-judgment"><strong>今日教学判断</strong><p>${escapeHtml(edition.teaching_judgment)}</p></div>
    ${statsHtml(edition, topics)}
    ${edition.status !== "published" ? `<div class="review-banner">教研预览：来源已经过规则复核，教学卡仍需人工确认后再作为正式发布内容。</div>` : ""}`;
}

function headlineHtml(topics) {
  return `<section>
    <div class="section-title"><h2>今日看点</h2><small>${topics.length} 个热点 · 点击进入教学卡</small></div>
    <div class="headline-list">
      ${topics.map((topic, index) => `<button class="headline-item" data-topic="${topic.topic_id}">
        <span class="headline-no">${String(index + 1).padStart(2, "0")}</span>
        <span class="headline-category">${escapeHtml(topic.category)}</span>
        <span class="headline-copy"><strong>${escapeHtml(topic.topic)}</strong><small>${escapeHtml(topic.card?.classroom_entry || topic.angle)}</small></span>
        <span class="headline-arrow">›</span>
      </button>`).join("")}
    </div>
  </section>`;
}

function topicSummariesHtml(topics) {
  const groups = topics.reduce((result, topic) => {
    (result[topic.category] ||= []).push(topic);
    return result;
  }, {});
  return Object.entries(groups).map(([category, items], groupIndex) => `<section class="topic-section">
    <div class="topic-section-head"><span class="number">${String(groupIndex + 1).padStart(2, "0")}</span><h2>${escapeHtml(category)}</h2><small>${items.length} TOPICS</small></div>
    ${items.map(topic => `<article class="topic-card">
      <div class="topic-meta"><span class="pill priority">${topic.priority}级</span><span class="pill">${topic.status}</span><span class="pill">${topic.media_count}家媒体</span><span class="pill">${topic.paper_support_count}篇人民日报支撑</span></div>
      <h3>${escapeHtml(topic.topic)}</h3>
      <p>${escapeHtml(topic.card?.quick_intro || topic.angle)}</p>
      <div class="topic-actions"><button class="button primary" data-topic="${topic.topic_id}">打开教学卡</button><button class="button" data-copy-quick="${topic.topic_id}">复制3分钟速讲</button></div>
    </article>`).join("")}
  </section>`).join("");
}

function renderDaily() {
  const edition = currentDaily();
  if (!edition) return renderEmpty("还没有生成日报");
  const topics = (edition.topic_ids || []).map(topicById).filter(Boolean);
  main.innerHTML = `<div class="content-wrap">${editionHeader(edition, topics)}${headlineHtml(topics)}${topicSummariesHtml(topics)}</div>`;
}

function renderWeekly() {
  const edition = state.data.weekly_editions.find(item => item.week_start === state.selectedWeekly) || state.data.weekly_editions[0];
  if (!edition) return renderEmpty("还没有生成周报");
  const topics = (edition.topic_ids || []).map(topicById).filter(Boolean);
  main.innerHTML = `<div class="content-wrap">${editionHeader(edition, topics, "周报")}${headlineHtml(topics)}${topicSummariesHtml(topics)}</div>`;
}

function sourceCards(items, kind) {
  const sources = items.filter(item => item.source_kind === kind);
  if (!sources.length) return kind === "people_daily_newspaper"
    ? `<div class="empty-support">暂未发现可靠的《人民日报》正式版支撑文章。系统不会为了凑齐来源强行关联。</div>`
    : `<div class="empty-support">暂无APP评论来源。</div>`;
  return sources.map(item => {
    const article = item.article || {};
    const confidence = kind === "people_daily_newspaper" ? ` · 匹配度 ${Math.round((item.confidence || 0) * 100)}%` : "";
    return `<article class="source-card">
      <span class="source-role">${escapeHtml(item.relation_role)}${confidence}</span>
      <h3>${escapeHtml(article.title)}</h3>
      <p>${escapeHtml(article.summary || item.match_reason)}</p>
      <small>${escapeHtml(article.date)} · ${escapeHtml(article.source_name)}${article.section_name ? ` · ${escapeHtml(article.section_name)}` : ""}</small>
      ${article.source_url ? `<p><a href="${escapeHtml(article.source_url)}" target="_blank" rel="noreferrer">打开原文 ↗</a></p>` : ""}
    </article>`;
  }).join("");
}

function renderTopic(id) {
  const topic = topicById(id);
  if (!topic?.card) return renderEmpty("没有找到这张教学卡");
  state.selectedTopic = id;
  const card = topic.card;
  const navItems = [
    ["overview", "新闻概况"], ["framework", "深度教学分析"], ["quick", "3分钟速讲"],
    ["worth", "为什么值得讲"], ["questions", "课堂问题"], ["background", "背景与时间线"],
    ["views", "媒体观点比较"], ["paper", "人民日报支撑"], ["sources", "全部来源"],
  ];
  main.innerHTML = `<div class="content-wrap">
    <button class="button detail-back" data-back>← 返回日报</button>
    <header class="detail-header">
      <div class="topic-meta"><span class="pill priority">${topic.priority}级</span><span class="pill">${escapeHtml(topic.category)}</span><span class="pill">${topic.status}</span><span class="pill">${topic.start_date}—${topic.end_date}</span></div>
      <h1>${escapeHtml(topic.topic)}</h1>
      <p class="detail-lead">${escapeHtml(card.quick_intro)}</p>
      <div class="topic-actions"><button class="button primary" data-copy-full="${topic.topic_id}">复制完整教学卡</button><button class="button" data-copy-quick="${topic.topic_id}">复制3分钟速讲</button><button class="button" onclick="window.print()">打印讲义</button></div>
      ${card.review_status !== "published" ? `<div class="review-banner">当前状态：教学卡初稿。APP热点归并已经复核；人民日报关联与教学表达仍需人工确认。</div>` : ""}
    </header>
    <div class="detail-layout">
      <article>
        <section id="overview" class="detail-section"><h2>新闻概况</h2><p class="overview-copy">${escapeHtml(card.news_overview || card.quick_intro)}</p></section>
        <section id="framework" class="detail-section analysis-section">
          <div class="section-title"><h2>深度教学分析</h2><small>从新闻现象走向治理逻辑</small></div>
          <h3>问题—原因—影响—对策</h3>
          <div class="framework-grid">${analysisGridHtml(card.analysis_framework)}</div>
          <h3>建议讲授顺序</h3>
          <div class="teaching-path">
            <div><strong>01 现象导入</strong><p>${escapeHtml(card.classroom_entry)}</p></div>
            <div><strong>02 矛盾提炼</strong><p>${escapeHtml(card.controversy)}</p></div>
            <div><strong>03 机制分析</strong><p>结合问题、原因和影响，说明个案背后的责任边界、制度短板与公共价值。</p></div>
            <div><strong>04 表达迁移</strong><p>使用下方规范表达形成申论分论点、面试分析段或课堂总结。</p></div>
          </div>
          <h3>可直接使用的规范表达</h3><ol class="numbered-list">${(card.standard_expressions || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
          <h3>常见误区</h3><ol class="numbered-list">${(card.common_mistakes || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
        </section>
        <section id="quick" class="detail-section"><h2>3分钟速讲</h2><div class="quick-card"><p>${escapeHtml(card.quick_intro)}</p><h3>三个关键事实</h3><ol class="numbered-list">${(card.key_facts || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol><h3>三个核心判断</h3><ol class="numbered-list">${(card.core_judgments || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol></div></section>
        <section id="worth" class="detail-section"><h2>为什么值得讲</h2><p>${escapeHtml(card.worth_teaching)}</p><p><strong>课堂切入：</strong>${escapeHtml(card.classroom_entry)}</p></section>
        <section id="questions" class="detail-section"><h2>课堂互动问题</h2><ol class="numbered-list">${(card.classroom_questions || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol></section>
        <section id="background" class="detail-section"><h2>背景与时间线</h2><ul class="timeline">${(card.background || []).map(item => `<li><time>${escapeHtml(item.date)}</time><div><strong>${escapeHtml(item.source)}</strong> · ${escapeHtml(item.title)}</div></li>`).join("")}</ul><p>${escapeHtml(card.controversy)}</p></section>
        <section id="views" class="detail-section"><h2>APP评论观点比较</h2>${(card.media_viewpoints || []).map(item => `<article class="source-card"><span class="source-role">媒体观点</span><h3>${escapeHtml(item.source)}｜${escapeHtml(item.title)}</h3><p>${escapeHtml(item.viewpoint)}</p>${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">查看来源 ↗</a>` : ""}</article>`).join("")}</section>
        <section id="paper" class="detail-section"><h2>《人民日报》正式版支撑</h2>${sourceCards(topic.sources || [], "people_daily_newspaper")}</section>
        <section id="sources" class="detail-section"><h2>全部来源</h2><h3>人民日报APP评论</h3>${sourceCards(topic.sources || [], "peopleapp_opinion")}<h3>《人民日报》正式版</h3>${sourceCards(topic.sources || [], "people_daily_newspaper")}</section>
      </article>
      <aside class="detail-nav"><strong>本课目录</strong>${navItems.map(([anchor, label]) => `<a href="#${anchor}">${label}</a>`).join("")}<div class="topic-meta">${(card.tags || []).map(tag => `<span class="pill">${escapeHtml(tag)}</span>`).join("")}</div></aside>
    </div>
  </div>`;
  main.focus();
}

function renderThemes() {
  const topicsByCategory = state.data.topics.reduce((result, topic) => {
    (result[topic.category] ||= []).push(topic);
    return result;
  }, {});
  main.innerHTML = `<div class="content-wrap simple-page"><p class="edition-kicker">THEME ARCHIVE · 长期母题</p><h1>主题档案</h1><p>把每天的新闻变化沉淀成可持续复用的教学母题。点击主题后，可查看该主题下的全部热点卡。</p><div class="theme-grid">${Object.entries(topicsByCategory).map(([category, topics]) => `<article class="theme-card" data-category="${escapeHtml(category)}"><small>${topics.length} 个热点</small><h2>${escapeHtml(category)}</h2><p>${escapeHtml(topics.slice(0, 4).map(item => item.topic).join("；"))}</p></article>`).join("")}</div></div>`;
}

function renderCategory(category) {
  const topics = state.data.topics.filter(topic => topic.category === category);
  main.innerHTML = `<div class="content-wrap simple-page"><button class="button detail-back" data-view-button="themes">← 返回主题档案</button><p class="edition-kicker">TEACHING THEME</p><h1>${escapeHtml(category)}</h1><p>共 ${topics.length} 个经过热点归并的教学主题。</p>${topicSummariesHtml(topics)}</div>`;
}

function renderRanking() {
  const ranked = [...state.data.topics].sort((a, b) => (b.media_count * 2 + b.app_article_count + b.paper_support_count) - (a.media_count * 2 + a.app_article_count + a.paper_support_count));
  main.innerHTML = `<div class="content-wrap simple-page"><p class="edition-kicker">HOTSPOT RANKING · 多源关注</p><h1>热点排行</h1><p>排行用于帮助教师快速确定优先级，综合参考媒体数量、APP评论文章和人民日报支撑数量，不代表价值判断。</p><div class="ranking-list">${ranked.map((topic, index) => `<button class="ranking-row" data-topic="${topic.topic_id}"><strong>${String(index + 1).padStart(2, "0")}</strong><span><h3>${escapeHtml(topic.topic)}</h3><small>${escapeHtml(topic.category)} · ${topic.media_count}家媒体 · ${topic.app_article_count}篇APP评论</small></span><span class="pill priority">${topic.priority}级</span></button>`).join("")}</div></div>`;
}

function renderInfo(kind) {
  const sourcePage = kind === "sources";
  main.innerHTML = `<div class="content-wrap simple-page"><p class="edition-kicker">${sourcePage ? "SOURCE NOTES" : "USER GUIDE"}</p><h1>${sourcePage ? "来源说明" : "使用指南"}</h1>${sourcePage ? `
    <p>本工具使用两条彼此独立的事实链。页面不会把来源文章简单混在一起，也不会为了凑齐材料强行建立关系。</p>
    <div class="theme-grid"><article class="theme-card"><small>热点信号 · 媒体观点 · 争议观察</small><h2>人民日报APP评论库</h2><p>用于识别多家媒体共同关注的现实话题，并保留媒体差异。</p></article><article class="theme-card"><small>政策依据 · 治理案例 · 规范表达</small><h2>《人民日报》正式版文章库</h2><p>用于补充权威政策语境、案例和可用于课堂的规范表达。</p></article></div>
    <p class="review-banner">自动匹配的人民日报文章会显示匹配理由与可信度；未完成人工确认前，统一标记为教研预览。</p>` : `
    <div class="theme-grid"><article class="theme-card"><small>第一步</small><h2>先看“今日看点”</h2><p>30秒判断当天最值得补充的热点，以及适合进入哪类课程。</p></article><article class="theme-card"><small>第二步</small><h2>复制3分钟速讲</h2><p>适合课堂临时补充，也可作为课程开场或案例导入。</p></article><article class="theme-card"><small>第三步</small><h2>展开教学卡</h2><p>继续查看媒体观点、人民日报支撑、分析框架、误区和课堂问题。</p></article><article class="theme-card"><small>第四步</small><h2>核对原始来源</h2><p>点击原文链接确认事实和语境，再用于正式课程或讲义。</p></article></div>`}</div>`;
}

function renderEmpty(message) {
  main.innerHTML = `<div class="content-wrap simple-page"><h1>${escapeHtml(message)}</h1><p>请先运行数据生成流程，或选择其他日期。</p></div>`;
}

function render() {
  if (!state.data) return;
  state.selectedTopic = null;
  if (state.view === "today" || state.view === "daily") renderDaily();
  else if (state.view === "weekly") renderWeekly();
  else if (state.view === "themes") renderThemes();
  else if (state.view === "ranking") renderRanking();
  else if (state.view === "sources" || state.view === "guide") renderInfo(state.view);
}

document.addEventListener("click", event => {
  const nav = event.target.closest("[data-view]");
  if (nav) setView(nav.dataset.view);
  const archiveTab = event.target.closest("[data-archive]");
  if (archiveTab) setArchive(archiveTab.dataset.archive);
  const daily = event.target.closest("[data-daily]");
  if (daily) {
    state.selectedDaily = daily.dataset.daily;
    state.view = "daily";
    renderArchive(); render(); archiveSidebar.classList.remove("open");
  }
  const weekly = event.target.closest("[data-weekly]");
  if (weekly) {
    state.selectedWeekly = weekly.dataset.weekly;
    state.view = "weekly";
    renderArchive(); render(); archiveSidebar.classList.remove("open");
  }
  const topic = event.target.closest("[data-topic]");
  if (topic) renderTopic(topic.dataset.topic);
  const category = event.target.closest("[data-category]");
  if (category) renderCategory(category.dataset.category);
  const back = event.target.closest("[data-back]");
  if (back) render();
  const viewButton = event.target.closest("[data-view-button]");
  if (viewButton) setView(viewButton.dataset.viewButton);
  const copyQuick = event.target.closest("[data-copy-quick]");
  if (copyQuick) copyText(quickText(topicById(copyQuick.dataset.copyQuick)), "3分钟速讲已复制");
  const copyFull = event.target.closest("[data-copy-full]");
  if (copyFull) copyText(fullCardText(topicById(copyFull.dataset.copyFull)), "完整教学卡已复制");
});

searchInput.addEventListener("input", event => {
  state.search = event.target.value;
  renderArchive();
});

document.querySelector("#mobileArchiveToggle").addEventListener("click", () => archiveSidebar.classList.toggle("open"));

document.querySelector("#themeToggle").addEventListener("click", () => {
  const current = document.documentElement.dataset.theme || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("hotspot-teaching-theme", next);
  document.querySelector("[data-theme-icon]").textContent = next === "dark" ? "☾" : "☀";
  document.querySelector("[data-theme-label]").textContent = next === "dark" ? "深色阅读" : "浅色阅读";
});

async function init() {
  const savedTheme = localStorage.getItem("hotspot-teaching-theme");
  if (savedTheme) document.documentElement.dataset.theme = savedTheme;
  try {
    const response = await fetch("./data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`数据读取失败：${response.status}`);
    state.data = await response.json();
    state.selectedDaily = state.data.daily_editions[0]?.edition_date || null;
    state.selectedWeekly = state.data.weekly_editions[0]?.week_start || null;
    renderArchive();
    render();
  } catch (error) {
    main.innerHTML = `<div class="content-wrap simple-page"><h1>暂时无法读取教学日报</h1><p>${escapeHtml(error.message)}</p><p>如果是直接双击打开，请通过本地工作台入口启动。</p></div>`;
  }
}

init();
