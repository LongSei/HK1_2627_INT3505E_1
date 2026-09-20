from abc import ABC, abstractmethod
from database import SqliteDatabaseManager

class IOrderRepository(ABC):
    """Giao diện trừu tượng định nghĩa các hành vi quản lý đơn hàng."""

    @abstractmethod
    def get_order_by_id(self, order_id: int) -> dict | None:
        """Lấy thông tin chi tiết của một đơn đặt hàng theo ID.

        Args:
            order_id (int): ID của đơn hàng cần tìm kiếm.

        Returns:
            dict | None: Thông tin đơn hàng dạng từ điển nếu thấy, ngược lại là None.
        """
        pass


class SQLiteOrderRepository(IOrderRepository):
    """Triển khai quản lý đơn hàng chi tiết bằng hệ quản trị cơ sở dữ liệu SQLite."""

    def __init__(self, db: SqliteDatabaseManager):
        self.db = db

    def get_order_by_id(self, order_id: int) -> dict | None:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return dict(row) if row else None
