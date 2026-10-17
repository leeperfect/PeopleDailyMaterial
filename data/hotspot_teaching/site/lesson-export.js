(function(root) {
  'use strict';
  let loading;
  function library() {
    if (root.docx) return Promise.resolve(root.docx);
    if (!loading) loading = new Promise((resolve,reject) => {
      const script=document.createElement('script'); script.src='./vendor/docx-9.6.1.js';
      script.onload=()=>root.docx ? resolve(root.docx) : reject(new Error('讲义组件未载入'));
      script.onerror=()=>{loading=null;script.remove();reject(new Error('Word组件读取失败，请重试'));};
      document.head.append(script);
    });
    return loading;
  }
  function documentFromBlocks(blocks,d) {
    const {Document,Paragraph,TextRun,ExternalHyperlink,PageBreak,Footer,PageNumber}=d;
    const children=blocks.map(s=>{
      if(s.type==='page') return new Paragraph({children:[new PageBreak()]});
      if(s.type==='space') return new Paragraph({children:[new TextRun('作答区'),...Array.from({length:4},()=>new TextRun({break:1,text:'________________________________________________________________'}))],keepLines:true,spacing:{line:420,after:160}});
      let runs=[new TextRun({text:s.text,bold:s.bold || false})];
      if(s.type==='link'&&/^https?:\/\//.test(s.url)) runs=[new ExternalHyperlink({link:s.url,children:[new TextRun({text:s.text,style:'Hyperlink'})]})];
      const style=({title:'Title',h1:'Heading1',h2:'Heading2',h3:'Heading3',meta:'Caption'})[s.type];
      return new Paragraph({children:runs,style,numbering:s.type==='li'?{reference:'teaching-bullets',level:0}:undefined,keepNext:s.keepNext || ['title','h1','h2','h3'].includes(s.type),widowControl:true,spacing:{after:s.type==='meta'?140:160,line:340}});
    });
    return new Document({creator:'热点教学日报',title:blocks.find(b=>b.type==='title')?.text || '教学讲义',
      numbering:{config:[{reference:'teaching-bullets',levels:[{level:0,format:d.LevelFormat.BULLET,text:'•',alignment:'left',style:{run:{font:'Arial',size:18},paragraph:{indent:{left:340,hanging:220}}}}]}]},
      styles:{default:{document:{run:{font:{name:'Microsoft YaHei',eastAsia:'Microsoft YaHei'},size:23,color:'000000'},paragraph:{spacing:{line:340,after:140}}}},paragraphStyles:[
        {id:'Title',name:'Title',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:36,bold:true,color:'000000'},paragraph:{keepNext:true,spacing:{before:0,after:220}}},
        ...[1,2,3].map((n)=>({id:`Heading${n}`,name:`Heading ${n}`,basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:30-n*2,bold:true,color:'000000'},paragraph:{keepNext:true,spacing:{before:240,after:120}}})),
        {id:'Caption',name:'Caption',basedOn:'Normal',run:{size:20,color:'555555'}}]},
      sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1080,bottom:1080,left:1080,right:1080}}},footers:{default:new Footer({children:[new Paragraph({alignment:'center',children:[new TextRun({text:'热点教学日报  ·  ',size:18}),new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},children}]});
  }
  async function word(blocks) { const d=await library(); return d.Packer.toBlob(documentFromBlocks(blocks,d)); }
  function download(blob,name) {const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);}
  async function copy(blocks,rich=true) {
    const m=root.LessonModel, text=m.plain(blocks);
    if(rich && navigator.clipboard?.write && root.ClipboardItem) {
      try {await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([m.html(blocks)],{type:'text/html'}),'text/plain':new Blob([text],{type:'text/plain'})})]);return 'rich';}catch(_){}
    }
    if(navigator.clipboard?.writeText) {try {await navigator.clipboard.writeText(text);return 'plain';}catch(_){}}
    const area=document.createElement('textarea');area.value=text;area.style.cssText='position:fixed;opacity:0';document.body.append(area);area.select();const ok=document.execCommand('copy');area.remove();if(!ok)throw new Error('复制未成功，请在预览中选择文字复制');return 'plain';
  }
  function print(blocks) {
    let frame=document.querySelector('#printFrame');if(frame)frame.remove();
    frame=document.createElement('iframe');frame.id='printFrame';frame.title='打印讲义';frame.setAttribute('aria-hidden','true');frame.tabIndex=-1;frame.style.cssText='position:fixed;width:1px;height:1px;right:0;bottom:0;border:0';document.body.append(frame);
    const doc=frame.contentDocument;doc.open();doc.write(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>教学讲义</title><style>@page{size:letter;margin:20mm}body{font:12pt/1.8 'PingFang SC','Microsoft YaHei',sans-serif;color:#000}h1,h2,h3{break-after:avoid}p,li{orphans:2;widows:2}a{overflow-wrap:anywhere}.page-break{break-before:page}h1{font-size:20pt!important}.answer-space{height:120px!important}</style></head><body>${root.LessonModel.html(blocks)}</body></html>`);doc.close();
    const ready=doc.fonts?.ready || Promise.resolve();ready.then(()=>{frame.contentWindow.focus();frame.contentWindow.print();});
  }
  const api={documentFromBlocks,word,copy,download,print};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.LessonExport=api;
})(typeof window==='undefined'?globalThis:window);
