#!/usr/bin/env node
// Export the same lesson content used by the site into editable local Markdown.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');

(async()=>{
  const root=path.resolve(__dirname,'..');
  await import(pathToFileURL(path.join(root,'web/hotspot_teaching_daily/lesson-model.js')).href);
  const M=globalThis.LessonModel;
  const payloadPath=path.join(root,'data/hotspot_teaching/site/data.json');
  const payload=JSON.parse(fs.readFileSync(payloadPath,'utf8'));
  const topics=payload.topics.filter(t=>t.lesson);
  const out=path.join(root,'data/hotspot_teaching/exports/handouts');
  fs.mkdirSync(out,{recursive:true});
  const files={};
  const hash=content=>crypto.createHash('sha256').update(content).digest('hex');
  const markdown=blocks=>blocks.map(b=>{
    if(b.type==='page')return '\n---\n';
    if(b.type==='space')return '作答区\n\n________________________________________\n\n________________________________________\n\n________________________________________';
    if(b.type==='title')return '# '+b.text;
    if(/^h[123]$/.test(b.type))return '#'.repeat(Number(b.type[1]))+' '+b.text;
    if(b.type==='meta')return '> '+b.text;
    if(b.type==='li')return '- '+b.text;
    if(b.type==='link')return `[${b.text.replace(/\[/g,'（').replace(/\]/g,'）')}](${b.url})`;
    return b.bold?'**'+b.text+'**':b.text;
  }).join('\n\n')+'\n';
  const index=['# 热点授课资料目录',`共 ${topics.length} 套；原有 ${payload.source_coverage.original_lessons} 个热点、新增 ${payload.source_coverage.supplemental_lessons} 个主题。资料截至 ${payload.source_coverage.teaching_until}。`,
    '每套包含教师详稿、学生练习单和课件提纲。学生版不含答案；教师稿含参考答案与课堂追问。均为教研稿，授课前请结合班型试讲。',
    '新资料中一篇图片文章仅作延伸阅读，一篇已被纠正的旧闻仅作纠错对照，相关说明随讲义保留。'];
  for(const category of payload.categories){
    index.push('## '+category.name,'| 课程 | 教师稿 | 学生练习 | 课件提纲 |','| --- | --- | --- | --- |');
    for(const topic of topics.filter(t=>t.category===category.name)){
      const names={};
      for(const mode of ['teacher','student','slides']){
        const name=topic.topic_id+'-'+mode+'.md';
        const content=markdown(M.build([topic],mode,{useDraft:false}));
        fs.writeFileSync(path.join(out,name),content);
        files[name]=hash(content);names[mode]=name;
      }
      index.push(`| ${topic.lesson.title} | [打开](${names.teacher}) | [打开](${names.student}) | [打开](${names.slides}) |`);
    }
  }
  const indexContent=index.join('\n\n').replace(/\|\n\n(?=\|)/g,'|\n')+'\n';
  fs.writeFileSync(path.join(out,'index.md'),indexContent);files['index.md']=hash(indexContent);
  fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({generated_at:payload.generated_at,
    lesson_count:topics.length,student_answers:false,source_payload_sha256:hash(fs.readFileSync(payloadPath)),files},null,2)+'\n');
  console.log(`${topics.length} 套本地讲义、${Object.keys(files).length-1} 份材料与目录已生成。`);
})().catch(e=>{console.error(e);process.exitCode=1;});
