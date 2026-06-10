from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import uuid
import time
import queue

app = Flask(__name__)
app.secret_key = 'vercel_ping_stream_2026'

# Quản lý trạng thái các task
tasks = {}
video_streams = {}

@app.route('/api/node/tasks', methods=['GET'])
def get_tasks():
    pending = [t for t in tasks.values() if t['status'] == 'pending']
    return jsonify(pending)

@app.route('/api/node/submit', methods=['POST'])
def submit_result():
    data = request.json
    task_id = data.get('task_id')
    if task_id in tasks:
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = data.get('result')
    return jsonify({"status": "received"})

@app.route('/api/node/upload_chunk', methods=['POST'])
def upload_chunk():
    session_id = request.args.get('session_id')
    chunk_data = request.data
    
    if session_id in video_streams:
        if len(chunk_data) == 0:
            video_streams[session_id].put(None)
        else:
            video_streams[session_id].put(chunk_data)
        return "OK", 200
    return "Session Expired", 410

@app.route('/stream/<session_id>')
def stream_video(session_id):
    if session_id not in video_streams:
        video_streams[session_id] = queue.Queue(maxsize=50)

    def generate():
        q = video_streams[session_id]
        consecutive_empty_loops = 0
        
        while True:
            try:
                chunk = q.get(timeout=2.0)
                if chunk is None:
                    break
                consecutive_empty_loops = 0
                yield chunk
            except queue.Empty:
                consecutive_empty_loops += 1
                if consecutive_empty_loops > 10:
                    break
                yield b''

    response = Response(stream_with_context(generate()), content_type="video/mp4")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

