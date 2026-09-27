import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Store:
    """Atomic snapshots with optimistic concurrency; no DB lock held during API calls."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS sessions "
                "(id TEXT PRIMARY KEY, revision INTEGER NOT NULL, data TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints "
                "(lesson_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
            )

            db.execute(
                "CREATE TABLE IF NOT EXISTS tutor_messages "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)"
            )

    def tutor_messages(self):
        with self.connect() as db:
            return [
                json.loads(row[0])
                for row in db.execute("SELECT data FROM tutor_messages ORDER BY id DESC LIMIT 100")
            ][::-1]

    def save_tutor_message(self, message):
        with self.connect() as db:
            db.execute("INSERT INTO tutor_messages(data) VALUES (?)", (json.dumps(message),))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, state):
        with self.connect() as db:
            db.execute("INSERT INTO sessions VALUES (?, 0, ?)", (state["id"], json.dumps(state)))

    def load(self, session_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT data, revision FROM sessions WHERE id=?", (session_id,)
            ).fetchone()
        if row is None:
            raise ValueError("Session not found. Use 'grey sessions' to list IDs.")
        return json.loads(row[0]), row[1]

    def save(self, state, revision):
        with self.connect() as db:
            result = db.execute(
                "UPDATE sessions SET data=?, revision=revision+1 WHERE id=? AND revision=?",
                (json.dumps(state), state["id"], revision),
            )
            if result.rowcount != 1:
                raise ValueError("Session changed in another process. Reload before retrying.")
        return revision + 1

    def all(self):
        with self.connect() as db:
            return [
                json.loads(row[0]) for row in db.execute("SELECT data FROM sessions ORDER BY rowid")
            ]

    def save_checkpoint(self, result):
        with self.connect() as db:
            db.execute(
                "INSERT INTO checkpoints VALUES (?, ?) "
                "ON CONFLICT(lesson_id) DO UPDATE SET data=excluded.data",
                (result["lesson_id"], json.dumps(result)),
            )

    def checkpoints(self):
        with self.connect() as db:
            return {row[0]: json.loads(row[1]) for row in db.execute("SELECT * FROM checkpoints")}
