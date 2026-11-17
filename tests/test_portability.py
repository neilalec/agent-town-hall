import contextlib
import importlib.metadata
import concurrent.futures
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from agent_chat import cli as chat


class PortabilityTests(unittest.TestCase):
    def test_installed_distribution_identity(self):
        dist=importlib.metadata.distribution('agent-town-hall')
        self.assertEqual(dist.version,'0.1.1')
        self.assertEqual(dist.metadata['Name'],'agent-town-hall')
        self.assertEqual(dist.metadata['Author'],'Neil Massella')
        self.assertEqual(dist.metadata['License-Expression'],'MIT')
        self.assertIn('LICENSE',dist.metadata.get_all('License-File'))
        license_file=next(f for f in dist.files if str(f).endswith('/licenses/LICENSE'))
        self.assertIn('Copyright (c) 2026 Neil Massella',dist.locate_file(license_file).read_text())
        self.assertIn('Repository, https://github.com/neilalec/agent-town-hall',dist.metadata.get_all('Project-URL'))
        self.assertTrue(any(e.name=='agent-chat' and e.value=='agent_chat.cli:main' for e in dist.entry_points))

    def test_public_feed_branding(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=chat.connect(Path(tmp)/'test.sqlite3')
            try:
                with contextlib.redirect_stdout(io.StringIO()) as out:chat.feed(db,follow=False)
                self.assertIn('Agent Town Hall conversation feed (read-only)',out.getvalue())
            finally:db.close()

    def test_platform_defaults(self):
        home=Path(tempfile.gettempdir())/'example-home'
        self.assertEqual(chat.default_db_path('darwin',{},home),home/'Library/Application Support/agent-chat/chat.sqlite3')
        self.assertEqual(chat.default_db_path('linux',{},home),home/'.local/share/agent-chat/chat.sqlite3')
        self.assertEqual(chat.default_db_path('linux',{'XDG_DATA_HOME':'relative'},home),home/'.local/share/agent-chat/chat.sqlite3')
        root=home/'custom-data'
        self.assertEqual(chat.default_db_path('linux',{'XDG_DATA_HOME':str(root)},home),root/'agent-chat/chat.sqlite3')
        self.assertEqual(chat.default_db_path('win32',{'LOCALAPPDATA':str(root)},home),root/'agent-chat/chat.sqlite3')
        self.assertEqual(chat.default_db_path('win32',{},home),home/'AppData/Local/agent-chat/chat.sqlite3')

    def test_environment_and_cli_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path=Path(tmp)/'env.sqlite3';override=Path(tmp)/'override.sqlite3'
            with patch.dict(os.environ,{'AGENT_CHAT_DB':str(env_path)}):
                self.assertEqual(chat.parser().parse_args(['init']).db,env_path)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(chat.main(['--db',str(override),'init']),0)
                self.assertTrue(override.exists());self.assertFalse(env_path.exists())

    def test_initialization_retries_only_lock_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'chat.sqlite3'
            real=chat._connect_once
            errors=[sqlite3.OperationalError('database is locked'), None]
            def attempt(p,t):
                error=errors.pop(0)
                if error: raise error
                return real(p,t)
            with patch.object(chat,'_connect_once',side_effect=attempt), patch.object(chat.time,'sleep') as sleep:
                db=chat.connect(path); db.close(); self.assertEqual(sleep.call_count,1)
            with patch.object(chat,'_connect_once',side_effect=sqlite3.OperationalError('bad schema')), patch.object(chat.time,'sleep') as sleep:
                with self.assertRaises(sqlite3.OperationalError):chat.connect(path)
                sleep.assert_not_called()

    def test_invalid_utf8_body_is_json_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            body=Path(tmp)/'invalid.md';body.write_bytes(bytes([255,254,255]))
            database=Path(tmp)/'not-created.sqlite3'
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code=chat.main(['--db',str(database),'--agent','builder','send','--to','reviewer','--file',str(body)])
            self.assertEqual(code,2)
            self.assertFalse(json.loads(out.getvalue())['ok'])
            self.assertFalse(database.exists())

    def test_home_expansion(self):
        self.assertEqual(chat.default_db_path(env={'AGENT_CHAT_DB':'~/agent-example.sqlite3'}),Path.home()/'agent-example.sqlite3')

    def test_auto_initialization_and_nonvendor_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'shared data #' / 'messages.sqlite3'
            out=io.StringIO()
            with contextlib.redirect_stdout(out):
                code=chat.main(['--db',str(path),'--agent','builder-7','send','--to','review_team','--body','hello'])
            self.assertEqual(code,0);self.assertTrue(path.exists())
            db=chat.connect_feed(path)
            try:
                rows,_=chat.feed_history(db,50);self.assertEqual(rows[0]['sender'],'builder-7')
                with self.assertRaises(sqlite3.OperationalError):db.execute('DELETE FROM messages')
            finally:db.close()

    def test_feed_missing_parent_does_not_initialize(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'not-created';path=folder/'missing.sqlite3'
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(chat.main(['--db',str(path),'feed','--no-follow']),3)
            self.assertFalse(folder.exists());self.assertFalse(json.loads(out.getvalue())['ok'])

    def test_control_characters_escaped_only_in_feed(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=chat.connect(Path(tmp)/'test.sqlite3')
            try:
                body='line 1\nline 2\tend'+chr(27)+'[2J'+chr(13)+'hidden'+chr(7)
                chat.post(db,'builder','reviewer','Example',body)
                out=io.StringIO()
                with contextlib.redirect_stdout(out):chat.feed(db,follow=False)
                self.assertNotIn(chr(27),out.getvalue());self.assertIn(r'\x1b[2J',out.getvalue())
                self.assertIn('line 1\nline 2\tend',out.getvalue())
                self.assertEqual(chat.receive(db,'reviewer',mark=False)[0]['body'],body)
                self.assertEqual(chat.unread_count(db,'reviewer'),1)
            finally:db.close()

    def test_fresh_database_concurrent_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'new folder'/'shared.sqlite3'
            def send(i):
                p=subprocess.run([sys.executable,'-m','agent_chat','--db',str(path),'--agent',f'worker-{i}','send','--to','reviewer','--body',f'message {i}'],capture_output=True,text=True,encoding='utf-8',timeout=45)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                return json.loads(p.stdout)['message']['id']
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                ids=list(pool.map(send,range(24)))
            self.assertEqual(len(set(ids)),24)
            db=chat.connect(path)
            try:
                self.assertEqual(chat.unread_count(db,'reviewer'),24)
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:db.close()

    def test_identifiers_and_finite_waits(self):
        for invalid in ['A','two words','../agent','', 'a'*65]:
            with self.assertRaises(Exception):chat.agent_name(invalid)
        with tempfile.TemporaryDirectory() as tmp:
            db=chat.connect(Path(tmp)/'test.sqlite3')
            try:
                for invalid in [float('nan'),float('inf'),-.1]:
                    with self.assertRaises(chat.ChatError):chat.watch(db,'builder',invalid,.1)
                    with self.assertRaises(chat.ChatError):chat.feed(db,interval=invalid)
            finally:db.close()

    def test_database_path_with_spaces_and_unicode_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/('messages \u03bb #1' + (' ?' if os.name!='nt' else ''))/ 'chat.sqlite3'
            db=chat.connect(path)
            try:
                chat.post(db,'one','two','','Unicode \u2192 exact')
                ro=chat.connect_feed(path)
                try:self.assertEqual(chat.feed_history(ro,1)[0][0]['body'],'Unicode \u2192 exact')
                finally:ro.close()
            finally:db.close()


if __name__=='__main__':unittest.main()
