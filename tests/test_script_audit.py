"""离线回归：所有资料均在临时目录；外部平台、配置、真实归档均不调用。"""
import io
import json
import sqlite3
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from modules.notion_index import AmbiguousArticleMatch, add_to_indexes, build_existing_indexes, find_duplicate
from scripts import build_hotspot_magazine_site as hotspot, build_idea_magazine_site as idea
from scripts import cleanup_local_data as cleanup, notion_maintenance as maintenance
from scripts import query_material_assets as material, serve_hotspot_teaching_daily as teaching, sync_to_notion as sync


class ScriptAudit(unittest.TestCase):
    def test_notion_identity(self):
        a = dict(article_id='a', title='同题', date='2026-05-20', url='url-1')
        b = dict(a, article_id='b', url='url-2')
        ix = build_existing_indexes([dict(a, id='page')])
        self.assertIsNone(find_duplicate(b, ix))
        with self.assertRaises(AmbiguousArticleMatch):
            find_duplicate(dict(b, url='url-1'), ix)
        self.assertEqual(find_duplicate(dict(a, title='新题'), ix)['id'], 'page')
        add_to_indexes(dict(b, article_id=''), 'old', ix)
        self.assertEqual(find_duplicate(b, ix)['id'], 'old')
        with self.assertRaises(AmbiguousArticleMatch):
            find_duplicate(dict(b, url=''), ix)
        add_to_indexes(b, 'old', ix)
        self.assertEqual(find_duplicate(b, ix)['article_id'], 'b')
        add_to_indexes(b, 'other', ix)
        with self.assertRaises(AmbiguousArticleMatch):
            find_duplicate(b, ix)

    def test_raw_fallback_honors_article_limit(self):
        with TemporaryDirectory() as tmp, patch.object(sync, 'PROJECT_ROOT', tmp), redirect_stdout(io.StringIO()):
            raw = Path(tmp) / 'data/raw'; raw.mkdir(parents=True)
            p = raw / 'articles_20260520.json'
            p.write_text(json.dumps([{'title': str(i)} for i in range(5)]))
            with patch.object(sync, 'load_articles_from_database', return_value=[{'date':'2026-05-19','title':'已入库'}]):
                rows = sync.load_articles(['20260519', '2026-05-20', '20260520'], limit=3)
            self.assertEqual([r['title'] for r in rows], ['已入库', '0', '1'])
            self.assertTrue(rows[1]['article_id'].startswith('people_daily_20260520_'))
            self.assertNotIn('article_id', p.read_text())
            self.assertEqual(len(sync.load_articles(['2026-05-20'], force_raw=True, limit=1)), 1)

    def test_sync_scope_rejected_before_connecting(self):
        bad = (['--start','2026-05-01'], ['--all','2026-05-01'], ['--limit','0'],
               ['--all','--start','2026-05-20','--end','2026-05-01'], ['--all','--end','2026-02-31'])
        for argv in bad:
            with self.subTest(argv=argv), patch.object(sys,'argv',['sync',*argv]), patch.object(sync,'sync_articles') as call, redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                try: sync.main()
                finally: call.assert_not_called()
        with patch.object(sys,'argv',['sync','--all','--start','20260501','--end','20260520','--dry-run']), patch.object(sync,'sync_articles') as call:
            sync.main()
            self.assertEqual(call.call_args.args, (None,))
            self.assertEqual(call.call_args.kwargs['start_date'], '2026-05-01')
            self.assertTrue(call.call_args.kwargs['dry_run'])

    def test_date_scoped_maintenance_honors_one_shared_limit(self):
        a = dict(article_id='a', title='同题', date='2026-05-20', url='u1')
        b = dict(a, article_id='b', url='u2')
        old = dict(a, article_id='other', date='2026-05-19')
        pages = [dict(a, id='p1'), dict(a, id='p2'), dict(a,id='blank',article_id=''),
                 dict(old,id='old1'), dict(old,id='old2')]
        plan = maintenance.classify(pages, [a,b], in_scope=lambda p:p['date']==a['date'])
        self.assertEqual(plan['duplicate_ids'], ['a'])
        self.assertEqual(plan['missing_articles'], [b])
        with patch.object(sys,'argv',['maintenance','--date',a['date'],'--archive-duplicates','--create-missing','--limit','1','--delay','0']), patch.multiple(maintenance, Config=Mock(), setup_logger=Mock(), NotionAPI=Mock(),query_pages=Mock(return_value=pages), load_local_articles=Mock(return_value=[a,b]), page_has_children=Mock(return_value=True)), patch.object(maintenance,'archive_duplicate_page') as archive, patch.object(maintenance,'create_article_page') as create, redirect_stdout(io.StringIO()):
            maintenance.main()
            archive.assert_called_once()
            self.assertEqual(archive.call_args.args[1]['id'], 'p2')
            create.assert_not_called()

    def test_search_does_not_silently_ignore_dates(self):
        from scripts import query_articles, query_peopleapp_opinion
        for module in (query_articles, query_peopleapp_opinion):
            for flags in (['--search','城市','--date','2026-05-01'], ['--limit','0']):
                with self.subTest(module=module.__name__, flags=flags), patch.object(sys,'argv',['query',*flags]), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                    module.main()
                self.assertEqual(exc.exception.code, 2)

    def test_material_lookup_cannot_create_or_write(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)/'资料 ?#.sqlite'
            with self.assertRaises(sqlite3.OperationalError): material.connect(p)
            self.assertFalse(p.exists())
            sqlite3.connect(p).close()
            conn = material.connect(p)
            try:
                with self.assertRaises(sqlite3.OperationalError): conn.execute('create table unused (id)')
            finally: conn.close()

    def test_cleanup_only_recognized_archive_names(self):
        with TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            root = Path(tmp); vault = root/'vault'; raw=root/'raw'; raw.mkdir()
            day=datetime(2026,5,20)
            keep_dirs=['2026/05/2026-05-20','2026/05/2026-05-99','2026/05/资料', '_素材库/案例/我的笔记', '2026/05/2026-06-01']
            for d in [*keep_dirs,'2026/05/2026-05-21']: (vault/d).mkdir(parents=True)
            (vault/'2027').symlink_to(vault/'2026',target_is_directory=True)
            keep_files=['articles_20260520.json','articles_20260599.json','articles_20260521.backup.json']
            for f in [*keep_files,'articles_20260521.json']: (raw/f).write_text('[]')
            cleanup.cleanup_json_files(raw,day,day); cleanup.cleanup_vault(vault,day,day)
            self.assertEqual({f.name for f in raw.iterdir()}, set(keep_files))
            self.assertTrue(all((vault/d).exists() for d in keep_dirs))
            self.assertFalse((vault/'2026/05/2026-05-21').exists())
            with patch.object(sys,'argv',['cleanup','--keep-start','2026-06-01','--keep-end','2026-05-01','--confirm-delete']), patch.object(cleanup,'cleanup_json_files') as operation, redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                try: cleanup.main()
                finally: operation.assert_not_called()

    def test_workbench_loads_only_referenced_sources_in_batches(self):
        from scripts import serve_idea_magazine as workbench
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / 'core.sqlite'
            with sqlite3.connect(p) as core:
                core.execute('CREATE TABLE articles(article_id TEXT PRIMARY KEY, title, source_url, markdown_path, date, section_name)')
                core.execute("INSERT INTO articles VALUES ('a','核心库标题','url','a.md','2026-05-20','版面')")
            core.close()
            assets = sqlite3.connect(':memory:'); assets.row_factory = sqlite3.Row
            self.addCleanup(assets.close)
            assets.execute('CREATE TABLE article_analysis(article_id, title, source_url, date)')
            assets.executemany('INSERT INTO article_analysis VALUES (?,?,?,?)', [(s,s,'url','2026-05-19') for s in ('a','b','unrelated')])
            keys = {f'其他-{i}' for i in range(550)} | {'a','b'}
            with patch.object(workbench,'ARTICLE_DB',p):
                results = workbench.load_article_map(assets, keys)
            self.assertEqual(set(results), {'a','b'})
            self.assertEqual(results['a']['title'], '核心库标题')
            self.assertEqual(results['b']['date'], '2026-05-19')

    def test_teaching_payload_reused_until_changed(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)/'data.json'; p.write_text('{"value":1}')
            with patch.object(teaching,'DATA_FILE',p):
                self.assertIs(teaching.load_payload(), teaching.load_payload())
                p.write_text('{"value":22}'); self.assertEqual(teaching.load_payload()['value'],22)
        p = {'topics':[{'topic_id':'a'},{'topic_id':'b'}], 'daily':[{'day':'d','topic_ids':['b','missing','a']}]}
        self.assertEqual([t['topic_id'] for t in teaching.edition_payload(p,'daily','day','d')['topics']],['b','a'])

    def test_both_workbenches_export_to_external_directory(self):
        with TemporaryDirectory() as tmp:
            for i,(module,method,collection,marker) in enumerate([(idea,'idea_payload','ideas','  <script>\n    const EMBEDDED_PAYLOAD'),(hotspot,'topic_payload','topics','<script>\nconst EMBEDDED_PAYLOAD')]):
                path=Path(tmp)/str(i)/'index.html'
                fake=SimpleNamespace(HTML=marker, **{method:lambda *,share:{collection:[]}})
                with patch.object(module,'load_source_module',return_value=fake):
                    self.assertEqual(module.build_site(path)['output'],str(path.resolve()))
                self.assertIn('PAYLOAD__=',path.read_text())


if __name__ == '__main__':
    unittest.main()
