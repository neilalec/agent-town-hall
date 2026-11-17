#!/usr/bin/env python3
"""Local, durable CLI inboxes. No model API, network service or server."""
import argparse
import json
import os
import re
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = '0.1.0'


def default_db_path(platform=None, env=None, home=None):
    """CLI --db overrides AGENT_CHAT_DB, then platform-specific user data."""
    platform = sys.platform if platform is None else platform
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    if env.get('AGENT_CHAT_DB'):
        return Path(env['AGENT_CHAT_DB']).expanduser()
    if platform == 'win32':
        root = Path(env['LOCALAPPDATA']) if env.get('LOCALAPPDATA') else home / 'AppData' / 'Local'
    elif platform == 'darwin':
        root = home / 'Library' / 'Application Support'
    else:
        xdg = Path(env.get('XDG_DATA_HOME', ''))
        root = xdg if xdg.is_absolute() else home / '.local' / 'share'
    return root / 'agent-chat' / 'chat.sqlite3'



class ChatError(Exception):
    pass


def agent_name(value):
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', value):
        raise argparse.ArgumentTypeError('agent must be a lowercase identifier (1-64 characters)')
    return value


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ChatError(message)


def _connect_once(path, timeout):
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(str(path), timeout=timeout, isolation_level=None)
    try:
        db.row_factory = sqlite3.Row
        db.execute(f'PRAGMA busy_timeout={max(1, int(timeout * 1000))}')
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          thread_id INTEGER REFERENCES messages(id),
          reply_to INTEGER REFERENCES messages(id),
          sender TEXT NOT NULL, recipient TEXT NOT NULL,
          subject TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL,
          CHECK(sender != recipient)
        );
        CREATE INDEX IF NOT EXISTS inbox ON messages(recipient,id);
        CREATE INDEX IF NOT EXISTS threads ON messages(thread_id,id);
        CREATE TABLE IF NOT EXISTS receipts (
          agent TEXT NOT NULL, message_id INTEGER NOT NULL REFERENCES messages(id),
          read_at TEXT NOT NULL, PRIMARY KEY(agent,message_id)
        );
        ''')
        return db
    except BaseException:
        db.close()
        raise


def connect(path):
    # journal_mode=WAL can report BUSY immediately on simultaneous first use.
    # Retry only initialization locks; never replay message transactions.
    deadline = time.monotonic() + 30
    while True:
        try:
            return _connect_once(path, max(.001, deadline - time.monotonic()))
        except sqlite3.OperationalError as exc:
            code = getattr(exc, "sqlite_errorcode", 0) & 255
            busy = code in (5, 6) or str(exc) in ("database is locked", "database table is locked")
            remaining = deadline - time.monotonic()
            if not busy or remaining <= 0:
                raise
            time.sleep(min(.05, remaining))


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def post(db, sender, recipient, subject, body, parent=None):
    if not body.strip():
        raise ChatError('message body must not be empty')
    db.execute('BEGIN IMMEDIATE')
    try:
        thread = None
        if parent is not None:
            row = db.execute('SELECT * FROM messages WHERE id=?', (parent,)).fetchone()
            if row is None:
                raise ChatError(f'message {parent} does not exist')
            if sender not in (row['sender'], row['recipient']):
                raise ChatError('agent is not a participant in the parent message')
            recipient = row['sender'] if sender == row['recipient'] else row['recipient']
            thread, subject = row['thread_id'], row['subject']
        if recipient == sender:
            raise ChatError('sender and recipient must differ')
        cursor = db.execute('''INSERT INTO messages
          (thread_id,reply_to,sender,recipient,subject,body,created_at)
          VALUES (?,?,?,?,?,?,?)''', (thread, parent, sender, recipient, subject, body, now()))
        message_id = cursor.lastrowid
        if thread is None:
            db.execute('UPDATE messages SET thread_id=? WHERE id=?', (message_id, message_id))
        result = dict(db.execute('SELECT * FROM messages WHERE id=?', (message_id,)).fetchone())
        db.execute('COMMIT')
        return result
    except BaseException:
        db.execute('ROLLBACK')
        raise


def receive(db, agent, unread=False, thread=None, limit=200, mark=True):
    # Selection and receipt creation are atomic: concurrent arrivals cannot be
    # marked read without actually being returned to this reader.
    db.execute('BEGIN IMMEDIATE' if mark else 'BEGIN')
    try:
        where = ['(m.sender=? OR m.recipient=?)']
        params = [agent, agent]
        if unread:
            where += ['m.recipient=?', 'r.message_id IS NULL']
            params.append(agent)
        if thread is not None:
            where.append('m.thread_id=?')
            params.append(thread)
        sql = '''SELECT m.*,r.read_at FROM messages m LEFT JOIN receipts r
          ON r.message_id=m.id AND r.agent=? WHERE ''' + ' AND '.join(where) + ' ORDER BY m.id LIMIT ?'
        rows = [dict(r) for r in db.execute(sql, [agent] + params + [limit])]
        if mark:
            stamp = now()
            db.executemany('INSERT OR IGNORE INTO receipts VALUES (?,?,?)',
                           [(agent, r['id'], stamp) for r in rows if r['recipient'] == agent])
            for row in rows:
                if row['recipient'] == agent and row['read_at'] is None:
                    row['read_at'] = stamp
        db.execute('COMMIT')
        return rows
    except BaseException:
        db.execute('ROLLBACK')
        raise


def unread_count(db, agent):
    return db.execute('''SELECT COUNT(*) FROM messages m WHERE recipient=? AND NOT EXISTS
      (SELECT 1 FROM receipts r WHERE r.agent=? AND r.message_id=m.id)''', (agent, agent)).fetchone()[0]


def connect_feed(path):
    # Never initialize a schema, select WAL mode, or open a writable database.
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True,
                         timeout=5, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def feed_history(db, history, thread=None):
    # One short snapshot prevents arrivals between history and follow from
    # being missed, including with --history 0 or a filtered thread.
    db.execute('BEGIN')
    try:
        watermark = db.execute('SELECT COALESCE(MAX(id),0) FROM messages').fetchone()[0]
        where = 'id<=?' + (' AND thread_id=?' if thread is not None else '')
        params = [watermark] + ([thread] if thread is not None else []) + [history]
        rows = [dict(r) for r in db.execute(
            'SELECT * FROM messages WHERE ' + where + ' ORDER BY id DESC LIMIT ?', params)]
        db.execute('COMMIT')
        return list(reversed(rows)), watermark
    except BaseException:
        db.execute('ROLLBACK')
        raise


def feed_new(db, after, thread=None):
    where = 'id>?' + (' AND thread_id=?' if thread is not None else '')
    params = [after] + ([thread] if thread is not None else [])
    return [dict(r) for r in db.execute(
        'SELECT * FROM messages WHERE ' + where + ' ORDER BY id LIMIT 500', params)]


def terminal_text(value):
    # Keep multiline Markdown readable without allowing terminal escape/control injection.
    return ''.join(c if c in '\n\t' or (ord(c) >= 32 and not 127 <= ord(c) <= 159)
                   else f'\\x{ord(c):02x}' for c in value)


def print_feed_message(message):
    print('-' * 72)
    print(f"[{message['created_at']}] #{message['id']} | "
          f"{message['sender']} -> {message['recipient']} | thread {message['thread_id']}"
          + (f" | reply to {message['reply_to']}" if message['reply_to'] is not None else ''))
    if message['subject']:
        print(f"Subject: {terminal_text(message['subject'])}")
    print()
    print(terminal_text(message['body']))
    print(flush=True)


def feed(db, history=50, thread=None, follow=True, interval=1):
    if not 0 <= history <= 10000 or not .1 <= interval <= 30:
        raise ChatError('history must be 0..10000; interval must be 0.1..30 seconds')
    try:
        rows, after = feed_history(db, history, thread)
        print('Agent Chat conversation feed (read-only)' +
              (f' | thread {thread}' if thread is not None else ' | all threads'), flush=True)
        for row in rows:
            print_feed_message(row)
        if not rows:
            print('(No recent messages.)', flush=True)
        if not follow:
            return
        print('Following new messages. Press Ctrl+C to stop.', flush=True)
        sleeper = threading.Event()
        while True:
            rows = feed_new(db, after, thread)
            for row in rows:
                print_feed_message(row)
                after = row['id']
            if len(rows) < 500:
                # Each SELECT has finished; no snapshot or lock spans this wait.
                sleeper.wait(interval)
    except KeyboardInterrupt:
        print('\nFeed stopped.', flush=True)


def watch(db, agent, timeout, interval, thread=None, limit=200, mark=True):
    if not 0 <= timeout <= 86400 or not .1 <= interval <= 30:
        raise ChatError('timeout must be 0..86400 seconds; interval must be 0.1..30 seconds')
    deadline = time.monotonic() + timeout
    sleeper = threading.Event()
    while True:
        rows = receive(db, agent, unread=True, thread=thread, limit=limit, mark=mark)
        if rows:
            return rows
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return []
        # No transaction/SQLite lock is held during the bounded wait.
        sleeper.wait(min(interval, remaining))


def parser():
    p = Parser(prog='agent-chat', description=__doc__)
    p.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    p.add_argument('--db', type=Path, default=default_db_path())
    p.add_argument('--agent', type=agent_name)
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('init', help='Initialize a local database without an agent identity')
    f = commands.add_parser('feed', help='Read-only history and live conversation feed; no agent identity needed')
    f.add_argument('--history', type=int, default=50)
    f.add_argument('--thread', type=int)
    f.add_argument('--no-follow', action='store_true')
    f.add_argument('--interval', type=float, default=1)
    for name in ('send', 'reply'):
        s = commands.add_parser(name)
        if name == 'send':
            s.add_argument('--to', required=True, type=agent_name)
            s.add_argument('--subject', default='')
        else:
            s.add_argument('message_id', type=int)
        body = s.add_mutually_exclusive_group(required=True)
        body.add_argument('--body')
        body.add_argument('--file', type=Path)
        body.add_argument('--stdin', action='store_true')
    for name in ('read', 'unread', 'watch'):
        s = commands.add_parser(name)
        s.add_argument('--thread', type=int)
        s.add_argument('--limit', type=int, default=200)
        if name != 'unread':
            s.add_argument('--no-mark', action='store_true')
        if name == 'watch':
            s.add_argument('--timeout', type=float, default=60)
            s.add_argument('--interval', type=float, default=1)
    return p


def main(argv=None):
    db = None
    for stream in (sys.stdout, sys.stdin):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    try:
        args = parser().parse_args(argv)
        args.db = args.db.expanduser()
        if args.command == 'feed':
            db = connect_feed(args.db)
            feed(db, args.history, args.thread, not args.no_follow, args.interval)
            return 0
        if args.command == 'init':
            db = connect(args.db)
            print(json.dumps({'ok': True, 'database': str(args.db.resolve())}))
            return 0
        if args.agent is None:
            raise ChatError('--agent is required for send, reply, read, unread and watch')
        if hasattr(args, 'limit') and not 1 <= args.limit <= 10000:
            raise ChatError('limit must be 1..10000')
        body = None
        if args.command in ('send', 'reply'):
            body = args.body if args.body is not None else (
                args.file.read_text(encoding='utf-8-sig') if args.file else sys.stdin.read())
        db = connect(args.db)
        result = {'ok': True, 'agent': args.agent, 'database': str(args.db.resolve())}
        if args.command in ('send', 'reply'):
            result['message'] = post(db, args.agent, getattr(args, 'to', None),
                                     getattr(args, 'subject', ''), body, getattr(args, 'message_id', None))
        elif args.command == 'watch':
            result['messages'] = watch(db, args.agent, args.timeout, args.interval,
                                       args.thread, args.limit, not args.no_mark)
            result['timed_out'] = not bool(result['messages'])
        else:
            result['messages'] = receive(db, args.agent, args.command == 'unread', args.thread,
                                         args.limit, args.command == 'read' and not args.no_mark)
        result['unread_count'] = unread_count(db, args.agent)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except BrokenPipeError:
        return 0
    except (ChatError, OSError, sqlite3.Error) as exc:
        print(json.dumps({'ok': False, 'error': type(exc).__name__, 'message': str(exc)}, ensure_ascii=False))
        return 3 if isinstance(exc, sqlite3.OperationalError) else 2
    except KeyboardInterrupt:
        print(json.dumps({'ok': False, 'error': 'interrupted', 'message': 'operation interrupted'}))
        return 130
    finally:
        if db is not None:
            db.close()


if __name__ == '__main__':
    sys.exit(main())
