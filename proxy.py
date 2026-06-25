from flask import Flask, request, jsonify
import yt_dlp
import re
import os
import time
import random
import threading
import requests

app = Flask(__name__)

YDL_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "nocheckcertificate": True,
    "socket_timeout": 30,
}

# ─── PROXY POOL ──────────────────────────────────────────────────────────────
PROXY_LIST_URL = os.environ.get(
    "PROXY_LIST_URL", "http://nl-01.freezehost.pro:10861/raw"
)
PROXY_REFRESH_SECS = int(os.environ.get("PROXY_REFRESH_SECS", 300))  # 5 phút
PROXY_SCHEME = os.environ.get("PROXY_SCHEME", "http")  # http/socks5/socks4
USE_PROXY = os.environ.get("USE_PROXY", "1") == "1"


class ProxyPool:
    """Tải & quản lý danh sách proxy từ URL raw (mỗi dòng 1 proxy ip:port)."""

    def __init__(self, list_url, refresh_secs=300, scheme="http"):
        self.list_url = list_url
        self.refresh_secs = refresh_secs
        self.scheme = scheme
        self._proxies = []          # list "ip:port" còn sống / chưa test fail
        self._dead = set()          # proxy bị fail gần đây, tránh dùng lại ngay
        self._lock = threading.Lock()
        self._last_fetch = 0
        self.refresh(force=True)

    def _parse_raw(self, text):
        proxies = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Hỗ trợ vài format: "ip:port", "ip:port:user:pass", "http://ip:port"
            line = re.sub(r"^(https?|socks[45]):\/\/", "", line)
            if re.match(r"^[\w\.\-]+:\d+(:[\w\-\.@%]+:[\w\-\.@%]+)?$", line):
                proxies.append(line)
        return proxies

    def refresh(self, force=False):
        now = time.time()
        if not force and (now - self._last_fetch) < self.refresh_secs:
            return
        try:
            resp = requests.get(self.list_url, timeout=10)
            resp.raise_for_status()
            fresh = self._parse_raw(resp.text)
            if fresh:
                with self._lock:
                    self._proxies = fresh
                    self._dead.clear()  # cho cơ hội lại từ đầu sau mỗi lần refresh
                self._last_fetch = now
                print(f"[proxy-pool] Loaded {len(fresh)} proxies from {self.list_url}")
            else:
                print("[proxy-pool] Refresh returned 0 proxies, keeping old list")
        except Exception as e:
            print(f"[proxy-pool] Refresh failed: {e}")

    def get(self):
        """Trả về 1 proxy URL ngẫu nhiên (chưa bị mark dead), hoặc None."""
        self.refresh()  # tự refresh nếu đã quá hạn
        with self._lock:
            alive = [p for p in self._proxies if p not in self._dead]
            pool = alive or self._proxies  # nếu hết alive thì thử lại toàn bộ
            if not pool:
                return None
            choice = random.choice(pool)
        return f"{self.scheme}://{choice}"

    def mark_dead(self, proxy_url):
        raw = re.sub(r"^(https?|socks[45]):\/\/", "", proxy_url or "")
        with self._lock:
            self._dead.add(raw)

    def status(self):
        with self._lock:
            return {
                "total": len(self._proxies),
                "dead": len(self._dead),
                "alive": len(self._proxies) - len(self._dead & set(self._proxies)),
                "last_fetch_ago_secs": int(time.time() - self._last_fetch),
                "source": self.list_url,
            }


proxy_pool = ProxyPool(PROXY_LIST_URL, PROXY_REFRESH_SECS, PROXY_SCHEME) if USE_PROXY else None


def ydl_opts_with_proxy(base_opts):
    """Trả về (opts, proxy_url_used) — gắn proxy ngẫu nhiên nếu pool có sẵn."""
    opts = dict(base_opts)
    proxy_url = None
    if proxy_pool:
        proxy_url = proxy_pool.get()
        if proxy_url:
            opts["proxy"] = proxy_url
    return opts, proxy_url


def run_with_proxy_retry(extract_fn, base_opts, max_attempts=4):
    """Thử extract_info qua nhiều proxy khác nhau, mark_dead proxy lỗi rồi đổi proxy khác."""
    last_err = None
    attempts = max_attempts if proxy_pool else 1
    for _ in range(attempts):
        opts, proxy_url = ydl_opts_with_proxy(base_opts)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                result = extract_fn(ydl)
            return result, proxy_url
        except Exception as e:
            last_err = e
            if proxy_url and proxy_pool:
                proxy_pool.mark_dead(proxy_url)
            # Nếu không dùng proxy thì không có gì để đổi, raise ngay
            if not proxy_pool:
                break
    raise last_err


def sanitize_id(video_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "", video_id)

def format_number(n):
    if n is None:
        return "N/A"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def format_duration(secs):
    if secs is None:
        return "N/A"
    secs = int(secs)
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "yt-dlp proxy"})

