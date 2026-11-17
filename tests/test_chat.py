import concurrent.futures
import contextlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path
from agent_chat import cli as chat


SCRIPT = Path(chat.__file__)


class MessagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='agent-chat-test-')
        self.path = Path(self.tmp.name) / 'test.sqlite3'
        self.db = chat.connect(self.path)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_unicode_markdown_and_persistence(self):
        body = '# Example\n\n`C:\\Example Data\\tile.img` â€” abc1234\n\n* measured â†’ exact *\n'
        m = chat.post(self.db, 'codex', 'claude', 'Example', body)
        other = chat.connect(self.path)
        try:
            rows = chat.receive(other, 'claude', mark=False)
            self.assertEqual(rows[0]['body'], body)
            self.assertEqual(m['thread_id'], m['id'])
            self.assertIn('+00:00', m['created_at'])
        finally:
            other.close()

    def test_unread_per_agent_and_limited_read(self):
        a = chat.post(self.db, 'codex', 'claude', '', 'one')
        b = chat.post(self.db, 'codex', 'claude', '', 'two')
        chat.receive(self.db, 'claude', unread=True, mark=False)
        self.assertEqual(chat.unread_count(self.db, 'claude'), 2)
        rows = chat.receive(self.db, 'claude', unread=True, limit=1)
        self.assertEqual([x['id'] for x in rows], [a['id']])
        self.assertEqual(chat.unread_count(self.db, 'claude'), 1)
        self.assertEqual(chat.unread_count(self.db, 'codex'), 0)
        self.assertEqual(chat.receive(self.db, 'claude', unread=True)[0]['id'], b['id'])
        self.assertEqual(chat.unread_count(self.db, 'claude'), 0)

    def test_receipts_do_not_consume_other_agent_inbox(self):
        chat.post(self.db, 'codex', 'claude', '', 'to Claude')
        chat.post(self.db, 'claude', 'codex', '', 'to Codex')
        chat.receive(self.db, 'claude')
        self.assertEqual(chat.unread_count(self.db, 'claude'), 0)
        self.assertEqual(chat.unread_count(self.db, 'codex'), 1)

    def test_watch_poll_count_is_bounded(self):
        with patch.object(chat, 'receive', wraps=chat.receive) as receive:
            self.assertEqual(chat.watch(self.db, 'claude', .22, .1), [])
            self.assertLessEqual(receive.call_count, 4)

    def test_watch_early_wakes_do_not_trigger_extra_queries(self):
        clock = [0.0]
        polls = []
        def empty(*args, **kwargs):
            polls.append(clock[0])
            return []
        def early_wait(delay):
            self.assertFalse(self.db.in_transaction)
            self.assertGreaterEqual(delay, .001)
            clock[0] += delay - .0005  # model an early OS timed-wait return
        with patch.object(chat.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(chat, 'receive', side_effect=empty), \
             patch.object(chat.threading, 'Event') as event:
            event.return_value.wait.side_effect = early_wait
            self.assertEqual(chat.watch(self.db, 'claude', .22, .1), [])
        self.assertEqual(len(polls), 3)
        self.assertTrue(all(b-a >= .1-1e-12 for a,b in zip(polls,polls[1:])))
        self.assertTrue(all(at < .22 for at in polls))
        self.assertGreaterEqual(clock[0], .22)
        self.assertLess(clock[0], .222)

    def test_watch_oversleep_does_not_query_after_deadline(self):
        clock = [0.0]
        with patch.object(chat.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(chat, 'receive', return_value=[]) as receive, \
             patch.object(chat.threading, 'Event') as event:
            event.return_value.wait.side_effect = lambda delay: clock.__setitem__(0, 1.0)
            self.assertEqual(chat.watch(self.db, 'claude', .22, .1), [])
            self.assertEqual(receive.call_count, 1)

    def test_watch_zero_timeout_still_checks_inbox_once(self):
        with patch.object(chat, 'receive', return_value=[]) as receive, \
             patch.object(chat.threading, 'Event') as event:
            self.assertEqual(chat.watch(self.db, 'claude', 0, .1), [])
            self.assertEqual(receive.call_count, 1)
            event.return_value.wait.assert_not_called()

    def test_reply_thread_and_participants(self):
        a = chat.post(self.db, 'codex', 'claude', 'question', 'question')
        b = chat.post(self.db, 'claude', None, '', 'answer', a['id'])
        c = chat.post(self.db, 'codex', None, '', 'follow-up', b['id'])
        self.assertEqual((b['recipient'], c['recipient']), ('codex', 'claude'))
        self.assertEqual(c['thread_id'], a['id'])
        self.assertEqual(c['reply_to'], b['id'])
        with self.assertRaises(chat.ChatError):
            chat.post(self.db, 'stranger', None, '', 'wrong', a['id'])
        with self.assertRaises(chat.ChatError):
            chat.post(self.db, 'codex', None, '', 'missing', 999)
        self.assertEqual(len(chat.receive(self.db, 'claude', thread=a['id'])), 3)
        self.assertEqual(chat.receive(self.db, 'stranger', thread=a['id']), [])

    def test_invalid_send_rolls_back(self):
        with self.assertRaises(chat.ChatError):
            chat.post(self.db, 'codex', 'codex', '', 'self')
        with self.assertRaises(chat.ChatError):
            chat.post(self.db, 'codex', 'claude', '', '  ')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM messages').fetchone()[0], 0)

    def cli(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), '--db', str(self.path), *args],
                                capture_output=True, text=True, encoding='utf-8', timeout=45)
        return result.returncode, json.loads(result.stdout)

    def test_errors_are_json(self):
        code, result = self.cli('--agent', 'codex', 'reply', '999', '--body', 'test')
        self.assertEqual(code, 2)
        self.assertFalse(result['ok'])
        code, result = self.cli('--agent', 'codex', 'send')
        self.assertEqual(code, 2)
        self.assertIn('required', result['message'])

    def test_file_body_and_peek(self):
        body = '# Exact\n\nC:\\example\\measured page\nabc1234\n'
        p = Path(self.tmp.name) / 'message.md'
        p.write_text(body, encoding='utf-8')
        code, result = self.cli('--agent', 'codex', 'send', '--to', 'claude', '--file', str(p))
        self.assertEqual(code, 0)
        self.assertEqual(result['message']['body'], body)
        code, result = self.cli('--agent', 'claude', 'unread')
        self.assertEqual(result['unread_count'], 1)
        code, result = self.cli('--agent', 'claude', 'read')
        self.assertEqual(result['unread_count'], 0)

    def test_concurrent_subprocess_writes(self):
        def write(i):
            code, response = self.cli('--agent', 'codex', 'send', '--to', 'claude', '--body', f'parallel {i}')
            self.assertEqual(code, 0)
            return response['message']
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            messages = list(pool.map(write, range(32)))
        self.assertEqual(len({m['id'] for m in messages}), 32)
        self.assertEqual(chat.unread_count(self.db, 'claude'), 32)
        self.assertEqual(self.db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_watch_timeout_and_delayed_arrival(self):
        start = time.monotonic()
        self.assertEqual(chat.watch(self.db, 'claude', .22, .1), [])
        self.assertGreaterEqual(time.monotonic() - start, .20)
        def delayed():
            time.sleep(.15)
            db = chat.connect(self.path)
            try:
                chat.post(db, 'codex', 'claude', '', 'arrived')
            finally:
                db.close()
        thread = threading.Thread(target=delayed)
        thread.start()
        try:
            rows = chat.watch(self.db, 'claude', 2, .1)
            self.assertEqual(rows[0]['body'], 'arrived')
            self.assertEqual(chat.unread_count(self.db, 'claude'), 0)
        finally:
            thread.join()

    def test_concurrent_reply_and_reader(self):
        parent = chat.post(self.db, 'codex', 'claude', '', 'root')
        def reply(i):
            return self.cli('--agent', 'claude', 'reply', str(parent['id']), '--body', f'reply {i}')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(reply, i) for i in range(12)]
            seen = chat.receive(self.db, 'codex', unread=True)
            for future in futures:
                self.assertEqual(future.result()[0], 0)
        seen += chat.receive(self.db, 'codex', unread=True)
        self.assertEqual(len({m['id'] for m in seen}), 12)
        self.assertTrue(all(m['thread_id'] == parent['id'] for m in seen))


if __name__ == '__main__':
    unittest.main(verbosity=2)
