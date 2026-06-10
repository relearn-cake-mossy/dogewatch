from flask import Flask, render_template_string, request, jsonify, send_file, Response, stream_with_context
import time
import uuid
import requests

# KHAI BÁO BIẾN APP Ở CẤP CAO NHẤT (TOP-LEVEL) - SỬA LỖI VERCEL BUILD FAILED
app = Flask(__name__)
app.secret_key = 'vercel_cloud_hub_2026'

# Bộ nhớ tạm thời lưu dữ liệu tác vụ (Task Polling)
tasks = {}
results = {}
stream_links = {}  # Cổng lưu trữ link Youtube thực tế để làm trung gian Stream Tunnel

@app.route('/download/proxy')
def download_proxy():
    try:
        return send_file('proxy.py', as_attachment=True, download_name='proxy.py')
    except Exception:
        return "Proxy script file not found.", 404

# ==========================================================
# 💥 CỔNG TRUNG GIAN GIẢI MÃ: STREAM TUNNEL (SỬA LỖI ĐEN MÀN HÌNH & 403 FORBIDDEN)
# ==========================================================
@app.route('/stream_tunnel')
def stream_tunnel():
    video_id = request.args.get('v')
    real_url = stream_links.get(video_id)
    
    if not real_url:
        return "Video stream link expired or invalid. Please refresh and try again.", 404

    req_headers = {}
    if 'Range' in request.headers:
        req_headers['Range'] = request.headers['Range']
    req_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    try:
        # Vercel đứng ra tải hộ video từ YouTube theo từng đoạn nhỏ (Chunk)
        res = requests.get(real_url, headers=req_headers, stream=True, timeout=15)
        
        def generate():
            for chunk in res.iter_content(chunk_size=1024 * 256):  # 256KB mỗi chunk
                if chunk:
                    yield chunk

        tunnel_res = Response(stream_with_context(generate()), status=res.status_code)
        for key, value in res.headers.items():
            if key.lower() in ['content-type', 'content-range', 'accept-ranges', 'content-length']:
                tunnel_res.headers[key] = value
        
        # Ép thêm Header CORS để trình duyệt bypass qua mọi bộ lọc bảo mật
        tunnel_res.headers['Access-Control-Allow-Origin'] = '*'
        return tunnel_res
    except Exception as e:
        return f"Stream tunnel error: {str(e)}", 500

# --- APIS CHO HOME PROXY VÀO XIN VIỆC ---
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