# =========================================================================
# GIAO DIỆN LUXURY FLUENT DARK - ĐÃ ĐƯỢC TINH CHỈNH MỊN MÀNG, TỈ LỆ CHUẨN UX
# =========================================================================
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DogeWatch Cloud Player</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            :root {
                --bg-main: #0c0c14;
                --bg-glow: radial-gradient(circle at 50% -20%, #1e1b4b 0%, #0c0c14 60%);
                --surface-card: rgba(22, 22, 38, 0.6);
                --surface-input: rgba(30, 30, 50, 0.7);
                --border-fluent: rgba(255, 255, 255, 0.08);
                --border-focus: #6366f1;
                --accent-color: #818cf8;
                --text-primary: #f3f4f6;
                --text-secondary: #9ca3af;
            }

            body {
                background: var(--bg-main);
                background-image: var(--bg-glow);
                color: var(--text-primary);
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                min-height: 100vh;
                letter-spacing: -0.01em;
            }

            .app-container {
                max-width: 1100px;
                padding-top: 2.5rem;
                padding-bottom: 2.5rem;
            }

            /* Acrylic Glass Effect */
            .fluent-card {
                background: var(--surface-card);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--border-fluent);
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                margin-bottom: 1.5rem;
            }

            .app-title {
                font-size: 1.35rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                background: linear-gradient(to right, #fff, #93c5fd);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* Custom Premium Input */
            .search-box-wrapper {
                position: relative;
                display: flex;
                gap: 10px;
            }

            .form-control {
                background: var(--surface-input);
                color: var(--text-primary);
                border: 1px solid var(--border-fluent);
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 0.95rem;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .form-control:focus {
                background: rgba(35, 35, 60, 0.9);
                color: #fff;
                border-color: var(--border-focus);
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
            }

            .form-control::placeholder {
                color: #555870;
            }

            .btn-fluent {
                background: var(--border-focus);
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 0.9rem;
                font-weight: 600;
                letter-spacing: 0.02em;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                white-space: nowrap;
            }

            .btn-fluent:hover {
                background: #4f46e5;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
            }

            .btn-fluent:active {
                transform: translateY(0);
            }

            /* Modern Compact Video Section */
            .player-section {
                display: none;
                background: #000;
                border-radius: 12px;
                overflow: hidden;
                margin-bottom: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            }

            video {
                width: 100%;
                aspect-ratio: 16 / 9;
                display: block;
                max-height: 560px;
            }

            /* Responsive Mịn Grid */
            .section-heading {
                font-size: 0.9rem;
                font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .v-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
                gap: 16px;
            }

            .v-item {
                background: rgba(20, 20, 35, 0.4);
                border-radius: 10px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.04);
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            }

            .v-item:hover {
                transform: translateY(-4px);
                border-color: rgba(255, 255, 255, 0.15);
                background: rgba(30, 30, 55, 0.6);
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
            }

            .v-thumb-container {
                position: relative;
                width: 100%;
                aspect-ratio: 16 / 9;
                background: #000;
                overflow: hidden;
            }

            .v-thumb {
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: transform 0.5s ease;
            }

            .v-item:hover .v-thumb {
                transform: scale(1.04);
            }

            .v-info {
                padding: 12px;
            }

            .v-title {
                font-size: 0.85rem;
                font-weight: 500;
                line-height: 1.4;
                color: var(--text-primary);
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                height: 2.8em;
            }

            /* Custom Skeleton / Dot Animation */
            .pulse-dot {
                width: 8px;
                height: 8px;
                background-color: #10b981;
                border-radius: 50%;
                display: inline-block;
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                animation: pulse 1.6s infinite;
            }

            @keyframes pulse {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }
        </style>
    </head>
    <body>
        <div class="container app-container">
            <div class="fluent-card d-flex align-items-center justify-content-between py-3">
                <div class="app-title">
                    <span class="pulse-dot"></span> DogeWatch Link Node
                </div>
                <span class="badge" style="background: rgba(255,255,255,0.06); border: 1px solid var(--border-fluent)">v2.5 P2P Hybrid</span>
            </div>

            <div class="fluent-card">
                <div class="search-box-wrapper">
                    <input type="text" id="searchInput" class="form-control" placeholder="Nhập tên video hoặc từ khóa bạn muốn tìm...">
                    <button onclick="runTask('search')" id="searchBtn" class="btn btn-fluent">
                        TÌM KIẾM
                    </button>
                </div>
            </div>

            <div id="playerSection" class="player-section shadow-lg">
                <video id="videoPlayer" autoplay controls playsinline></video>
            </div>

            <div class="fluent-card">
                <div class="section-heading">
                    📦 Danh sách kết quả tìm kiếm
                </div>
                <div id="videoGrid" class="v-grid">
                    <div class="text-center w-100 py-4" style="grid-column: 1/-1; color: var(--text-secondary); font-size: 0.9rem;">
                        Chưa có dữ liệu. Vui lòng nhập từ khóa tìm kiếm bên trên.
                    </div>
                </div>
            </div>
        </div>

        <script>
            let currentTaskId = "";
            let session_id = "";

            async function runTask(type, val = "") {
                const btn = document.getElementById('searchBtn');
                if (type === 'extract') {
                    session_id = "sess_" + Math.random().toString(36).substring(2, 15);
                    btn.disabled = true;
                    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>ĐANG KẾT NỐI...`;
                } else {
                    btn.disabled = true;
                    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>ĐANG TÌM...`;
                }
                
                const q = document.getElementById('searchInput').value;
                try {
                    const res = await fetch('/api/create_task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({type: type, query: q, video_id: val, session_id: session_id})
                    });
                    const d = await res.json();
                    currentTaskId = d.task_id;
                    pollResult();
                } catch(e) {
                    btn.disabled = false;
                    btn.innerText = "TÌM KIẾM";
                }
            }

            async function pollResult() {
                try {
                    const res = await fetch('/api/poll_result?task_id=' + currentTaskId);
                    const d = await res.json();
                    if (d.status === 'completed') {
                        const btn = document.getElementById('searchBtn');
                        btn.disabled = false;
                        btn.innerText = "TÌM KIẾM";
                        
                        if(d.result.videos) renderGrid(d.result.videos);
                        if(d.result.streaming_ready) {
                            document.getElementById('playerSection').style.display = "block";
                            const player = document.getElementById('videoPlayer');
                            player.src = "/stream/" + session_id;
                            player.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    } else { 
                        setTimeout(pollResult, 1000); 
                    }
                } catch(e) {
                    const btn = document.getElementById('searchBtn');
                    btn.disabled = false;
                    btn.innerText = "TÌM KIẾM";
                }
            }

            function renderGrid(videos) {
                let h = "";
                if(videos.length === 0) {
                    h = `<div class="text-center w-100 py-4" style="grid-column: 1/-1; color: var(--text-secondary);">Không tìm thấy video nào.</div>`;
                    document.getElementById('videoGrid').innerHTML = h;
                    return;
                }
                videos.forEach(v => {
                    h += `<div class="v-item" onclick="runTask('extract', '${v.id}')">
                        <div class="v-thumb-container">
                            <img src="${v.thumbnail}" class="v-thumb" loading="lazy">
                        </div>
                        <div class="v-info">
                            <div class="v-title">${v.title}</div>
                        </div>
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
    tasks[tid] = {
        'task_id': tid, 'type': data.get('type'), 'query': data.get('query'), 
        'video_id': data.get('video_id'), 'session_id': data.get('session_id'), 'status': 'pending'
    }
    return jsonify({"task_id": tid})

@app.route('/api/poll_result')
def poll_result():
    tid = request.args.get('task_id')
    if tid in tasks and tasks[tid]['status'] == 'completed':
        return jsonify({"status": "completed", "result": tasks[tid]['result']})
    return jsonify({"status": "pending"})
