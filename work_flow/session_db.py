import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '../sessions/session.db')

class SessionDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 检查是否已存在 tool_call_id 字段
        c.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in c.fetchall()]
        if 'tool_call_id' not in columns:
            try:
                c.execute('ALTER TABLE messages ADD COLUMN tool_call_id TEXT')
            except Exception:
                pass
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp INTEGER,
            tool_call_id TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS session_meta (
            session_id TEXT PRIMARY KEY,
            user_info TEXT,
            assigned_agent TEXT,
            tool_calls TEXT,
            sessions_finished INTEGER,
            called_tools TEXT,
            tool_call_count TEXT,
            conversation_finished INTEGER
        )''')
        conn.commit()
        conn.close()

    def save_message(self, session_id: str, role: str, content: str, timestamp: int, tool_call_id: str = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO messages (session_id, role, content, timestamp, tool_call_id) VALUES (?, ?, ?, ?, ?)',
                  (session_id, role, content, timestamp, tool_call_id))
        conn.commit()
        conn.close()

    def get_messages(self, session_id: str, max_length: int = 10) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT role, content, timestamp, tool_call_id FROM messages WHERE session_id=? ORDER BY timestamp DESC LIMIT ?',
                  (session_id, max_length))
        rows = c.fetchall()
        conn.close()
        return [{'role': r[0], 'content': r[1], 'timestamp': r[2], 'tool_call_id': r[3]} for r in rows]

    def save_meta(self, session_id: str, meta: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('REPLACE INTO session_meta (session_id, user_info, assigned_agent, tool_calls, sessions_finished, called_tools, tool_call_count, conversation_finished) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (session_id, meta.get('user_info', ''), meta.get('assigned_agent', ''),
                   str(meta.get('tool_calls', '')), int(meta.get('sessions_finished', False)),
                   str(meta.get('called_tools', '')), str(meta.get('tool_call_count', '')), int(meta.get('conversation_finished', False))))
        conn.commit()
        conn.close()

    def get_meta(self, session_id: str) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT user_info, assigned_agent, tool_calls, sessions_finished, called_tools, tool_call_count, conversation_finished FROM session_meta WHERE session_id=?', (session_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {}
        return {
            'user_info': row[0],
            'assigned_agent': row[1],
            'tool_calls': row[2],
            'sessions_finished': bool(row[3]),
            'called_tools': row[4],
            'tool_call_count': row[5],
            'conversation_finished': bool(row[6])
        }
