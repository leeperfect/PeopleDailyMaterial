"""维护与写作入口只用离线替身验证。"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from modules.notion import NotionAPI
from modules.writing_workflow import load_state
from scripts.notion_maintenance import create_article_page, query_pages
from scripts.rebuild_article_database import parse_scalar


class AuditGuards(unittest.TestCase):
    def test_broken_state_does_not_look_new(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / 'state.json'
            config = {'workflow_state': str(p)}
            self.assertEqual(load_state(config)['articles'], {})
            for text in ('broken', '[]', '{"articles": []}'):
                p.write_text(text)
                with self.assertRaises(ValueError):
                    load_state(config)
                self.assertEqual(p.read_text(), text)

    def test_maintenance_create_includes_id_and_body_in_same_request(self):
        api = NotionAPI.__new__(NotionAPI)
        api._data_source_id = 'source'
        api.notion = Mock()
        api.notion.pages.create.return_value = {'id': 'new'}
        self.assertEqual(create_article_page(api, {'article_id': 'A', 'title': '测试', 'content': '正文'}), 'new')
        body = api.notion.pages.create.call_args.kwargs
        self.assertEqual(body['parent'], {'data_source_id': 'source'})
        self.assertIn('Article ID', body['properties'])
        self.assertTrue(body['children'])
        api.notion.blocks.children.append.assert_not_called()

    def test_maintenance_never_accepts_ambiguous_data_source(self):
        api = NotionAPI.__new__(NotionAPI)
        api.database_id, api._data_source_id = 'db', None
        api.notion = Mock()
        api.notion.databases.retrieve.return_value = {'data_sources': [{'id':'x'}, {'id':'y'}]}
        with self.assertRaises(RuntimeError):
            query_pages(api)
        api.notion.data_sources.query.assert_not_called()

    def test_empty_text_cannot_replace_an_existing_page(self):
        api = NotionAPI.__new__(NotionAPI)
        api.notion = Mock()
        self.assertFalse(api.update_page('page', {'content': ' '}))
        self.assertFalse(api.notion.mock_calls)

    def test_current_markdown_writer_and_old_lists_both_roundtrip(self):
        value = ['带,逗号', '含"引号"', '反斜线\\']
        self.assertEqual(parse_scalar(json.dumps(value, ensure_ascii=False)), value)
        self.assertEqual(parse_scalar('[旧格式, 关键词]'), ['旧格式', '关键词'])
