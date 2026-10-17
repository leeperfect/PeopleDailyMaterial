/* Original editorial illustrations. Decorative themes, never news photographs. */
'use strict';
window.LessonVisuals=(()=>{
 const svg=(body,cls='')=>`<svg class="${cls}" viewBox="0 0 320 170" fill="none" aria-hidden="true">${body}</svg>`;
 const art={
  care:svg('<circle cx="160" cy="82" r="68" fill="var(--cover-wash)"/><path d="M160 125s-61-35-61-71c0-32 44-40 61-10 17-30 61-22 61 10 0 36-61 71-61 71Z" fill="var(--cover-accent)"/><path d="M60 124h54l28 22h43l28-22h48M71 106l40 18m138-18-40 18" stroke="var(--cover-ink)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>'),
  book:svg('<circle cx="239" cy="39" r="23" fill="var(--cover-accent)"/><path d="M52 25c36-6 69 2 108 23 39-21 72-29 108-23v112c-40-4-74 0-108 20-34-20-68-24-108-20Z" fill="var(--cover-paper)" stroke="var(--cover-ink)" stroke-width="3"/><path d="M160 48v109M75 52c24 0 42 5 63 16M75 75c24 0 42 5 63 16M75 98c24 0 42 5 63 16M185 68c21-11 39-16 63-16M185 91c21-11 39-16 63-16M185 114c21-11 39-16 63-16" stroke="var(--cover-ink)" stroke-width="3" stroke-linecap="round"/><path d="M219 24v63l12-9 12 5V21" fill="var(--cover-accent)"/>'),
  city:svg('<circle cx="244" cy="38" r="28" fill="var(--cover-accent)"/><path d="M30 150V71l62-36v115M113 150V18h73v132M208 150V77h80v73" fill="var(--cover-paper)" stroke="var(--cover-ink)" stroke-width="3"/><path d="M132 42h35m-35 23h35m-35 23h35M53 84h17m-17 22h17m-17 22h17m163-31h30m-30 22h30M149 150v-36M21 153h278" stroke="var(--cover-ink)" stroke-width="4" stroke-linecap="round"/><path d="M16 163h288" stroke="var(--cover-accent)" stroke-width="7" stroke-linecap="round"/>'),
  lens:svg('<rect x="39" y="20" width="196" height="123" rx="14" fill="var(--cover-paper)" stroke="var(--cover-ink)" stroke-width="3"/><path d="M39 51h196M60 36h2m12 0h2m12 0h2M62 77h67m-67 18h46m-46 18h56" stroke="var(--cover-ink)" stroke-width="4" stroke-linecap="round"/><circle cx="195" cy="91" r="48" fill="var(--cover-wash)" stroke="var(--cover-ink)" stroke-width="6"/><path d="m230 127 35 32" stroke="var(--cover-accent)" stroke-width="18" stroke-linecap="round"/><path d="m176 91 13 13 26-27" stroke="var(--cover-accent)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'),
  growth:svg('<path d="M34 149h260M58 148V99h42v49m28 0V66h42v82m28 0V31h42v117" fill="var(--cover-paper)" stroke="var(--cover-ink)" stroke-width="3" stroke-linejoin="round"/><path d="m45 71 64-28 55 2 89-33m-25-7 29 5-8 28" stroke="var(--cover-accent)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="269" cy="113" r="30" fill="var(--cover-accent)"/><path d="M269 98v30m-9-24h16m-16 16h16" stroke="var(--cover-paper)" stroke-width="3" stroke-linecap="round"/>'),
  leaf:svg('<circle cx="161" cy="83" r="73" fill="var(--cover-wash)"/><path d="M155 146c-69-5-85-54-73-105 46-1 82 34 73 105Z" fill="var(--cover-accent)"/><path d="M159 123c-6-76 32-105 89-103 1 64-33 103-89 103Z" fill="var(--cover-ink)"/><path d="m160 155-47-79m45 68 56-92" stroke="var(--cover-paper)" stroke-width="3" stroke-linecap="round"/><path d="M77 157h166" stroke="var(--cover-ink)" stroke-width="3" stroke-linecap="round"/>'),
  culture:svg('<circle cx="161" cy="85" r="69" stroke="var(--cover-ink)" stroke-width="3"/><circle cx="161" cy="85" r="47" fill="var(--cover-accent)"/><path d="m22 109 87-55 57 106 77-118 61 64" stroke="var(--cover-ink)" stroke-width="3" stroke-linejoin="round"/><circle cx="46" cy="41" r="12" fill="var(--cover-accent)"/><circle cx="281" cy="143" r="10" fill="var(--cover-ink)"/>'),
 };
 const families=[
  {id:'education',label:'教育成长',match:/教育|青年/,art:'book',lines:['让成长','真正发生']},
  {id:'digital',label:'数字生活',match:/数字|网络/,art:'lens',lines:['多问一句','为什么']},
  {id:'care',label:'民生服务',match:/民生|公共服务/,art:'care',lines:['看见需求','回应期待']},
  {id:'governance',label:'基层治理',match:/治理|公共安全|监管/,art:'city',lines:['规则之中','看见人']},
  {id:'economy',label:'经济发展',match:/经济|产业|市场|乡村/,art:'growth',lines:['读懂变化','看见发展']},
  {id:'ecology',label:'生态环境',match:/生态/,art:'leaf',lines:['留一片绿','给未来']},
  {id:'culture',label:'文化社会',match:/文化|体育|国际/,art:'culture',lines:['从一个故事','看见更远']},
 ];
 const special={N06:['看见需要','也看见尊严'],N01:['答案很漂亮','真的学会了吗'],N18:['从一纸清单','到一次办成'],N29:['好规则','也要防走样'],N14:['时间表外','也有好教学'],N03:['先问证据','再下结论']};
 function family(t){const category=t.category||'';return (/生态/.test(category)?families.find(f=>f.id==='ecology'):families.find(f=>f.match.test(category)))||families[6];}
 function cover(t,i){const f=family(t),lines=special[t.lesson?.editorial_key]||f.lines;return `<div class="pin-cover cover-${f.id} cover-size-${i%3}" aria-hidden="true"><span class="cover-category">${f.label} / 课堂案例</span><div class="cover-title">${lines.map(s=>`<span>${s}</span>`).join('')}</div>${art[f.art]}<span class="cover-caption">一个热点 · 一种思考</span></div>`;}
 const paths={home:'M3 10 12 3l9 7v10h-6v-7H9v7H3Z',fresh:'m13 2-9 12h7l-1 8 10-13h-7Z',catalog:'M3 3h7v7H3Zm11 0h7v7h-7ZM3 14h7v7H3Zm11 0h7v7h-7Z',pack:'M5 3h14v19l-7-5-7 5Z',recent:'M3 5v5h5M3 10a9 9 0 1 1 1 8m8-13v7l4 2',daily:'M4 5h16v16H4ZM7 2v6m10-6v6M4 11h16m-12 4h3m3 0h3',weekly:'M4 4h16v17H4ZM8 2v4m8-4v4M7 10h10M7 14h10m-10 4h6',themes:'M3 7h7l2-3h9v16H3Z',ranking:'M4 21V11h4v10m2 0V3h4v18m2 0v-7h4v7',guide:'M12 17h.01M9 8a3 3 0 0 1 6 0c0 2-3 2-3 5M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0'};
 function decorateNav(){document.querySelectorAll('[data-nav]').forEach(a=>a.insertAdjacentHTML('afterbegin',`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true"><path d="${paths[a.dataset.nav]}"/></svg>`));}
 return {families,family,cover,decorateNav};
})();
