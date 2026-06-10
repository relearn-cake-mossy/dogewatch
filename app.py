from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import uuid
import requests

app = Flask(__name__)
app.secret_key = 'vercel_global_hub_2026'

tasks = {}
results = {}
# Bộ nhớ tạm lưu link YouTube gốc do máy nhà gửi lên
global_streams = {}

# --- API ĐỒNG BỘ VỚI PROXY Ở NHÀ ---
@app.route('/api/node/tasks', methods=['GET'])
def get_tasks():
    pending = [t for t in tasks.values() if t['status'] == 'pending']
    return jsonify(pending)

@app.route('/api/node/submit', methods=['POST'])
def submit_result():
    data = request.json
    task_id = data.get('task_id')
    if task_id in tasks:
        results[task_id] = data.get('result')
        tasks[task_id]['status'] = 'completed'
    return jsonify({"status": "received"})

# ==========================================================
# 🚀 ĐƯỜNG ỐNG TRUNG CHUYỂN TOÀN CẦU (Bypass mọi giới hạn mạng)
# ==========================================================
@app.route('/global_stream/<video_id>')
def global_stream(video_id):
    real_youtube_url = global_streams.get(video_id)
    if not real_youtube_url:
        return "Luồng video đã hết hạn hoặc không hợp lệ. Vui lòng thử lại.", 404

    # Copy lại Header Range từ trình duyệt để tua video mượt mà
    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    if 'Range' in request.headers:
        req_headers['Range'] = request.headers['Range']

    try:
        # Vercel trực tiếp kéo luồng dữ liệu từ YouTube
        res = requests.get(real_youtube_url, headers=req_headers, stream=True, timeout=10)
        
        def generate():
            # Đọc và đẩy liên tục từng cụm 256KB về điện thoại
            for chunk in res.iter_content(chunk_size=1024 * 256):
                if chunk: yield chunk

        response = Response(stream_with_context(generate()), status=res.status_code)
        
        # Chuyển tiếp các Header quan trọng liên quan đến Video Player
        for k, v in res.headers.items():
            if k.lower() in ['content-type', 'content-range', 'accept-ranges', 'content-length']:
                response.headers[k] = v
                
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return f"Stream lỗi: {str(e)}", 500

# --- INTERFACE WEB ---
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Global Video Hub</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #07070a; color: #e1e1e8; font-family: system-ui, sans-serif; }
            .main-card { background: #0f0f17; border: 1px solid #1f1f2e; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
            .form-control { background-color: #161622; color: #fff; border-color: #2b2b3d; }
            .btn-danger { background-color: #ff0055; border: none; font-weight: bold; }
            .player-section { display: none; background: #000; border-radius: 12px; overflow: hidden; margin-bottom: 20px; border: 1px solid #ff0055; }
            video { width: 100%; display: block; max-height: 480px; }
            .v-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; }
            .v-item { background: #0f0f17; border-radius: 8px; overflow: hidden; border: 1px solid #1f1f2e; cursor: pointer; }
            .v-item:hover { border-color: #ff0055; }
            .v-thumb { width: 100%; aspect-ratio: 16/9; object-fit: cover; }
            .v-info { padding: 8px; font-size: 12.5px; height: 40px; overflow: hidden; }
        </style>
    </head>
    <body>
        <div class="container py-4">
            <h4 class="text-danger fw-bold mb-3">🪐 GLOBAL CLOUD STREAM</h4>
            <div class="main-card">
                <div class="input-group">
                    <input type="text" id="searchInput" class="form-control" placeholder="Tìm kiếm video mọi lúc mọi nơi...">
                    <button onclick="runTask('search')" class="btn btn-danger px-4">TÌM KIẾM</button>
                </div>
            </div>

            <div id="playerSection" class="player-section shadow-lg">
                <video id="videoPlayer" autoplay controls playsinline></video>
            </div>

            <div class="main-card">
                <div id="videoGrid" class="v-grid"></div>
            </div>
        </div>

        <script>
            let currentTaskId = "";
            let currentVid = "";

            async function runTask(type, val = "") {
                if(type === 'extract') currentVid = val;
                const q = document.getElementById('searchInput').value;
                document.querySelector('.btn-danger').innerText = "ĐANG XỬ LÝ...";
                
                const res = await fetch('/api/create_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: type, query: q, video_id: val})
                });
                const d = await res.json();
                currentTaskId = d.task_id;
                pollResult();
            }

            async function pollResult() {
                const res = await fetch('/api/poll_result?task_id=' + currentTaskId + '&video_id=' + currentVid);
                const d = await res.json();
                if (d.status === 'completed') {
                    document.querySelector('.btn-danger').innerText = "TÌM KIẾM";
                    if(d.result.videos) renderGrid(d.result.videos);
                    if(d.tunnel_url) {
                        document.getElementById('playerSection').style.display = "block";
                        document.getElementById('videoPlayer').src = d.tunnel_url;
                    }
                } else { setTimeout(pollResult, 1500); }
            }

            function renderGrid(videos) {
                let h = "";
                videos.forEach(v => {
                    h += `<div class="v-item" onclick="runTask('extract', '${v.id}')">
                        <img src="${v.thumbnail}" class="v-thumb">
                        <div class="v-info">${v.title}</div>
                    </div>`;
                });
                document.getElementById('videoGrid').innerHTML = h;
            }
        </script>
    </body>
    </html>
    """)

@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    tid = str(uuid.uuid4())
    tasks[tid] = {'task_id': tid, 'type': data.get('type'), 'query': data.get('query'), 'video_id': data.get('video_id'), 'status': 'pending'}
    return jsonify({"task_id": tid})

@app.route('/api/poll_result')
def poll_result():
    tid = request.args.get('task_id')
    vid = request.args.get('video_id')
    if tid in results:
        res_data = results[tid]
        tunnel_url = None
        if res_data and 'stream_url' in res_data:
            # Lưu link vào RAM Vercel để phục vụ phiên xem hiện tại
            global_streams[vid] = res_data['stream_url']
            tunnel_url = f"/global_stream/{vid}"
        return jsonify({"status": "completed", "result": res_data, "tunnel_url": tunnel_url})
    return jsonify({"status": "pending"})
