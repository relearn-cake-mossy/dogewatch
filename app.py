from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os

app = Flask(__name__)

PROXY_URL = os.environ.get("PROXY_URL", "http://botdic.nethr.nl:10416")

def call_proxy(endpoint, params=None):
    try:
        url = f"{PROXY_URL}{endpoint}"
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing query"}), 400
    data = call_proxy("/search", {"q": query})
    return jsonify(data)

@app.route("/api/video")
def video_info():
    video_id = request.args.get("id", "")
    if not video_id:
        return jsonify({"error": "Missing video id"}), 400
    data = call_proxy("/video", {"id": video_id})
    return jsonify(data)

@app.route("/api/stream")
def stream_url():
    video_id = request.args.get("id", "")
    quality = request.args.get("quality", "best")
    if not video_id:
        return jsonify({"error": "Missing video id"}), 400
    data = call_proxy("/stream", {"id": video_id, "quality": quality})
    return jsonify(data)

@app.route("/watch")
def watch():
    video_id = request.args.get("v", "")
    if not video_id:
        return redirect(url_for("index"))
    return render_template("index.html", video_id=video_id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
