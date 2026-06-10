# app.py
import time
import uuid
from flask import Flask, render_template_string, request, jsonify, send_file

app = Flask(__name__)
app.secret_key = 'vercel_cloud_hub_2026'

# Stateless storage (Lưu ý: Vercel reset bộ nhớ thường xuyên, 
# nhưng đủ để xử lý các tác vụ tức thời)
tasks = {}
results = {}
online_nodes = {}

@app.route('/download/proxy')
def download_proxy():
    return send_file('proxy.py', as_attachment=True)

# --- API FOR HOME PROXY ---
@app.route('/api/node/register', methods=['POST'])
def register_node():
    data = request.json
    node_id = data.get('node_id')
    online_nodes[node_id] = {
        'info': data.get('info'),
        'last_seen': time.time()
    }
    return jsonify({"status": "registered"})

@app.route('/api/node/tasks', methods=['GET'])
def get_tasks():
    # Proxy gọi vào đây để lấy việc
    node_id = request.args.get('node_id')
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

# --- MAIN UI ---
@app.route('/')
def index():
    search_q = request.args.get('q', '')
    video_id = request.args.get('v', '')
    
    # Tạo Task ID duy nhất cho mỗi lần nhấn
    current_task_id = str(uuid.uuid4())
    
    HTML_UI = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Cloud Video Hub</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: #0a0a0c; color: #e2e2e9; font-family: 'Segoe UI', sans-serif; }
            .navbar { background: #111 !important; border-bottom: 1px solid #222; }
            .navbar-brand { font-weight: 900; color: #ff0055 !important; }
            .main-card { background: #12121a; border: 1px solid #1f1f2e; border-radius: 16px; padding: 25px; margin-bottom: 20px; }
            .btn-danger { background: #ff0055; border: none; font-weight: bold; }
            .proxy-badge { font-size: 11px; padding: 5px 12px; border-radius: 20px; background: #1a1a26; border: 1px solid #333; }
            
            /* Custom Player */
            .player-wrapper { position: relative; width: 100%; border-radius: 15px; overflow: hidden; background: #000; box-shadow: 0 10px 40px rgba(0,0,0,0.8); }
            .player-wrapper video { width: 100%; display: block; }
            .custom-controls { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.9)); padding: 20px; opacity: 0; transition: 0.3s; }
            .player-wrapper:hover .custom-controls { opacity: 1; }
            .progress-bar { height: 5px; background: rgba(255,255,255,0.2); cursor: pointer; border-radius: 10px; margin-bottom: 15px; }
            .progress-fill { height: 100%; width: 0%; background: #ff0055; border-radius: 10px; }
            
            /* Video Grid */
            .v-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
            .v-item { background: #161622; border-radius: 12px; overflow: hidden; border: 1px solid #222; text-decoration: none; color: inherit; transition: 0.2s; }
            .v-item:hover { transform: translateY(-5px); border-color: #ff0055; }
            .v-thumb { width: 100%; aspect-ratio: 16/9; object-fit: cover; }
            .v-info { padding: 12px; font-size: 13px; font-weight: 600; line-height: 1.4; height: 50px; overflow: hidden; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark px-4 shadow-sm">
            <span class="navbar-brand">🪐 CLOUD STREAM CENTER</span>
            <div id="nodeStatus">Checking Proxy Nodes...</div>
        </nav>

        <div class="container-fluid py-4 px-4">
            <div class="row">
                <div class="col-lg-3">
                    <div class="main-card">
                        <h6 class="text-warning mb-3">🔍 GLOBAL SEARCH</h6>
                        <input type="text" id="searchInput" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Enter keywords..." value="{{ search_q }}">
                        <button onclick="runTask('search')" class="btn btn-danger w-100">SEARCH NOW</button>
                    </div>
                    <div class="main-card text-center">
                        <p class="text-muted small">No active nodes? Run the script at home.</p>
                        <a href="/download/proxy" class="btn btn-sm btn-outline-light w-100">📥 DOWNLOAD PROXY</a>
                    </div>
                </div>

                <div class="col-lg-9">
                    <div id="statusAlert" class="alert alert-info" style="display:none;"></div>
                    
                    <div id="playerSection" class="main-card" style="display:none;">
                        <h5 id="vTitle" class="mb-3 text-info"></h5>
                        <div class="player-wrapper">
                            <video id="videoPlayer" autoplay></video>
                            <div class="custom-controls">
                                <div class="progress-bar" onclick="seek(event)"><div class="progress-fill" id="pFill"></div></div>
                                <div class="d-flex justify-content-between align-items-center">
                                    <button class="btn btn-sm text-white" onclick="togglePlay()"><i id="playIcon" class="fas fa-pause"></i></button>
                                    <span class="small" id="timeShow">00:00 / 00:00</span>
                                    <button class="btn btn-sm text-white" onclick="toggleFS()"><i class="fas fa-expand"></i></button>
                                </div>
                            </div>
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
                const v = val || new URLSearchParams(window.location.search).get('v');
                
                const btn = document.querySelector('.btn-danger');
                btn.disabled = true;
                btn.innerText = "WAITING FOR PROXY...";
                
                const res = await fetch('/api/create_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: type, query: q, video_id: v})
                });
                const data = await res.json();
                currentTaskId = data.task_id;
                pollResult();
            }

            async function pollResult() {
                const res = await fetch('/api/poll_result?task_id=' + currentTaskId);
                const data = await res.json();
                
                if (data.status === 'completed') {
                    document.querySelector('.btn-danger').disabled = false;
                    document.querySelector('.btn-danger').innerText = "SEARCH NOW";
                    renderData(data.result);
                } else {
                    setTimeout(pollResult, 2000); // Thử lại sau 2 giây
                }
            }

            function renderData(data) {
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
                if (data.stream_url) {
                    document.getElementById('playerSection').style.display = "block";
                    document.getElementById('vTitle').innerText = data.title;
                    const video = document.getElementById('videoPlayer');
                    video.src = data.stream_url;
                    video.play();
                }
            }

            function playVideo(id) {
                runTask('extract', id);
                window.scrollTo({top: 0, behavior: 'smooth'});
            }

            // Player Logic
            const v = document.getElementById('videoPlayer');
            function togglePlay() { 
                if(v.paused) { v.play(); document.getElementById('playIcon').className = 'fas fa-pause'; }
                else { v.pause(); document.getElementById('playIcon').className = 'fas fa-play'; }
            }
            v.ontimeupdate = () => {
                const pct = (v.currentTime / v.duration) * 100;
                document.getElementById('pFill').style.width = pct + "%";
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(HTML_UI, search_q=search_q)

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
    if task_id in results:
        return jsonify({"status": "completed", "result": results[task_id]})
    return jsonify({"status": "pending"})

if __name__ == '__main__':
    app.run(debug=True)
