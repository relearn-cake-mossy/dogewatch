from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.exceptions import HTTPException
import yt_dlp
import re
import os

app = Flask(__name__)

# ─── COOKIE ──────────────────────────────────────────────────────────────────
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_COOKIE_FILE = os.path.join(_APP_DIR, "youtube_cookies.txt")

YDL_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
    "nocheckcertificate": True,
    "socket_timeout": 15,
}
if os.path.isfile(_COOKIE_FILE):
    YDL_OPTS_BASE["cookiefile"] = _COOKIE_FILE
    print(f"[cookies] Loaded: {_COOKIE_FILE}")
else:
    print("[cookies] No cookie file found")


# ─── ERROR HANDLER: /api/* luôn trả JSON, không bao giờ trả HTML ─────────────
@app.errorhandler(Exception)
def handle_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": str(e), "results": []}), 500
    if isinstance(e, HTTPException):
        return e
    raise e


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def sanitize_id(video_id):
    return re.sub(r"[^a-zA-Z0-9_\-]", "", video_id)

def fmt_num(n):
    if n is None: return "N/A"
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def fmt_dur(secs):
    if secs is None: return "N/A"
    secs = int(secs)
    h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def ydl_run(extract_fn, extra_opts=None):
    opts = {**YDL_OPTS_BASE, **(extra_opts or {})}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return extract_fn(ydl)


# ─── GIAO DIỆN ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/watch")
def watch():
    v = request.args.get("v", "")
    return render_template("index.html", video_id=v) if v else redirect("/")


# ─── API ─────────────────────────────────────────────────────────────────────
@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing q"}), 400
    limit = int(request.args.get("limit", 12))
    try:
        result = ydl_run(
            lambda ydl: ydl.extract_info(f"ytsearch{limit}:{query}", download=False),
            {"extract_flat": True, "playlistend": limit},
        )
        videos = []
        for e in (result or {}).get("entries") or []:
            if not e: continue
            vid = e.get("id", "")
            videos.append({
                "id": vid,
                "title": e.get("title", "Unknown"),
                "channel": e.get("uploader") or e.get("channel", "Unknown"),
                "duration": fmt_dur(e.get("duration")),
                "views": fmt_num(e.get("view_count")),
                "thumbnail": e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            })
        return jsonify({"results": videos, "query": query})
    except Exception as e:
        return jsonify({"error": str(e), "results": []}), 500


@app.route("/api/video")
def video_info():
    video_id = sanitize_id(request.args.get("id", "").strip())
    if not video_id:
        return jsonify({"error": "Missing id"}), 400
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        info = ydl_run(
            lambda ydl: ydl.extract_info(url, download=False),
            {"extract_flat": False, "skip_download": True},
        )
        if not info:
            return jsonify({"error": "Video not found"}), 404

        thumbs = info.get("thumbnails") or []
        best_thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        if thumbs:
            b = max(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), default=None)
            if b and b.get("url"): best_thumb = b["url"]

        return jsonify({
            "id": video_id,
            "title": info.get("title", "Unknown"),
            "description": (info.get("description") or "")[:500],
            "channel": info.get("uploader") or info.get("channel", "Unknown"),
            "duration": fmt_dur(info.get("duration")),
            "views": fmt_num(info.get("view_count")),
            "likes": fmt_num(info.get("like_count")),
            "thumbnail": best_thumb,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stream")
def stream_url():
    video_id = sanitize_id(request.args.get("id", "").strip())
    quality = request.args.get("quality", "best")
    if not video_id:
        return jsonify({"error": "Missing id"}), 400
    url = f"https://www.youtube.com/watch?v={video_id}"
    quality_map = {
        "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "480p":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        "360p":  "best[height<=360]",
        "audio": "bestaudio[ext=m4a]/bestaudio",
    }
    try:
        info = ydl_run(
            lambda ydl: ydl.extract_info(url, download=False),
            {"format": quality_map.get(quality, quality_map["best"]), "skip_download": True},
        )
        if not info:
            return jsonify({"error": "Could not get stream URL"}), 404

        video_url = audio_url = None
        for f in (info.get("requested_formats") or []):
            if f.get("vcodec") and f["vcodec"] != "none": video_url = f.get("url")
            if f.get("acodec") and f["acodec"] != "none": audio_url = f.get("url")

        return jsonify({
            "id": video_id,
            "title": info.get("title"),
            "stream_url": video_url or info.get("url"),
            "audio_url": audio_url,
            "ext": info.get("ext"),
            "quality": quality,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
