#!/usr/bin/env python3
"""Compile individually authored lesson briefs; never infer facts from topic names."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data/hotspot_teaching/editorial/full-coverage'
EDITORIAL = ROOT / 'data/hotspot_teaching/editorial'


def compile_lesson(spec: dict, register: dict, inventory: dict) -> dict:
    refs = [register[key] for key in spec['sources']]
    ids = list(dict.fromkeys(ref['article_id'] for ref in refs))
    original = inventory.get(spec['key'])
    topic_id = original['topic_id'] if original else 'peopleapp_hotspot_lesson_' + hashlib.sha256(spec['key'].encode()).hexdigest()[:10]
    facts = []
    for fact in spec['facts']:
        if isinstance(fact, str):
            facts.append({'text': fact, 'source_ids': ids})
        else:
            facts.append({'text': fact['text'], 'source_ids': [register[key]['article_id'] for key in fact['sources']]})
    analysis = spec['analysis']
    if len(analysis) != 3 or len(spec['discussion']) < 2 or len(facts) < 2:
        raise ValueError(f"授课内容不完整：{spec['key']}")
    if any(len(text) < 45 for _, text in analysis):
        raise ValueError(f"机制分析过短：{spec['key']}")
    interactions = [{'question':q, 'likely_answer':wrong, 'follow_up':follow, 'answer':answer,
                     'check':'观察能否回应追问，并把理由与本课事实联系起来。'}
                    for q, wrong, follow, answer in spec['discussion']]
    quick = [spec['opening'], '先看资料。' + ''.join(f['text'] for f in facts),
             *[text for _, text in analysis],
             '落实到行动，可以这样安排：' + '；'.join(spec['actions']) + '。',
             spec['boundary'] + spec['transfer']]
    return {
        'topic_id':topic_id, 'title':spec['title'], 'subtitle':spec['subtitle'],
        'version':'2026-09-13.2', 'review_status':'editorial_preview',
        'courses':['面试综合分析','申论对策展开','申论案例运用'],
        'focus':spec['focus'] if 'focus' in spec else spec['transfer'],
        'misconception':spec['discussion'][0][1], 'takeaway':spec['transfer'],
        'source_ids':ids, 'facts':facts,
        'viewpoints':[{'text':spec['viewpoint'], 'source_id':ids[0]}],
        'quick_script':quick, 'chain':spec['chain'],
        'segments':[
            {'title':'用具体处境进入材料','minutes':2,
             'script':spec['opening']+'请两位学生先给出判断，再读出事实卡中的时间、范围和处置阶段。把尚未查明的内容留在问题栏，不补写结果。',
             'board':'已知事实｜待核对问题'},
            {'title':analysis[0][0],'minutes':2,'script':analysis[0][1]+'请学生回答：'+interactions[0]['question']+'若出现“'+interactions[0]['likely_answer']+'”的答法，追问：'+interactions[0]['follow_up'],
             'board':' → '.join(spec['chain'][:2])},
            {'title':analysis[1][0],'minutes':3,'script':analysis[1][1]+'请学生用“因为……所以……”补全机制解释，再讨论：'+interactions[1]['question']+'参考要点：'+interactions[1]['answer'],
             'board':analysis[1][0]},
            {'title':analysis[2][0],'minutes':2,'script':analysis[2][1]+'对策检查：'+'；'.join(spec['actions'])+'。请学生选一条，说清主体、动作和如何观察效果。',
             'board':'主体｜动作｜效果'},
            {'title':'收束与迁移检验','minutes':1,'script':spec['transfer']+'请学生用一句话完成总结。最后说明材料边界：'+spec['boundary'],
             'board':spec['chain'][-1]}
        ],
        'interactions':interactions,
        'exercises':[
            {'kind':'面试模拟题','prompt':spec['interview']['prompt'],'requirement':'准备2分钟，作答2分钟。说明作用机制，并回应一个实施边界。',
             'answer':spec['interview']['answer'],'points':[analysis[0][0],analysis[1][0],'建议具体，并保留事实与适用范围限定']},
            {'kind':'申论模拟练习','prompt':spec['writing']['prompt'],'requirement':'不超过180字。围绕题目要求组织要点，避免空泛表态。',
             'answer':spec['writing']['answer'],'points':['紧扣设问，提炼本课具体问题','要点之间有因果或实施顺序','不扩大来源事实，不以口号代替动作']}
        ],
        'slides':[
            {'title':spec['subtitle'],'bullets':[spec['opening']],'notes':'以课堂情境提问，暂缓给出结论；情境与新闻事实分开。'},
            {'title':'本课事实与材料范围','bullets':[f['text'] for f in facts],'notes':spec['boundary']},
            {'title':'怎样把判断讲清楚','bullets':spec['chain'],'notes':'\n'.join(text for _, text in analysis[:2])},
            {'title':'将原则变成具体安排','bullets':spec['actions'],'notes':analysis[2][1]},
            {'title':'课堂追问与方法迁移','bullets':[q['question'] for q in interactions]+[spec['transfer']],
             'notes':'\n'.join(q['answer'] for q in interactions)}
        ],
        'editorial_key':spec['key'],
        'topic_category':original['category'] if original else spec['category'],
        'is_supplement':not bool(original),
        'usage_boundary':spec['boundary'],
    }


def main() -> None:
    register = json.loads((WORK/'source-register.json').read_text())
    inventory = {t['key']:t for t in json.loads((WORK/'inventory.json').read_text())['topics']}
    specs = [row for file in sorted(WORK.glob('lessons-*.json')) for row in json.loads(file.read_text())]
    keys = [s['key'] for s in specs]
    if len(keys) != len(set(keys)):
        raise ValueError('授课编号重复')
    lessons = [compile_lesson(s, register, inventory) for s in specs]
    pilots = json.loads((EDITORIAL/'lesson-pilots.json').read_text())['lessons']
    if {l['topic_id'] for l in lessons} & {l['topic_id'] for l in pilots}:
        raise ValueError('新资料不得覆盖保留的三张原授课样板')
    pins = json.loads((EDITORIAL/'source-snapshot.json').read_text())
    wanted = {aid for l in lessons for aid in l['source_ids']}
    registered = {r['article_id']:r for r in register.values()}
    observed = {}
    for db in ('data/core/articles.sqlite','data/peopleapp_opinion/core/articles.sqlite'):
        conn = sqlite3.connect(f'file:{ROOT/db}?mode=ro',uri=True)
        for aid in wanted:
            row = conn.execute('SELECT content FROM articles WHERE article_id=?',(aid,)).fetchone()
            if row:
                observed[aid] = hashlib.sha256(row[0].encode()).hexdigest()
        conn.close()
    for aid in wanted:
        expected = registered[aid]['sha256']
        if observed.get(aid) != expected:
            raise ValueError(f'阅读后来源已变化，需重新核对：{aid}')
        if aid in pins and pins[aid] != expected:
            raise ValueError(f'旧来源快照发生变化，不自动覆盖：{aid}')
        pins[aid] = expected
    (EDITORIAL/'lesson-library.json').write_text(json.dumps({'schema_version':1,'lessons':lessons},ensure_ascii=False,indent=2)+'\n')
    (EDITORIAL/'source-snapshot.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n')
    reviews = {
        register['F01']['article_id']: {
            'status':'image_reference',
            'note':'图片延伸阅读：本地没有图内可核对文字，未引用校长发言；对应课程依据另一篇可读正文编写。',
        },
        register['F47']['article_id']: {
            'status':'superseded',
            'note':'旧闻已纠正：9月12日材料援引警方通报，资助女生与催捐威胁故事系编造。此旧文仅用于信息纠错训练，不能作为真实事件引用。',
            'correction_id':register['F03']['article_id'],
            'correction_title':register['F03']['title'],
            'correction_url':register['F03']['source_url'],
        },
    }
    (EDITORIAL/'source-review.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n')
    covered = {l['topic_id'] for l in lessons+pilots}
    remaining = [t['title'] for t in inventory.values() if t['topic_id'] not in covered]
    fresh = set(row['article_id'] for row in json.loads((WORK/'inventory.json').read_text())['fresh_articles'])
    result = {'lessons':len(lessons)+len(pilots),'original_topics':len(inventory),
              'original_covered':len(inventory)-len(remaining),'remaining_topics':remaining,
              'fresh_articles':len(fresh),'fresh_covered':len(fresh & wanted),
              'sources_verified':len(wanted)}
    result.update({'supplemental_lessons':sum(l['is_supplement'] for l in lessons),
                   'fresh_image_references':1,'fresh_corrected_sources':1})
    (WORK/'coverage-progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
