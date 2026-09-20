from abc import ABC, abstractmethod
from database import SqliteDatabaseManager

class IBookRepository(ABC):
    """Giao diện trừu tượng định nghĩa các hành vi quản lý sách.
    
    Tầng chứa toàn bộ tài liệu (Docstring) mô tả nghiệp vụ của hệ thống Sách.
    """

    @abstractmethod
    def get_books(self) -> list[dict]:
        """Lấy toàn bộ danh sách các cuốn sách từ kho lưu trữ.
        
        Lưu ý: Phương thức này kéo toàn bộ dữ liệu không qua bộ lọc hay phân trang.
        Việc tính toán, phân trang và tìm kiếm sẽ được xử lý trên RAM ở tầng ứng dụng.

        Returns:
            list[dict]: Danh sách chứa tất cả các sách dưới dạng từ điển.
        """
        pass
    
    @abstractmethod
    def get_amount_of_books(self) -> int:
        """Lấy tổng số lượng sách hiện có trong kho lưu trữ.

        Returns:
            int: Tổng số sách.
        """
        pass

    @abstractmethod
    def create_book(self, title: str, author: str, isbn: str = "", price: float = 0.0) -> int:
        """Thêm mới một cuốn sách vào trong kho lưu trữ.

        Args:
            title (str): Tiêu đề của cuốn sách.
            author (str): Tên tác giả của cuốn sách.
            isbn (str, optional): Mã định danh quốc tế ISBN. Mặc định là chuỗi rỗng.
            price (float, optional): Giá bán của cuốn sách. Mặc định là 0.0.

        Returns:
            int: ID của bản ghi sách vừa được tạo thành công.
        """
        pass

    @abstractmethod
    def update_book(self, book_id: int, title: str, author: str, isbn: str, price: float) -> bool:
        """Cập nhật toàn bộ thông tin của một cuốn sách (Ghi đè bản ghi).

        Args:
            book_id (int): ID của cuốn sách cần cập nhật.
            title (str): Tiêu đề mới.
            author (str): Tên tác giả mới.
            isbn (str): Mã ISBN mới.
            price (float): Giá bán mới.

        Returns:
            bool: True nếu cập nhật thành công, False nếu không tìm thấy bản ghi.
        """
        pass

    @abstractmethod
    def patch_book(self, book_id: int, update_fields: dict) -> bool:
        """Cập nhật một phần thông tin của một cuốn sách dựa trên các trường truyền vào.

        Args:
            book_id (int): ID của cuốn sách cần cập nhật.
            update_fields (dict): Cấu trúc dạng dict chứa các cặp {tên_cột: giá_trị_mới}.

        Returns:
            bool: True nếu cập nhật thành công ít nhất một trường, ngược lại là False.
        """
        pass

    @abstractmethod
    def delete_book(self, book_id: int) -> bool:
        """Xóa vĩnh viễn một cuốn sách ra khỏi hệ thống lưu trữ.

        Args:
            book_id (int): ID của cuốn sách cần xóa.

        Returns:
            bool: True nếu xóa thành công, False nếu ID không tồn tại.
        """
        pass


class SQLiteBookRepository(IBookRepository):
    """Triển khai quản lý sách chi tiết bằng hệ quản trị cơ sở dữ liệu SQLite."""

    def __init__(self, db: SqliteDatabaseManager):
        self.db = db

    def get_books(self) -> list[dict]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM books").fetchall()
            return [dict(row) for row in rows]

    def get_amount_of_books(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM books").fetchone()
            return row["count"] if row else 0

    def create_book(self, title: str, author: str, isbn: str = "", price: float = 0.0) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO books (title, author, isbn, price) VALUES (?, ?, ?, ?)",
                (title, author, isbn, price)
            )
            return cursor.lastrowid

    def update_book(self, book_id: int, title: str, author: str, isbn: str, price: float) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE books SET title = ?, author = ?, isbn = ?, price = ? WHERE id = ?",
                (title, author, isbn, price, book_id)
            )
            return cursor.rowcount > 0

    def patch_book(self, book_id: int, update_fields: dict) -> bool:
        if not update_fields:
            return False
            
        set_clause = ", ".join([f"{key} = ?" for key in update_fields.keys()])
        values = list(update_fields.values())
        values.append(book_id)

        query = f"UPDATE books SET {set_clause} WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount > 0

    def delete_book(self, book_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            return cursor.rowcount > 0