@app.route("/proxy/status")
def proxy_status():
    if not proxy_pool:
        return jsonify({"enabled": False})
    return jsonify({"enabled": True, **proxy_pool.status()})

@app.route("/proxy/refresh")
def proxy_refresh():
    if not proxy_pool:
        return jsonify({"enabled": False})
    proxy_pool.refresh(force=True)
    return jsonify({"enabled": True, **proxy_pool.status()})

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    max_results = int(request.args.get("limit", 12))

    opts = {
        **YDL_OPTS_BASE,
        "extract_flat": True,
        "playlistend": max_results,
    }

    try:
        result, used_proxy = run_with_proxy_retry(
            lambda ydl: ydl.extract_info(f"ytsearch{max_results}:{query}", download=False),
            opts,
        )

        videos = []
        if result and "entries" in result:
            for entry in result["entries"]:
                if not entry:
                    continue
                vid_id = entry.get("id", "")
                videos.append({
                    "id": vid_id,
                    "title": entry.get("title", "Unknown"),
                    "channel": entry.get("uploader") or entry.get("channel", "Unknown"),
                    "duration": format_duration(entry.get("duration")),
                    "duration_secs": entry.get("duration"),
                    "views": format_number(entry.get("view_count")),
                    "views_raw": entry.get("view_count"),
                    "thumbnail": entry.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    "url": entry.get("url") or f"https://www.youtube.com/watch?v={vid_id}",
                })

        return jsonify({"results": videos, "query": query})

    except Exception as e:
        return jsonify({"error": str(e), "results": []}), 500

@app.route("/video")
def video_info():
    video_id = request.args.get("id", "").strip()
    if not video_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    video_id = sanitize_id(video_id)
    url = f"https://www.youtube.com/watch?v={video_id}"

    opts = {
        **YDL_OPTS_BASE,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        info, used_proxy = run_with_proxy_retry(
            lambda ydl: ydl.extract_info(url, download=False),
            opts,
        )

        if not info:
            return jsonify({"error": "Video not found"}), 404

        # Build formats list
        formats = []
        for f in (info.get("formats") or []):
            if f.get("vcodec") != "none" and f.get("acodec") != "none":
                formats.append({
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "quality": f.get("quality"),
                    "resolution": f.get("resolution") or f"{f.get('height', '?')}p",
                    "filesize": f.get("filesize"),
                    "url": f.get("url"),
                })

        # Thumbnails: prefer highest quality
        thumbnails = info.get("thumbnails") or []
        best_thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        if thumbnails:
            best = max(thumbnails, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), default=None)
            if best and best.get("url"):
                best_thumb = best["url"]

        return jsonify({
            "id": video_id,
            "title": info.get("title", "Unknown"),
            "description": (info.get("description") or "")[:500],
            "channel": info.get("uploader") or info.get("channel", "Unknown"),
            "channel_id": info.get("channel_id"),
            "upload_date": info.get("upload_date"),
            "duration": format_duration(info.get("duration")),
            "duration_secs": info.get("duration"),
            "views": format_number(info.get("view_count")),
            "views_raw": info.get("view_count"),
            "likes": format_number(info.get("like_count")),
            "thumbnail": best_thumb,
            "tags": (info.get("tags") or [])[:10],
            "formats": formats[-8:],  # last 8 = best quality ones
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stream")
def stream_url():
    video_id = request.args.get("id", "").strip()
    quality = request.args.get("quality", "best")
    if not video_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    video_id = sanitize_id(video_id)
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Map quality string to yt-dlp format selector
    quality_map = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        "360p": "best[height<=360]",
        "audio": "bestaudio[ext=m4a]/bestaudio",
    }

    fmt = quality_map.get(quality, quality_map["best"])

    opts = {
        **YDL_OPTS_BASE,
        "format": fmt,
        "skip_download": True,
    }

    try:
        info, used_proxy = run_with_proxy_retry(
            lambda ydl: ydl.extract_info(url, download=False),
            opts,
        )

        if not info:
            return jsonify({"error": "Could not get stream URL"}), 404

        # For merged formats, yt_dlp gives requested_formats
        requested = info.get("requested_formats") or []
        video_url = None
        audio_url = None

        if requested:
            for f in requested:
                if f.get("vcodec") and f["vcodec"] != "none":
                    video_url = f.get("url")
                if f.get("acodec") and f["acodec"] != "none":
                    audio_url = f.get("url")

        direct_url = info.get("url")

        return jsonify({
            "id": video_id,
            "title": info.get("title"),
            "duration": format_duration(info.get("duration")),
            "stream_url": video_url or direct_url,
            "audio_url": audio_url,
            "direct_url": direct_url,
            "ext": info.get("ext"),
            "quality": quality,
            "proxy_used": used_proxy,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PROXY_PORT", 10416))
    host = os.environ.get("PROXY_HOST", "0.0.0.0")
    print(f"[yt-dlp proxy] Running on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