# --- GIAO DIỆN PREMIUM WEB UI ---
@app.route('/')
def index():
    HTML_UI = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Cloud Video Hub</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: #08080c; color: #e2e2e9; font-family: 'Segoe UI', system-ui, sans-serif; }
            .navbar { background: #0f0f16 !important; border-bottom: 1px solid #1f1f2e; }
            .navbar-brand { font-weight: 900; color: #ff0055 !important; font-size: 24px; }
            .main-card { background: #0f0f16; border: 1px solid #1f1f2e; border-radius: 16px; padding: 25px; margin-bottom: 20px; }
            .form-control, .form-control:focus { background-color: #161622; color: #fff; border-color: #2b2b3d; }
            .btn-danger { background-color: #ff0055; border: none; font-weight: bold; }
            
            /* Video Player Custom Aesthetic Dark */
            .player-wrapper { position: relative; width: 100%; border-radius: 14px; overflow: hidden; background: #000; box-shadow: 0 20px 50px rgba(0,0,0,0.9); }
            .player-wrapper video { width: 100%; display: block; }
            .custom-controls { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.95)); padding: 20px; opacity: 0; transition: 0.3s; }
            .player-wrapper:hover .custom-controls { opacity: 1; }
            .progress-bar-container { height: 6px; background: rgba(255,255,255,0.2); cursor: pointer; border-radius: 10px; margin-bottom: 15px; }
            .progress-fill { height: 100%; width: 0%; background: linear-gradient(90deg, #ff0055, #ff5500); border-radius: 10px; }
            
            /* Video Items Grid */
            .v-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
            .v-item { background: #0f0f16; border-radius: 12px; overflow: hidden; border: 1px solid #1f1f2e; cursor: pointer; transition: 0.2s; }
            .v-item:hover { transform: translateY(-4px); border-color: #ff0055; }
            .v-thumb { width: 100%; aspect-ratio: 16/9; object-fit: cover; }
            .v-info { padding: 12px; font-size: 13.5px; font-weight: 600; line-height: 1.4; height: 50px; overflow: hidden; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark px-4 shadow-sm">
            <span class="navbar-brand">🪐 CLOUD STREAM CENTER</span>
            <a href="/download/proxy" class="btn btn-sm btn-outline-light"><i class="fas fa-download"></i> Download Proxy</a>
        </nav>

        <div class="container-fluid py-4 px-4">
            <div class="row">
                <div class="col-xl-3 col-lg-4">
                    <div class="main-card">
                        <h6 class="text-warning mb-3">🔍 GLOBAL SEARCH</h6>
                        <div class="input-group">
                            <input type="text" id="searchInput" class="form-control text-white" placeholder="Search on YouTube...">
                            <button onclick="runTask('search')" class="btn btn-danger">SEARCH</button>
                        </div>
                    </div>
                </div>

                <div class="col-xl-9 col-lg-8">
                    <div id="playerSection" class="main-card" style="display:none;">
                        <h5 id="vTitle" class="mb-3 text-info"></h5>
                        <div class="player-wrapper">
                            <video id="videoPlayer" autoplay controls></video>
                        </div>
                    </div>

                    <div class="main-card">
                        <h5 class="mb-4 border-bottom border-secondary pb-2">📂 DISCOVERY RESULTS</h5>
                        <div id="videoGrid" class="v-grid"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let currentTaskId = "";

            async function runTask(type, val = "") {
                const q = document.getElementById('searchInput').value;
                const btn = document.querySelector('.btn-danger');
                btn.disabled = true;
                btn.innerText = "WAITING PROXY...";
                
                const res = await fetch('/api/create_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: type, query: q, video_id: val})
                });
                const data = await res.json();
                currentTaskId = data.task_id;
                pollResult(type, val);
            }

            async function pollResult(type, val) {
                const res = await fetch('/api/poll_result?task_id=' + currentTaskId + '&video_id=' + val);
                const data = await res.json();
                
                if (data.status === 'completed') {
                    document.querySelector('.btn-danger').disabled = false;
                    document.querySelector('.btn-danger').innerText = "SEARCH";
                    renderData(data.result, data.tunnel_url);
                } else {
                    setTimeout(() => pollResult(type, val), 1500);
                }
            }

            function renderData(data, tunnelUrl) {
                if (data.videos) {
                    let html = "";
                    data.videos.forEach(v => {
                        html += `
                        <div class="v-item" onclick="playVideo('${v.id}')">
                            <img src="${v.thumbnail}" class="v-thumb">
                            <div class="v-info">${v.title}</div>
                        </div>`;
                    });
                    document.getElementById('videoGrid').innerHTML = html;
                }
                if (tunnelUrl) {
                    document.getElementById('playerSection').style.display = "block";
                    document.getElementById('vTitle').innerText = data.title;
                    const video = document.getElementById('videoPlayer');
                    video.src = tunnelUrl;
                    video.play();
                }
            }

            function playVideo(id) {
                runTask('extract', id);
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(HTML_UI)

@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'task_id': task_id,
        'type': data.get('type'),
        'query': data.get('query'),
        'video_id': data.get('video_id'),
        'status': 'pending'
    }
    return jsonify({"task_id": task_id})

@app.route('/api/poll_result')
def poll_result():
    task_id = request.args.get('task_id')
    video_id = request.args.get('video_id')
    
    if task_id in results:
        res_data = results[task_id]
        tunnel_url = None
        if res_data and 'stream_url' in res_data:
            stream_links[video_id] = res_data['stream_url']
            tunnel_url = f"/stream_tunnel?v={video_id}"
            
        return jsonify({"status": "completed", "result": res_data, "tunnel_url": tunnel_url})
    return jsonify({"status": "pending"})

if __name__ == '__main__':
    app.run(debug=True)
