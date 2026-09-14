# RedNote Bulk Video Downloader

MVP web app: nhập URL profile RedNote/Xiaohongshu → quét bài đăng công khai → phát hiện video → tải video được chọn → đóng gói ZIP.

## Chạy trên Windows/macOS/Linux

1. Cài Python 3.11+.
2. Mở Terminal trong thư mục dự án.
3. `python -m venv .venv`
4. Windows: `.venv\\Scripts\\activate` — macOS/Linux: `source .venv/bin/activate`
5. `pip install -r requirements.txt`
6. `playwright install chromium`
7. `uvicorn app:app --host 0.0.0.0 --port 8000`
8. Mở `http://127.0.0.1:8000`

## Lưu ý
- Chỉ xử lý URL/nội dung mà người dùng có quyền truy cập và tải xuống.
- Không tự động vượt CAPTCHA hoặc cơ chế bảo vệ của RedNote.
- Cookie là tùy chọn và chỉ tồn tại trong bộ nhớ của tiến trình; không ghi vào database.
- RedNote có thể thay đổi API/web structure. Khi đó cần cập nhật parser.
- Bản MVP tải tuần tự để giảm tải; có thể nâng cấp queue/concurrency, lịch sử và retry.
