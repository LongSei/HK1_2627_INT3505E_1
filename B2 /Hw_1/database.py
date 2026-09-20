import sqlite3

class SqliteDatabaseManager:
    """Manages database initialization and lifecycle connections."""

    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Tạo và trả về một connection mới (dùng cho mỗi request).

        Returns:
            sqlite3.Connection: Đối tượng kết nối SQLite đã được cấu hình Row factory.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Trả về dữ liệu dạng dict-like
        return conn

    def _init_db(self):
        """Khởi tạo schema database nếu chưa có."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    isbn TEXT,
                    price REAL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    status TEXT,
                    total REAL
                );
            """)
