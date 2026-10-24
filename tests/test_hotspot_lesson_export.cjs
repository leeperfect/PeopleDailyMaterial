// Verify the content contract shared by clipboard, Word and print.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '..');
  await import(pathToFileURL(path.join(root, 'web/hotspot_teaching_daily/lesson-model.js')).href);
  const M = globalThis.LessonModel;
  const data = JSON.parse(fs.readFileSync(path.join(root, 'data/hotspot_teaching/site/data.json'), 'utf8'));
  const topics = data.topics;
  const lessons = topics.filter(t => t.lesson);
  const editorial = path.join(root,'data/hotspot_teaching/editorial');
  const authored = ['lesson-pilots.json','lesson-library.json'].flatMap(name=>JSON.parse(fs.readFileSync(path.join(editorial,name),'utf8')).lessons);
  assert.deepEqual(new Set(lessons.map(t=>t.topic_id)),new Set(authored.map(l=>l.topic_id)));
  assert.equal(lessons.length,authored.length);
  assert.equal(lessons.length,data.source_coverage.lesson_count);
  assert.equal(data.source_coverage.original_lessons,49);
  assert.equal(data.source_coverage.supplemental_lessons,lessons.filter(t=>t.is_supplement).length);
  assert.equal(data.fresh_articles.length,data.source_coverage.fresh_count);
  assert.equal(new Set(data.fresh_articles.map(a=>a.article_id)).size,data.fresh_articles.length);
  for(const a of data.fresh_articles){
    assert(Array.isArray(a.lesson_ids) && a.lesson_ids.every(id=>lessons.some(t=>t.topic_id===id)));
    if(!a.lesson_ids.length) assert.equal(a.material_status,'source_only');
  }
  assert.equal(data.fresh_articles.filter(a=>a.lesson_ids.length).length,data.source_coverage.fresh_with_lessons);
  const originalFeed=JSON.parse(fs.readFileSync(path.join(editorial,'full-coverage/inventory.json'),'utf8')).fresh_articles;
  for(const a of originalFeed) assert(data.fresh_articles.some(row=>row.article_id===a.article_id && row.lesson_ids.length));
  assert.equal(new Set(lessons.map(t=>t.lesson.quick_script.join(''))).size,lessons.length);
  const teacher=M.plain(M.build(lessons,'teacher'));
  for(const t of lessons){
    assert.equal(t.lesson.source_check,'matched');
    assert.equal(t.lesson.segments.reduce((n,s)=>n+s.minutes,0),10);
    assert(t.lesson.interactions.length>=2 && t.lesson.slides.length>=5);
    for(const e of t.lesson.exercises) assert(teacher.includes(e.answer));
  }
  const t = lessons[0];
  const drafts = {[t.topic_id]: {text: '仅属于教师的个人改稿'}};
  const notesById = {[t.topic_id]: {text: '不应发给学生的备课备注'}};
  const student = M.plain(M.build(lessons, 'student', {drafts, notesById, notes:true}));
  for (const topic of lessons) {
    assert(student.includes(topic.lesson.basis_until));
    for (const e of topic.lesson.exercises) {
      assert(student.includes(e.prompt));
      assert(!student.includes(e.answer));
    }
    for (const q of topic.lesson.interactions) assert(!student.includes(q.answer));
  }
  assert(!student.includes(drafts[t.topic_id].text));
  assert(!student.includes(notesById[t.topic_id].text));
  assert(!student.includes('含教师个人改稿'));
  const answerBlocks = M.build([t], 'student', {answers:true});
  const answerHeading = answerBlocks.findIndex(b => b.text === '参考答案 教师留存');
  assert.equal(answerBlocks[answerHeading - 1].type, 'page');
  assert(M.plain(answerBlocks).includes(t.lesson.exercises[0].answer));
  assert(M.plain(M.build([t], 'quick', {drafts})).includes(drafts[t.topic_id].text));
  assert(!M.plain(M.build([t], 'quick', {drafts,useDraft:false})).includes(drafts[t.topic_id].text));
  assert(!M.plain(M.build([t], 'slides')).includes(t.lesson.slides[0].notes));
  assert(M.plain(M.build([t], 'slides', {notes:true})).includes(t.lesson.slides[0].notes));
  const original = topics.find(topic => topic.card);
  const legacy = {...original,lesson:null};
  assert(M.plain(M.build([legacy], 'teacher')).includes(legacy.card.news_overview));
  assert(M.plain(M.build([original], 'legacy')).includes(original.card.news_overview));
  const corrected=data.fresh_articles.find(a=>a.material_status==='superseded');
  assert(corrected);
  const summary=M.plain(M.sourceSummary(corrected));
  assert(summary.includes('故事系编造') && summary.includes(corrected.source_review.correction_url));
  if(corrected.summary) assert(!summary.includes(corrected.summary));
  const correctionLesson=lessons.find(t=>corrected.lesson_ids.includes(t.topic_id));
  for(const mode of ['teacher','student','quick','slides']){
    const text=M.plain(M.build([correctionLesson],mode,{sources:false,notes:false}));
    assert(text.includes(corrected.source_review.note));
    assert(text.includes(corrected.source_review.correction_url));
  }
  const imageRef=data.fresh_articles.find(a=>a.material_status==='image_reference');
  assert(M.plain(M.sourceSummary(imageRef)).includes('未引用校长发言'));
  assert.equal(M.safeURL('javascript:alert(1)'), '');
  assert(!M.html([{type:'p',text:'<script>alert(1)</script>'}]).includes('<script>'));
  console.log('学生答案隔离、个人资料隔离、来源日期、讲稿选择与旧卡取用检查通过。');
})().catch(error => {console.error(error);process.exitCode = 1;});
