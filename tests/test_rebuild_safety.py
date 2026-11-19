"""用临时资料验证重建边界，不读取真实文章或写入正式库。"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import rebuild_article_database as rebuild


class RebuildSafetyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.raw = self.root / 'raw'
        self.raw.mkdir()
        overrides = patch.multiple(rebuild, DATA_DIR=str(self.root), RAW_DIR=str(self.raw),
                                   VAULT_DIR=str(self.root / 'vault'), PROJECT_ROOT=str(self.root))
        overrides.start()
        self.addCleanup(overrides.stop)

    def test_snapshot_belongs_to_new_target(self):
        (self.raw / 'articles_20261101.json').write_text(json.dumps([{'title': '测试', 'content': '正文'}]))
        target = self.root / 'check' / 'test.sqlite'
        summary = rebuild.rebuild(str(target))
        self.assertEqual(summary['stats']['article_count'], 1)
        self.assertEqual(summary['jsonl_path'], 'check/test.jsonl')
        self.assertTrue(target.with_name('test_rebuild_manifest.json').is_file())
        self.assertFalse((self.root / 'data' / 'core').exists())
        before = target.read_bytes()
        with self.assertRaises(FileExistsError):
            rebuild.rebuild(str(target))
        self.assertEqual(before, target.read_bytes())

    def test_snapshot_alone_prevents_overwrite(self):
        (self.root / 'articles.jsonl').write_text('保留')
        with self.assertRaises(FileExistsError):
            rebuild.rebuild('articles.sqlite')
        self.assertFalse((self.root / 'articles.sqlite').exists())
        self.assertEqual((self.root / 'articles.jsonl').read_text(), '保留')

    def test_empty_or_malformed_source_does_not_create_database(self):
        target = self.root / 'check' / 'articles.sqlite'
        with self.assertRaises(ValueError):
            rebuild.rebuild(str(target))
        (self.raw / 'articles_20261101.json').write_text('not-json')
        with self.assertRaisesRegex(ValueError, 'articles_20261101.json'):
            rebuild.rebuild(str(target))
        self.assertFalse(target.parent.exists())
