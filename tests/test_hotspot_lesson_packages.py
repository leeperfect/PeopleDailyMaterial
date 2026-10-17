"""Critical contracts for source provenance, review preservation and lesson exports."""
import hashlib
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hotspot_lesson_packages as packages
import build_hotspot_teaching_daily as builder


class LessonPackagesTest(unittest.TestCase):
    def test_all_original_topics_and_fresh_sources_have_lessons(self):
        lessons = packages.load_lessons()
        inventory = json.loads((ROOT/'data/hotspot_teaching/editorial/full-coverage/inventory.json').read_text())
        self.assertFalse({t['topic_id'] for t in inventory['topics']} - lessons.keys())
        source_ids = {aid for lesson in lessons.values() for aid in lesson['source_ids']}
        self.assertFalse({a['article_id'] for a in inventory['fresh_articles']} - source_ids)
        self.assertTrue(all(l['source_check']=='matched' for l in lessons.values()))
        self.assertTrue(all(l['review_status']=='editorial_preview' for l in lessons.values()))

    def test_changed_source_never_inherits_lesson_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = json.loads(packages.EDITORIAL.read_text())['lessons'][0]
            (root/'lessons.json').write_text(json.dumps({'lessons':[sample]}))
            conn = sqlite3.connect(root/'sources.sqlite')
            conn.execute('CREATE TABLE articles(article_id,title,date,source,source_url,content)')
            for aid in sample['source_ids']:
                conn.execute('INSERT INTO articles VALUES(?,?,?,?,?,?)',(aid,'来源','2026-07-29','媒体','https://example.org','原始事实'))
            conn.commit(); conn.close()
            pins = {aid:hashlib.sha256('原始事实'.encode()).hexdigest() for aid in sample['source_ids']}
            (root/'pins.json').write_text(json.dumps(pins))
            args=(root/'lessons.json',root/'pins.json',(root/'sources.sqlite',))
            before=packages.load_lessons(*args)[sample['topic_id']]
            self.assertEqual(before['source_check'],'matched')
            conn=sqlite3.connect(root/'sources.sqlite')
            conn.execute('UPDATE articles SET content=? WHERE article_id=?',('更正后的事实',sample['source_ids'][0]))
            conn.commit();conn.close()
            after=packages.load_lessons(*args)[sample['topic_id']]
            self.assertEqual(after['review_status'],'source_changed')
            self.assertEqual(after['quick_script'],sample['quick_script'])

    def test_fact_requires_declared_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample=json.loads(packages.EDITORIAL.read_text())['lessons'][0]
            sample['source_ids']=[]
            p=Path(tmp)/'lesson.json';p.write_text(json.dumps({'lessons':[sample]}))
            with self.assertRaisesRegex(ValueError,'事实缺少有效出处'):
                packages.load_lessons(p,Path(tmp)/'missing.json',())

    def test_refresh_preserves_review_only_for_unchanged_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'db.sqlite'
            topic={'topic_id':'case-1','topic':'停车计费规则透明化','category':'城市治理与公共服务','angle':'细化计费','status':'热点','priority':'A','media_count':1,'article_count':0,'start_date':'2026-09-01','end_date':'2026-09-10','app_articles':[]}
            paper={'article_id':'paper-1','title':'停车收费','date':'2026-09-10','summary':'明确收费单位','content':'事实材料','content_hash':'original','relation_role':'治理案例','confidence':0.9,'match_reason':'具体关联'}
            with patch.object(builder,'OUTPUT_DB',path),patch.object(builder,'load_app_articles',return_value={}),patch.object(builder,'match_paper_support',return_value=[paper]):
                builder.refresh_database([topic],[])
                conn=builder.connect_output()
                conn.execute('UPDATE topic_article_links SET reviewed=1')
                conn.execute("UPDATE teaching_cards SET review_status='published',review_note='人工核对'")
                conn.execute("UPDATE daily_editions SET status='published'")
                conn.execute("UPDATE weekly_editions SET status='published'")
                original_card=tuple(conn.execute('SELECT * FROM teaching_cards').fetchone())
                days=[tuple(r) for r in conn.execute('SELECT * FROM daily_editions ORDER BY edition_date')]
                weeks=[tuple(r) for r in conn.execute('SELECT * FROM weekly_editions ORDER BY week_start')]
                conn.commit();conn.close()
                topic['angle']='新增观察角度'
                builder.refresh_database([topic],[])
                conn=builder.connect_output()
                self.assertEqual(conn.execute('SELECT reviewed FROM topic_article_links').fetchone()[0],1)
                self.assertEqual(tuple(conn.execute('SELECT * FROM teaching_cards').fetchone()),original_card)
                self.assertEqual([tuple(r) for r in conn.execute("SELECT * FROM daily_editions WHERE status='published' ORDER BY edition_date")],days)
                self.assertEqual([tuple(r) for r in conn.execute("SELECT * FROM weekly_editions WHERE status='published' ORDER BY week_start")],weeks)
                conn.close()
                paper['content_hash']='corrected'
                builder.refresh_database([topic],[])
                conn=builder.connect_output()
                self.assertEqual(conn.execute('SELECT reviewed FROM topic_article_links').fetchone()[0],0)
                self.assertEqual(tuple(conn.execute('SELECT * FROM teaching_cards').fetchone()),original_card)
                conn.close()


if __name__=='__main__': unittest.main()
