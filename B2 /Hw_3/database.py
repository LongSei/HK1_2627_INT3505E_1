import sqlite3
import os

class SqliteDatabaseManager:
    """Manages database initialization and lifecycle connections."""

    # Bổ sung thêm tham số schema_path để trỏ tới file SQL
    def __init__(self, db_path: str = "app.db", schema_path: str = "schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Tạo và trả về một connection mới."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  
        return conn

    def _init_db(self):
        """Đọc file schema.sql và khởi tạo database nếu chưa có."""
        # Kiểm tra xem file schema.sql có tồn tại không
        if os.path.exists(self.schema_path):
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
            
            # Thực thi toàn bộ script trong file
            with self.get_connection() as conn:
                conn.executescript(schema_script)
        else:
            print(f"Cảnh báo: Không tìm thấy file {self.schema_path}!")