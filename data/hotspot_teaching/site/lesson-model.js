/* Shared content model for screen, clipboard, Word and print. No DOM dependency. */
(function (root) {
  'use strict';
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeURL = value => /^https?:\/\//i.test(value || '') ? value : '';
  const cleanTitle = value => String(value).replace(/[\p{P}\p{S}]/gu, ' ').replace(/\s+/g, ' ').trim();
  const b = (type, text, extra = {}) => ({type, text: String(text ?? ''), ...extra});
  const paragraphs = text => String(text || '').split(/\n+/).filter(s => s.trim()).map(s => b('p', s));
  const lessonTitle = topic => topic.lesson?.title || topic.topic;
  const modes = {quick:'3分钟讲稿', teacher:'教师详稿', student:'学生练习单', slides:'课件提纲', legacy:'原教学卡'};
  function metadata(topic, edited = false) {
    const l = topic.lesson;
    return l ? `资料截至 ${l.basis_until} · 教研版本 ${l.version} · ${l.source_check === 'matched' ? '新教研稿 待试讲确认' : '来源有变化 待重新核验'}${edited ? ' · 含教师个人改稿' : ''}`
      : `资料截至 ${topic.end_date || '未注明'} · 原版资料 · ${topic.card?.review_status === 'published' ? '曾标记发布，取用前核对关联来源' : '待教研确认'}`;
  }
  function sourceBlocks(topic) {
    const records = topic.lesson?.sources || (topic.sources || []).map(s => s.article).filter(Boolean);
    const seen = new Set();
    return [b('h2','参考来源'), ...records.filter(s => { if (seen.has(s.article_id)) return false; seen.add(s.article_id); return true; }).map((s, i) => b('link', `${i+1}. ${s.source_review?.status==='superseded'?'【旧闻已纠正】':s.source_review?.status==='image_reference'?'【图片延伸阅读】':''}${s.title}（${s.date || '日期未注明'}）`, {url:safeURL(s.source_url)}))];
  }
  function cautions(topic) {
    return (topic.lesson?.source_cautions || []).flatMap(r => [b('p',r.note,{bold:true}),
      ...(r.correction_url ? [b('link',`纠正依据：${r.correction_title}`,{url:safeURL(r.correction_url)})] : [])]);
  }
  function sourceSummary(a) {
    const review=a.source_review;
    const label=review?.status==='superseded'?'旧闻已纠正':review?.status==='image_reference'?'图片延伸阅读':a.lesson_ids?.length?'已关联授课资料':'来源资料';
    return [b('title',a.title),b('meta',`${a.date} · ${a.source_name} · ${label}`),
      ...(review?[b('p',review.note,{bold:true})]:[]),
      ...(review?.correction_url?[b('link',`纠正依据：${review.correction_title}`,{url:safeURL(review.correction_url)})]:[]),
      ...(!review?[b('h2',a.summary?'原库摘要':'正文节选'),b('p',a.summary||a.content_excerpt||'请查看来源原文。')]:[]),
      b('link',review?.status==='superseded'?'原文留存（已纠正，仅供对照）':'来源原文',{url:safeURL(a.source_url)})];
  }
  function facts(topic) {
    const l = topic.lesson;
    return [b('h2','事件事实'), ...l.facts.map(f => b('li', `${f.text} [${f.source_ids.map(id => l.source_ids.indexOf(id)+1).join(', ')}]`))];
  }
  function quick(topic, options) {
    const draft = options.drafts?.[topic.topic_id]?.text;
    return [b('h2','课堂口语稿'), ...(options.useDraft && draft ? paragraphs(draft) : topic.lesson.quick_script.map(s => b('p',s)))];
  }
  function exerciseBlocks(l, answers) {
    const blocks = [];
    for (const e of l.exercises) {
      blocks.push(b('h2',e.kind), b('p',e.prompt,{keepNext:true}), b('meta',e.requirement,{keepNext:true}));
      if (answers) blocks.push(b('h3','参考作答'), b('p',e.answer), b('h3','教师观察要点'), ...e.points.map(s => b('li',s)));
      else blocks.push(b('space','作答区'));
    }
    return blocks;
  }
  function legacy(topic) {
    const c = topic.card || {}, blocks = [];
    const textFields = {news_overview:'新闻概况',quick_intro:'简要判断',worth_teaching:'选用说明',classroom_entry:'课堂切入',controversy:'讨论方向'};
    for (const [key,label] of Object.entries(textFields)) if (c[key]) blocks.push(b('h2',label), b('p',c[key]));
    for (const [key,label] of Object.entries({key_facts:'原卡资料摘要',core_judgments:'核心判断',standard_expressions:'教学表达',common_mistakes:'常见误区',classroom_questions:'课堂问题'})) {
      blocks.push(b('h2',label), ...(c[key] || []).map(s => b('li',s)));
    }
    blocks.push(b('h2','原版分析框架'));
    for (const [key,value] of Object.entries(c.analysis_framework || {})) blocks.push(b('h3',key), ...(Array.isArray(value) ? value : [value]).map(s => b('p',s)));
    blocks.push(b('h2','背景与时间线'), ...(c.background || []).map(s => b('li',`${s.date} ${s.source} ${s.title}`)), b('h2','媒体观点'));
    for (const v of c.media_viewpoints || []) blocks.push(b('h3',`${v.source} ${v.title}`), b('p',v.viewpoint));
    for (const [key, values] of Object.entries(c.cases || {})) {
      blocks.push(b('h2',`原卡归类 ${key}`), ...values.map(s => b('p',`${s.title || ''} ${s.summary || s.viewpoint || ''}`)));
    }
    return blocks;
  }
  function section(topic, key, options = {}) {
    const l = topic.lesson;
    if (!l) return legacy(topic);
    if (key === 'quick') return quick(topic,options);
    if (key === 'facts') return facts(topic);
    if (key === 'chain') return [b('h2','分析路径'),...l.chain.map(s => b('li',s)),b('p',l.takeaway)];
    if (key === 'segments') return l.segments.flatMap(s => [b('h2',`${s.title}  ${s.minutes}分钟`),b('p',s.script,{keepNext:true}),b('p',`板书：${s.board}`,{bold:true})]);
    if (key === 'interactions') return l.interactions.flatMap(q => [b('h2',q.question),b('p',`学生可能回答：${q.likely_answer}`,{keepNext:true}),b('p',`教师追问：${q.follow_up}`,{bold:true,keepNext:true}),b('p',`参考要点：${q.answer}`,{keepNext:true}),b('meta',`观察：${q.check}`)]);
    if (key === 'exercises') return exerciseBlocks(l, options.answers !== false);
    if (key === 'slides') return l.slides.flatMap((s,i) => [b('h2',`第${i+1}页 ${s.title}`),...s.bullets.map((t,j) => b('li',t,{keepNext:options.notes || j < s.bullets.length-1})),...(options.notes ? [b('meta',`讲解备注：${s.notes}`)] : [])]);
    if (key === 'viewpoints') return [b('h2','媒体观点与出处'), ...l.viewpoints.map(v => b('p',`${v.text} [${l.source_ids.indexOf(v.source_id)+1}]`))];
    return [];
  }
  function build(topics, mode = 'teacher', opts = {}) {
    const options = {answers:mode !== 'student',sources:true,notes:false,useDraft:true,...opts};
    const blocks = [];
    if (topics.length > 1) blocks.push(b('title',cleanTitle(opts.packTitle || '本次备课')),b('meta',`${topics.length}个案例 · ${modes[mode] || modes.teacher}`));
    topics.forEach((topic,index) => {
      if (index > 0) blocks.push(b('page',''));
      const l = topic.lesson;
      blocks.push(b('title',cleanTitle(`${lessonTitle(topic)} ${modes[l ? mode : 'legacy']}`)), b('meta',metadata(topic,!!(['quick','teacher'].includes(mode) && options.useDraft && options.drafts?.[topic.topic_id]?.text))));
      blocks.push(...cautions(topic));
      if(l?.usage_boundary) blocks.push(b('meta',`材料使用边界：${l.usage_boundary}`));
      if (!l || mode === 'legacy') blocks.push(...legacy(topic));
      else if (mode === 'student') {
        blocks.push(b('p','阅读材料，完成下列模拟练习。题目由教研整理，非考试原题。'),...facts(topic),...(options.sources ? sourceBlocks(topic) : []),...exerciseBlocks(l,false));
        if (options.answers) blocks.push(b('page',''),b('h1','参考答案 教师留存'),...exerciseBlocks(l,true));
      } else if (mode === 'slides') blocks.push(...section(topic,'slides',options));
      else {
        blocks.push(b('p',l.focus),b('meta',`适用：${l.courses.join('、')}。${l.teaching_note}`),...quick(topic,options));
        if (mode !== 'quick') {
          blocks.push(...facts(topic),...section(topic,'chain'),...section(topic,'segments'));
          if (options.answers) blocks.push(...section(topic,'interactions'));
          else blocks.push(b('h2','课堂提问'),...l.interactions.map(q => b('li',q.question)));
          blocks.push(...exerciseBlocks(l,options.answers),...section(topic,'viewpoints'));
        }
      }
      if (mode !== 'student' && options.notes && options.notesById?.[topic.topic_id]?.text) blocks.push(b('h2','我的备课备注'),...paragraphs(options.notesById[topic.topic_id].text));
      if (options.sources && !(l && mode === 'student')) blocks.push(...sourceBlocks(topic));
      else if (!options.sources) blocks.push(b('meta','本次未附来源目录，完整出处见热点教学日报对应案例。'));
    });
    return blocks;
  }
  function html(blocks) {
    return blocks.map(s => {
      const t=escape(s.text);
      if (s.type==='page') return '<div class="page-break" style="page-break-before:always"></div>';
      if (s.type==='space') return `<div style="break-inside:avoid"><p>${t}</p><div class="answer-space" style="height:100px;border-bottom:1px solid #ccc"></div></div>`;
      if (s.type==='title') return `<h1 style="color:#000;font-size:24pt;line-height:1.4">${t}</h1>`;
      if (/^h[123]$/.test(s.type)) return `<${s.type} style="color:#000;line-height:1.5">${t}</${s.type}>`;
      if (s.type==='link') return `<p><a href="${escape(safeURL(s.url))}" style="color:#24557c">${t}</a></p>`;
      if (s.type==='li') return `<ul style="margin:6px 0;padding-left:24px;${s.keepNext?'break-after:avoid;':''}"><li>${t}</li></ul>`;
      return `<p style="line-height:1.8;${s.keepNext?'break-after:avoid;':''}${s.type==='meta'?'color:#555;font-size:10pt;':''}">${s.bold?`<strong>${t}</strong>`:t}</p>`;
    }).join('');
  }
  const plain = blocks => blocks.map(s => s.type==='page' ? '\n' : s.type==='space' ? '作答区\n\n\n\n' : `${s.type==='li'?'• ':''}${s.text}${s.type==='link'&&s.url?'\n'+s.url:''}`).join('\n\n');
  const api={escape,safeURL,cleanTitle,metadata,lessonTitle,modes,sourceBlocks,cautions,sourceSummary,section,build,html,plain};
  if (typeof module !== 'undefined' && module.exports) module.exports=api;
  root.LessonModel=api;
})(typeof window === 'undefined' ? globalThis : window);
