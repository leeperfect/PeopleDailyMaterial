"""资料保全、只读检索与断点重试；所有资料在临时目录，外部服务均替身。"""
import io
import json
import os
import sqlite3
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from main import PeopleDailyMaterialSystem
from modules.article_database import ArticleStore
from modules.markdown_writer import MarkdownWriter
from modules.notion import NotionAPI
from modules.utils import safe_json_dump


class CoreAuditTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(tmp.name)
        for path in ('data/raw', 'data/processed'):
            Path(path).mkdir(parents=True)
        self.store = ArticleStore('test.sqlite')
        self.addCleanup(self.store.close)
        self.system = PeopleDailyMaterialSystem.__new__(PeopleDailyMaterialSystem)
        self.system.article_store = self.store
        self.date = datetime(2026, 11, 19)

    def record(self, number):
        return {'url': f'https://paper.people.com.cn/rmrb/pc/content/202611/19/content_{number}.html',
                'title': f'标题{number}', 'date': '2026-11-19', 'content': '正文'}

    def test_merge_partial_day_and_preserve_prior_fields(self):
        one, two = self.record(1), self.record(2)
        self.system.save_articles_local([{**one, 'extra': '留存字段'}], self.date)
        self.system.save_articles_local([two, {**one, 'content': '新版'}], self.date)
        self.system.save_articles_local([], self.date)
        rows = self.system._daily_raw(self.date)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['extra'], '留存字段')
        self.assertEqual(rows[0]['content'], '新版')
        self.assertEqual(rows[1], two)
        self.assertEqual(self.store.stats()['article_count'], 2)
        self.assertEqual(len(json.loads(Path('data/processed/articles_20261119.json').read_text())), 2)

    def test_invalid_existing_archive_and_unserializable_data_not_truncated(self):
        path = Path('data/raw/articles_20261119.json')
        path.write_text('损坏但可抢救')
        with self.assertRaises(ValueError):
            self.system.save_articles_local([self.record(1)], self.date)
        self.assertFalse(safe_json_dump([1, object()], str(path)))
        self.assertEqual(path.read_text(), '损坏但可抢救')

    def test_core_read_only_batch_rollback_and_teaching_tags(self):
        one = self.record(1)
        self.store.upsert_article(one)
        aid = self.store.get_articles()[0]['article_id']
        self.store.conn.execute('INSERT INTO article_tags VALUES (?, ?, ?)', (aid, '教研', 'manual'))
        self.store.conn.commit()
        self.store.upsert_article({**one, 'title': '改题'})
        with self.assertRaises(ValueError):
            self.store.upsert_articles([self.record(2), {**one, 'date': '非法日期值'}])
        self.assertEqual(self.store.stats()['article_count'], 1)
        ro = ArticleStore('test.sqlite', read_only=True)
        self.addCleanup(ro.close)
        self.assertEqual(ro.search('改题')[0]['article_id'], aid)
        self.assertIsNotNone(ro.conn.execute("SELECT 1 FROM article_tags WHERE tag_type='manual'").fetchone())
        with self.assertRaises(sqlite3.OperationalError):
            ro.conn.execute('DELETE FROM articles')
        with self.assertRaises(sqlite3.OperationalError):
            ArticleStore('missing/core.sqlite', read_only=True)
        self.assertFalse(Path('missing').exists())

    def test_reading_notes_not_overwritten_even_on_title_collision(self):
        one = {**self.record(1), 'plate': '第"一"版', 'keywords': ['a,b', '经济']}
        writer = MarkdownWriter()
        fn = Path(writer.save_article(one, self.date))
        with fn.open('a') as f:
            f.write('\n人工批注')
        before = fn.read_bytes()
        self.assertEqual(writer.save_article(one, self.date), str(fn))
        self.assertIsNone(writer.save_article({**one, 'url': 'different'}, self.date))
        self.assertEqual(before, fn.read_bytes())

    def test_notion_index_read_error_never_becomes_empty(self):
        api = NotionAPI.__new__(NotionAPI)
        api._data_source_id = 'target'
        api.notion = Mock()
        api.notion.data_sources.query.side_effect = OSError('未连接')
        with self.assertRaises(OSError):
            api.get_existing_articles()
        api.notion.search.assert_not_called()

    def test_bad_pagination_does_not_return_partial_index(self):
        api = NotionAPI.__new__(NotionAPI)
        api._data_source_id = 'target'
        api.notion = Mock()
        api.notion.data_sources.query.return_value = {'results': [], 'has_more': True, 'next_cursor': None}
        with self.assertRaises(RuntimeError):
            api.get_existing_articles()

    def test_atomic_notion_creation_preserves_long_content(self):
        api = NotionAPI.__new__(NotionAPI)
        api._data_source_id, api.database_id = 'source', 'db'
        api.notion = Mock()
        api.notion.pages.create.return_value = {'id': 'page'}
        text = '\n'.join(['长段' * 1700] + [str(i) for i in range(120)])
        self.assertEqual(api.create_page({**self.record(1), 'content': text}, self.date), 'page')
        payload = api.notion.pages.create.call_args.kwargs
        self.assertEqual(payload['parent'], {'data_source_id': 'source'})
        self.assertLessEqual(len(payload['children']), 100)
        body = []
        for block in payload['children']:
            parts = [v['text']['content'] for v in block['paragraph']['rich_text']]
            self.assertTrue(all(len(v.encode('utf-16-le')) <= 4000 for v in parts))
            body.append(''.join(parts))
        self.assertEqual('\n'.join(body), text)
        api.notion.blocks.children.append.assert_not_called()

    def test_explicit_notion_update_keeps_old_body_on_failure(self):
        api = NotionAPI.__new__(NotionAPI)
        api.notion = Mock()
        api.notion.blocks.children.list.side_effect = [
            {'results':[{'id':'old1'}], 'has_more':True, 'next_cursor':'cursor'},
            {'results':[{'id':'old2'}], 'has_more':False},
        ]
        api.notion.blocks.children.append.side_effect = OSError('模拟写入失败')
        self.assertFalse(api.update_page('page', self.record(1)))
        self.assertEqual(api.notion.blocks.children.list.call_count, 2)
        api.notion.blocks.delete.assert_not_called()

    def test_failed_sync_keeps_checkpoint_and_retry_reuses_raw(self):
        sys = self.system
        sys.crawler, sys.parser, sys.processor = Mock(), Mock(), Mock()
        sys.notion_api, sys.series_detector, sys.exporter = Mock(), Mock(), Mock()
        sys.crawler.crawl_all_directories.return_value = [('https://paper.people.com.cn/rmrb/pc/layout/202611/19/node_01.html', '目录')]
        sys.parser.parse_directory.side_effect = lambda _: ([{'title':'同题','href':f'content_{i}.html'} for i in (1, 2)], '版面')
        sys.parser.parse_article.side_effect = lambda _, url: {**self.record(1 if 'content_1.' in url else 2), 'url':url}
        sys.processor.clean_content.side_effect = lambda s: s
        sys.processor.extract_keywords.return_value = []
        sys.processor.extract_summary.return_value = '摘要'
        sys.processor.classify_article.return_value = '其他'
        sys.series_detector.get_summary.return_value = ''
        sys.series_detector.get_related_titles.return_value = []
        sys.notion_api.get_existing_articles.side_effect = [[], [{'id':'page-1', 'article_id':'people_daily_20261119_1', 'title':'改题'}]]
        sys.notion_api.create_page.side_effect = ['page-1', None, 'page-2']
        with patch('modules.checkpoint.CHECKPOINT_DIR','checkpoints'), patch('main.mark_date_synced') as mark, redirect_stdout(io.StringIO()):
            sys.crawl_single_date(self.date, auto_select=True)
            mark.assert_not_called()
            self.assertTrue(Path('checkpoints/task_20261119.json').exists())
            sys.crawler.crawl_article.reset_mock()
            sys.crawl_single_date(self.date, auto_select=True)
            mark.assert_called_once_with('2026-11-19')
            sys.crawler.crawl_article.assert_not_called()
            sys.notion_api.update_page.assert_not_called()
            self.assertFalse(Path('checkpoints/task_20261119.json').exists())
        self.assertEqual(self.store.stats()['article_count'], 2)
        self.assertEqual(len(self.system._daily_raw(self.date)), 2)
