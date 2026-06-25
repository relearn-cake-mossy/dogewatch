# YTView — Xem YouTube

Web app xem YouTube dùng Flask + yt-dlp, deploy lên Render.com.

## Cấu trúc

```
youtube-viewer/
├── app.py          ← Giao diện web (Flask)
├── proxy.py        ← Proxy server yt-dlp (chạy tại botdic.nethr.nl:10416)
├── requirements.txt
├── render.yaml     ← Cấu hình deploy Render.com
└── templates/
    └── index.html  ← UI tìm kiếm & xem video
```

## Cách hoạt động

```
Trình duyệt  ──→  app.py (giao diện)  ──→  proxy.py (yt-dlp)  ──→  YouTube
              ←─────────────────────── stream URL ────────────────────────────
```

- `app.py` chạy giao diện, nhận request từ user, gọi proxy
- `proxy.py` dùng `yt-dlp` để tìm kiếm và lấy stream URL từ YouTube
- Video phát trực tiếp qua thẻ `<video>` HTML5

## API của proxy.py

| Endpoint         | Params              | Mô tả                            |
|------------------|---------------------|-----------------------------------|
| `/health`        | —                   | Kiểm tra trạng thái               |
| `/search`        | `q`, `limit`        | Tìm kiếm video                    |
| `/video`         | `id`                | Thông tin video                   |
| `/stream`        | `id`, `quality`     | Lấy URL stream                    |
| `/proxy/status`  | —                   | Xem trạng thái proxy pool         |
| `/proxy/refresh` | —                   | Bắt buộc tải lại list proxy ngay  |

**Quality options:** `best`, `1080p`, `720p`, `480p`, `360p`, `audio`

## Proxy Pool

`proxy.py` tự động tải danh sách proxy từ một URL raw (mỗi dòng 1 proxy
dạng `ip:port`), rồi **chọn ngẫu nhiên 1 proxy** cho mỗi request tới YouTube
qua `yt_dlp`. Mục đích: tránh bị YouTube rate-limit / chặn theo IP của server.

**Cách hoạt động:**
- Khi khởi động, tải list proxy từ `PROXY_LIST_URL`
- Tự refresh lại sau mỗi `PROXY_REFRESH_SECS` giây (mặc định 300s = 5 phút)
- Mỗi request `/search`, `/video`, `/stream` → chọn 1 proxy ngẫu nhiên
- Nếu proxy đó lỗi (timeout, connection refused...) → tự đánh dấu "dead",
  chọn proxy khác, thử lại tối đa 4 lần
- Endpoint `/proxy/status` cho biết: tổng proxy, số dead, lần refresh cuối

**Biến môi trường:**

| Biến                  | Mặc định                                     | Mô tả                                  |
|-----------------------|-----------------------------------------------|------------------------------------------|
| `PROXY_LIST_URL`      | `http://nl-01.freezehost.pro:10861/raw`      | URL raw chứa list proxy (mỗi dòng 1 proxy)|
| `PROXY_REFRESH_SECS`  | `300`                                          | Số giây giữa các lần tự refresh list      |
| `PROXY_SCHEME`        | `http`                                         | `http` / `socks5` / `socks4`              |
| `USE_PROXY`           | `1`                                            | Set `0` để tắt hoàn toàn proxy pool       |

**Format list proxy hỗ trợ** (mỗi dòng):
```
1.2.3.4:8080
5.6.7.8:3128
9.10.11.12:1080:user:pass
http://1.2.3.4:8080
```

Nếu list nguồn die hoặc không có proxy nào sống, `yt_dlp` sẽ tự chạy
**không proxy** (request trực tiếp) để tránh app bị treo hoàn toàn.

## Deploy lên Render.com

### Bước 1: Đẩy lên GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

### Bước 2: Deploy proxy.py (server riêng tại botdic.nethr.nl:10416)
```bash
# Trên server botdic.nethr.nl
pip install -r requirements.txt
python proxy.py
# Hoặc dùng gunicorn:
gunicorn proxy:app --bind 0.0.0.0:10416 --workers 4 --timeout 120
```

### Bước 3: Deploy app.py lên Render.com
1. Vào [render.com](https://render.com) → New → Web Service
2. Kết nối GitHub repo
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
5. Thêm Environment Variable:
   - `PROXY_URL` = `http://botdic.nethr.nl:10416`

### Bước 4 (tuỳ chọn): Dùng render.yaml để auto-config
Render.com sẽ tự đọc `render.yaml` nếu bạn dùng Blueprint.

## Chạy local (test)

```bash
# Terminal 1 — proxy
PROXY_PORT=10416 python proxy.py

# Terminal 2 — app
PROXY_URL=http://localhost:10416 python app.py
```

Mở http://localhost:5000
