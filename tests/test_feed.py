import contextlib
import io
import json
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from agent_chat import cli as chat


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='agent-feed-test-')
        self.path = Path(self.tmp.name) / 'chat.sqlite3'
        self.db = chat.connect(self.path)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_recent_history_across_agents_in_order(self):
        a = chat.post(self.db, 'codex', 'claude', 'first', 'one')
        b = chat.post(self.db, 'claude', None, '', 'two', a['id'])
        c = chat.post(self.db, 'claude', 'codex', 'next', 'three')
        db = chat.connect_feed(self.path)
        try:
            rows, watermark = chat.feed_history(db, 2)
            self.assertEqual([r['id'] for r in rows], [b['id'], c['id']])
            self.assertEqual([r['sender'] for r in rows], ['claude', 'claude'])
            self.assertEqual(watermark, c['id'])
            self.assertFalse(db.in_transaction)
        finally:
            db.close()

    def test_thread_history_and_follow(self):
        a = chat.post(self.db, 'codex', 'claude', '', 'one')
        b = chat.post(self.db, 'claude', None, '', 'two', a['id'])
        chat.post(self.db, 'claude', 'codex', '', 'different thread')
        db = chat.connect_feed(self.path)
        try:
            rows, after = chat.feed_history(db, 50, a['id'])
            self.assertEqual([r['id'] for r in rows], [a['id'], b['id']])
            c = chat.post(self.db, 'codex', None, '', 'followed', b['id'])
            chat.post(self.db, 'claude', 'codex', '', 'not followed')
            self.assertEqual([r['id'] for r in chat.feed_new(db, after, a['id'])], [c['id']])
        finally:
            db.close()

    def test_history_follow_boundary_has_no_gap(self):
        a = chat.post(self.db, 'codex', 'claude', '', 'old')
        db = chat.connect_feed(self.path)
        try:
            rows, after = chat.feed_history(db, 0)
            self.assertEqual(rows, [])
            self.assertEqual(after, a['id'])
            b = chat.post(self.db, 'claude', 'codex', '', 'arrived after snapshot')
            self.assertEqual([r['id'] for r in chat.feed_new(db, after)], [b['id']])
        finally:
            db.close()

    def test_connection_cannot_write_and_state_stays_unchanged(self):
        a = chat.post(self.db, 'codex', 'claude', '', 'incoming')
        chat.post(self.db, 'claude', 'codex', '', 'other inbox')
        before = list(self.db.execute('SELECT * FROM receipts'))
        counts = [chat.unread_count(self.db, x) for x in ('codex', 'claude')]
        db = chat.connect_feed(self.path)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM messages')
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('INSERT INTO receipts VALUES (?,?,?)', ('claude', a['id'], chat.now()))
            with contextlib.redirect_stdout(io.StringIO()):
                chat.feed(db, follow=False)
            self.assertEqual(db.total_changes, 0)
        finally:
            db.close()
        self.assertEqual(list(self.db.execute('SELECT * FROM receipts')), before)
        self.assertEqual([chat.unread_count(self.db, x) for x in ('codex', 'claude')], counts)

    def test_multiline_markdown_and_metadata_no_agent_required(self):
        body = '# Details\n\nC:\\Example Data\\page.img\n`abc1234` — exact\n' + 'x' * 5000
        a = chat.post(self.db, 'codex', 'claude', 'Example', body)
        p = subprocess.run([sys.executable, str(Path(chat.__file__)), '--db', str(self.path),
                            'feed', '--history', '50', '--no-follow'],
                           capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        for text in (body, 'codex -> claude', a['created_at'], f"thread {a['id']}", 'Example'):
            self.assertIn(text, p.stdout)

    def test_missing_database_not_created(self):
        path = Path(self.tmp.name) / 'absent.sqlite3'
        with self.assertRaises(sqlite3.OperationalError):
            chat.connect_feed(path)
        self.assertFalse(path.exists())

    def test_ctrl_c_clean_exit_and_sleep_between_queries(self):
        out = io.StringIO()
        with patch.object(chat.threading, 'Event') as event, patch.object(chat, 'feed_new', wraps=chat.feed_new) as query:
            event.return_value.wait.side_effect = [None, KeyboardInterrupt()]
            with contextlib.redirect_stdout(out):
                code = chat.main(['--db', str(self.path), 'feed', '--history', '0'])
            self.assertEqual(query.call_count, 2)
            self.assertEqual(event.return_value.wait.call_count, 2)
        self.assertEqual(code, 0)
        self.assertIn('Feed stopped.', out.getvalue())

    def test_invalid_history(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = chat.main(['--db', str(self.path), 'feed', '--history', '-1'])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out.getvalue())['ok'])

    def test_real_subprocess_follow_receives_cli_sends(self):
        script = str(Path(chat.__file__))
        proc = subprocess.Popen([sys.executable, script, '--db', str(self.path),
                                 'feed', '--history', '0', '--interval', '.1'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8')
        lines = queue.Queue()
        def pump():
            for line in proc.stdout:
                lines.put(line)
        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        try:
            while 'Following new messages.' not in lines.get(timeout=10):
                pass
            for sender, recipient, body in (('codex','claude','automatic-one'), ('claude','codex','automatic-two')):
                posted = subprocess.run([sys.executable, script, '--db', str(self.path), '--agent', sender,
                                         'send', '--to', recipient, '--body', body],
                                        capture_output=True, text=True, encoding='utf-8', timeout=10)
                self.assertEqual(posted.returncode, 0, posted.stderr)
                while body not in lines.get(timeout=10):
                    pass
            self.assertEqual([chat.unread_count(self.db, a) for a in ('codex','claude')], [1,1])
            self.assertEqual(self.db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0], 0)
        finally:
            proc.terminate()
            proc.wait(timeout=10)
            reader.join(timeout=5)
            proc.stdout.close()
            proc.stderr.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
