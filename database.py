"""SQLite persistence for calculation history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class HistoryRepository:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS calculation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,
                    result REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _record(row: sqlite3.Row) -> dict:
        result = row["result"]
        if float(result).is_integer():
            result = int(result)
        return {"id": row["id"], "expression": row["expression"], "result": result, "createdAt": row["created_at"]}

    def add(self, expression: str, result: int | float) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO calculation_history(expression, result, created_at) VALUES (?, ?, ?)",
                (expression, result, timestamp),
            )
            row = connection.execute("SELECT * FROM calculation_history WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._record(row)

    def list(self, limit: int = 100) -> list[dict]:
        limit = max(1, min(int(limit), 500))
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM calculation_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._record(row) for row in rows]

    def delete(self, record_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM calculation_history WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def clear(self) -> int:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM calculation_history")
            return cursor.rowcount
