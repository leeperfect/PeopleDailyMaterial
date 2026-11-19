"""分享隐私、第三系列封面与归档路径：只用临时资料。"""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from modules import writing_workflow as writing
from scripts import build_hotspot_magazine_site as hotspot_site, build_idea_magazine_site as idea_site
from scripts import export_content_ideas as tables
from scripts.rebuild_article_database import merge_records


class FollowupSafety(unittest.TestCase):
    def test_notes_stay_local(self):
        sentinel = 'PrivateNote_只可在本机看'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            idea = idea_site.load_source_module()
            idea.ASSET_DB, idea.ARTICLE_DB = root/'asset.sqlite', root/'unused.sqlite'
            with closing(sqlite3.connect(idea.ASSET_DB)) as c:
                c.execute('CREATE TABLE content_ideas(idea_id PRIMARY KEY,date,title,angle,platform,status,priority,outline_json,support_article_ids_json,created_at,updated_at)')
                c.execute("INSERT INTO content_ideas VALUES ('a','2026-05-20','主题','角度','公众号','备选','B','[]','[]','','')")
                c.row_factory = sqlite3.Row
                idea.ensure_note_table(c)
                c.execute("INSERT INTO content_idea_notes VALUES ('a',1,?,'')", (sentinel,)); c.commit()
                c.row_factory = sqlite3.Row
                rows = [tables.idea_record(r,{}) for r in tables.fetch_ideas(c,None,None)]
                self.assertNotIn(sentinel,tables.build_markdown(rows)); tables.write_csv(root/'ideas.csv',rows)
                self.assertNotIn(sentinel,(root/'ideas.csv').read_text(encoding='utf-8-sig'))
            hot = hotspot_site.load_source_module(); hot.TOPIC_DB = root/'topics.sqlite'
            with closing(sqlite3.connect(hot.TOPIC_DB)) as c:
                c.execute('CREATE TABLE hotspot_topics(topic_id,topic,category,angle,status,priority,media_count,article_count,start_date,end_date,sources_json,ai_brief,manual_note,selected)')
                c.execute('CREATE TABLE hotspot_topic_articles(topic_id,article_id,date,source_name,title,url)')
                c.execute("INSERT INTO hotspot_topics VALUES ('h','主题','分类','角度','热点','A',1,1,'','','[]','教研材料',?,1)",(sentinel,)); c.commit()
            for builder, module, loader, key, note in [(idea_site,idea,idea.idea_payload,'ideas','user_note'),(hotspot_site,hot,hot.topic_payload,'topics','manual_note')]:
                self.assertEqual(loader()[key][0][note],sentinel)
                self.assertIn(sentinel.lower(),loader()[key][0]['searchable'])
                item = loader(share=True)[key][0]
                self.assertNotIn(note,item); self.assertTrue(item['selected'])
                with patch.object(builder,'load_source_module',return_value=module):
                    builder.build_site(root/'snapshot.html')
                self.assertNotIn(sentinel.lower(),(root/'snapshot.html').read_text().lower())

    def test_method_series_cover_never_falls_back_to_another_series(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(writing,'PROJECT_ROOT',Path(tmp)):
            p = Path(tmp)/'申论方法系列'/'谈人民日报.md'; cover = Path(tmp)/'本文.png'; cover.touch()
            metadata = {'title':'人民日报', 'series_no':1}; config={'covers':{'people_daily':'其他.png'}}
            self.assertEqual(writing.detect_series(p,metadata),'shenlun_method')
            with self.assertRaisesRegex(ValueError,'wechat_cover'):writing.cover_for_article(p,metadata,config)
            self.assertEqual(writing.cover_for_article(p,dict(metadata,wechat_cover='本文.png'),config),cover.resolve())
            with self.assertRaises(ValueError):writing.cover_for_article(p,dict(metadata,wechat_cover='../其他.png'),config)

    def test_actual_note_path_wins_without_changing_original_text(self):
        row, = merge_records({'id':{'markdown_path':'现路径','content':'阅读视图'}},{'id':{'markdown_path':'旧路径','content':'原始正文'}})
        self.assertEqual((row['markdown_path'],row['content']),('现路径','原始正文'))
