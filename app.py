from flask import Flask, request, jsonify, Response, render_template_string
import uuid
import time

app = Flask(__name__)

# In-memory cluster arrays
tasks_queue = []
tasks_results = {}
video_buffers = {}
active_nodes = {}  # Tracking client node heartbeats

# High-fidelity Windows 11 Fluent Design & Aesthetic Dark Interface Layout
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DogeWatch Nexus - Premium Core</title>
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-mica: #030307;
            --bg-acrylic: rgba(15, 15, 23, 0.7);
            --bg-card: rgba(30, 30, 45, 0.45);
            --bg-card-hover: rgba(45, 45, 65, 0.6);
            --accent-primary: #60cdff;
            --accent-system: #0078d4;
            --accent-glow: rgba(96, 205, 255, 0.25);
            --text-main: #ffffff;
            --text-secondary: #adadbc;
            --text-disabled: #646473;
            --border-fluent: rgba(255, 255, 255, 0.07);
            --border-fluent-bright: rgba(255, 255, 255, 0.12);
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --transition-fluent: all 0.25s cubic-bezier(0.1, 0.9, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background: var(--bg-mica);
            color: var(--text-main);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* --- GLOBAL FLUENT HEADER --- */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 24px;
            height: 56px;
            background: var(--bg-acrylic);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border-bottom: 1px solid var(--border-fluent);
            z-index: 100;
            flex-shrink: 0;
        }

        .brand-zone {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            background: linear-gradient(135deg, #fff 0%, var(--accent-primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .build-tag {
            font-size: 0.65rem;
            background: rgba(255, 255, 255, 0.05);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            border: 1px solid var(--border-fluent);
            font-family: monospace;
        }

        /* --- TELEMETRY NODE BADGE --- */
        .node-telemetry-card {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-fluent);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            transition: var(--transition-fluent);
        }

        .node-telemetry-card:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: var(--border-fluent-bright);
        }

        .status-indicator {
            position: relative;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2ccb5b;
            box-shadow: 0 0 10px #2ccb5b;
        }

        .status-indicator.pulse::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: inherit;
            animation: fluentPulse 2s infinite ease-in-out;
        }

        .status-indicator.offline {
            background: #f74343;
            box-shadow: 0 0 10px #f74343;
        }

        .node-details {
            display: flex;
            flex-direction: column;
            line-height: 1.2;
        }

        .node-label { color: var(--text-secondary); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
        .node-value { font-weight: 500; color: var(--text-main); }

        /* --- MAIN CONTAINER STRUCTURE --- */
        .app-shell {
            display: flex;
            flex: 1;
            overflow: hidden;
            position: relative;
        }

        /* --- SIDEBAR NAVIGATION --- */
        nav.sidebar {
            width: 260px;
            background: rgba(10, 10, 15, 0.4);
            border-right: 1px solid var(--border-fluent);
            padding: 16px 8px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            flex-shrink: 0;
        }

        @media (max-width: 850px) {
            nav.sidebar { display: none; }
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            color: var(--text-secondary);
            border-radius: var(--radius-md);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: var(--transition-fluent);
            cursor: pointer;
            position: relative;
        }

        .nav-item:hover {
            background: var(--bg-card-hover);
            color: var(--text-main);
        }

        .nav-item.active {
            background: var(--bg-card);
            color: var(--accent-primary);
            font-weight: 600;
        }

        .nav-item.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 25%;
            height: 50%;
            width: 3px;
            background: var(--accent-primary);
            border-radius: var(--radius-sm);
        }

        .nav-category {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--text-disabled);
            padding: 12px 14px 6px 14px;
            letter-spacing: 0.8px;
        }

        /* --- WORKSPACE VIEWSPACE --- */
        main.workspace {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            background: radial-gradient(circle at top right, rgba(0, 120, 212, 0.05), transparent 600px);
        }

        /* --- INTEGRATED SEARCH HEADER --- */
        .search-container {
            max-width: 640px;
            margin: 0 auto 32px auto;
        }

        .fluent-search-bar {
            display: flex;
            background: var(--bg-card);
            border: 1px solid var(--border-fluent);
            border-bottom: 1px solid var(--border-fluent-bright);
            padding: 5px;
            border-radius: var(--radius-md);
            box-shadow: inset 0 1px 1px rgba(255,255,255,0.04);
            transition: var(--transition-fluent);
        }

        .fluent-search-bar:focus-within {
            background: rgba(20, 20, 30, 0.8);
            border-color: var(--accent-primary);
            box-shadow: 0 0 16px var(--accent-glow);
        }

        .fluent-search-bar input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-main);
            padding: 8px 16px;
            font-size: 0.9rem;
        }

        .fluent-search-bar input::placeholder { color: var(--text-disabled); }

        .fluent-search-bar button {
            background: var(--accent-system);
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
            padding: 0 20px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition-fluent);
        }

        .fluent-search-bar button:hover {
            background: #0086f0;
            box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
        }

        /* --- HIGH-END HOLLYWOOD THEATER VIEW (PLAYER) --- */
        #theater-stage {
            display: none;
            max-width: 1000px;
            margin: 0 auto 36px auto;
            animation: fluentReveal 0.40s cubic-bezier(0.1, 0.9, 0.2, 1) forwards;
        }

        .player-canvas {
            width: 100%;
            aspect-ratio: 16 / 9;
            background: #000;
            border-radius: var(--radius-lg);
            overflow: hidden;
            border: 1px solid var(--border-fluent);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
            position: relative;
        }

        .player-canvas video {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        /* --- MODERN CONTENT TYPOGRAPHY --- */
        .section-header {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--text-secondary);
            margin-bottom: 18px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section-header::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border-fluent);
        }

        /* --- EXTENSIVE MATRIX VIDEO GRID --- */
        .matrix-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        @media (max-width: 500px) {
            .matrix-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
        }

        .fluent-card {
            background: var(--bg-card);
            border: 1px solid var(--border-fluent);
            border-radius: var(--radius-lg);
            overflow: hidden;
            cursor: pointer;
            position: relative;
            transition: var(--transition-fluent);
        }

        .fluent-card:hover {
            transform: translateY(-4px);
            background: var(--bg-card-hover);
            border-color: rgba(255, 255, 255, 0.15);
            box-shadow: 0 12px 28px rgba(0,0,0,0.45);
        }

        .card-viewscreen {
            position: relative;
            width: 100%;
            aspect-ratio: 16 / 9;
            background: #07070a;
            overflow: hidden;
        }

        .card-viewscreen img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }

        .fluent-card:hover .card-viewscreen img {
            transform: scale(1.03);
        }

        .card-metadata {
            padding: 12px;
        }

        .card-title {
            font-size: 0.85rem;
            font-weight: 500;
            line-height: 1.4;
            color: var(--text-main);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 2.8em;
        }

        /* --- ADVANCED SKELETON LOAD SHIMMER --- */
        .skeleton-card {
            background: var(--bg-card);
            border: 1px solid var(--border-fluent);
            border-radius: var(--radius-lg);
            height: 215px;
            overflow: hidden;
            position: relative;
        }

        .skeleton-shimmer {
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.03) 50%, transparent 100%);
            background-size: 200% 100%;
            animation: fluentShimmer 1.5s infinite linear;
        }

        /* --- TELEMETRY STATUS PANEL --- */
        .loading-dashboard {
            display: none;
            background: rgba(255,255,255,0.01);
            border: 1px dashed var(--border-fluent);
            border-radius: var(--radius-lg);
            padding: 16px;
            text-align: center;
            max-width: 400px;
            margin: 20px auto;
            font-size: 0.85rem;
            color: var(--accent-primary);
        }

        /* --- ANIMATION ARRAYS --- */
        @keyframes fluentPulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(44, 203, 91, 0.5); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(44, 203, 91, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(44, 203, 91, 0); }
        }
        @keyframes fluentShimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        @keyframes fluentReveal {
            from { opacity: 0; transform: translateY(12px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
    </style>
</head>
<body>

    <header>
        <div class="brand-zone">
            <span class="brand-logo">DOGEWATCH // NEXUS</span>
            <span class="build-tag">v3.5.0-EJS</span>
        </div>
        
        <div class="node-telemetry-card" id="node-matrix-badge">
            <div class="status-indicator offline pulse" id="telemetry-dot"></div>
            <div class="node-details">
                <span class="node-label">Cluster Uplink</span>
                <span class="node-value" id="telemetry-text">Locating Node...</span>
            </div>
        </div>
    </header>

    <div class="app-shell">
        <nav class="sidebar">
            <span class="nav-category">Discover</span>
            <div class="nav-item active" onclick="loadDiscoverFeed()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
                Home Feed
            </div>
            <div class="nav-item" onclick="setSearchFocus()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                Search Station
            </div>
            
            <span class="nav-category">System Hierarchy</span>
            <div class="nav-item" style="cursor: default; opacity: 0.6;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect></svg>
                Core Proxy Active
            </div>
        </nav>

        <main class="workspace">
            
            <div class="search-container">
                <div class="fluent-search-bar">
                    <input type="text" id="nexus-search-input" placeholder="Query global video stream nodes...">
                    <button onclick="executeNexusSearch()">Search Network</button>
                </div>
            </div>

            <div id="theater-stage">
                <div class="player-canvas">
                    <video id="nexus-core-player" controls autoplay playsinline crossorigin="anonymous"></video>
                </div>
            </div>

            <div class="loading-dashboard" id="nexus-pipeline-loader">
                Parsing encryption layer & piping chunk sequences...
            </div>

            <h3 class="section-header" id="workspace-view-title">Network Index Feed</h3>
            
            <div class="matrix-grid" id="workspace-view-grid">
                </div>
        </main>
    </div>

    <script>
        // 1. Maintain dynamic socket telemetry diagnostics for local proxy nodes
        function runTelemetryDiagnostics() {
            fetch('/api/web/node_status')
                .then(res => res.json())
                .then(data => {
                    const dot = document.getElementById('telemetry-dot');
                    const valueStr = document.getElementById('telemetry-text');
                    if (data.connected) {
                        dot.className = "status-indicator pulse";
                        valueStr.innerText = `Home Proxy (${data.last_seen}s back)`;
                    } else {
                        dot.className = "status-indicator offline";
                        valueStr.innerText = "Uplink Terminated";
                    }
                });
        }

        // 2. Generate multi-card mock skeletons during network load sequences
        function renderGridSkeletons() {
            const grid = document.getElementById('workspace-view-grid');
            grid.innerHTML = '';
            for (let i = 0; i < 8; i++) {
                const skeleton = document.createElement('div');
                skeleton.className = 'skeleton-card';
                skeleton.innerHTML = '<div class="skeleton-shimmer"></div>';
                grid.appendChild(skeleton);
            }
        }

        // 3. Automated initial content feed download sequence
        function loadDiscoverFeed() {
            document.getElementById('workspace-view-title').innerText = "System Recommended Feed";
            renderGridSkeletons();
            
            fetch('/api/web/search?q=mrbeast%20trending')
                .then(res => res.json())
                .then(data => {
                    populateMatrixGrid(data.videos);
                }).catch(() => {
                    document.getElementById('workspace-view-grid').innerHTML = '';
                });
        }

        function setSearchFocus() {
            document.getElementById('nexus-search-input').focus();
        }

        function executeNexusSearch() {
            const query = document.getElementById('nexus-search-input').value.trim();
            if (!query) return;

            document.getElementById('workspace-view-title').innerText = `Network Query Index: "${query}"`;
            renderGridSkeletons();

            fetch(`/api/web/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    populateMatrixGrid(data.videos);
                });
        }

        // 4. Construct high-fidelity fluent object elements directly inside grid matrix
        function populateMatrixGrid(videos) {
            const grid = document.getElementById('workspace-view-grid');
            grid.innerHTML = '';
            
            if (!videos || videos.length === 0) {
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-disabled); font-size:0.9rem;">No responsive nodes found matching parameters.</div>';
                return;
            }

            videos.forEach(v => {
                const card = document.createElement('div');
                card.className = 'fluent-card';
                card.onclick = () => mountStreamPipeline(v.id);
                card.innerHTML = `
                    <div class="card-viewscreen">
                        <img src="${v.thumbnail}" alt="node_thumb" loading="lazy">
                    </div>
                    <div class="card-metadata">
                        <div class="card-title">${v.title}</div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        // 5. Mount encrypted backend stream array logic down to active proxy channels
        function mountStreamPipeline(videoId) {
            const stage = document.getElementById('theater-stage');
            const player = document.getElementById('nexus-core-player');
            const dashboard = document.getElementById('nexus-pipeline-loader');

            stage.style.display = 'block';
            dashboard.style.display = 'block';
            stage.scrollIntoView({ behavior: 'smooth', block: 'center' });

            fetch(`/api/web/extract?video_id=${videoId}`)
                .then(res => res.json())
                .then(data => {
                    dashboard.style.display = 'none';
                    if (data.session_id) {
                        player.src = `/api/stream?session_id=${data.session_id}`;
                        player.play();
                    } else {
                        alert("Nexus Pipeline Interrupted: Local routing gateway dropped task execution packets.");
                    }
                }).catch(() => {
                    dashboard.style.display = 'none';
                });
        }

        // Trigger systemic routines
        window.onload = () => {
            runTelemetryDiagnostics();
            loadDiscoverFeed();
            setInterval(runTelemetryDiagnostics, 4000); // Poll tracking arrays every 4000ms
        };
    </script>
</body>
</html>
"""

# =========================================================================
# WEB FRONTEND INTERFACE CHANNELS
# =========================================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/web/node_status')
def get_node_status():
    if not active_nodes:
        return jsonify({"connected": False})
    last_node = list(active_nodes.values())[-1]
    elapsed = int(time.time() - last_node)
    return jsonify({"connected": elapsed < 15, "last_seen": elapsed})

@app.route('/api/web/search')
def web_search():
    query = request.args.get('q', 'trending')
    task_id = str(uuid.uuid4())
    tasks_queue.append({'task_id': task_id, 'type': 'search', 'query': query})
    
    start = time.time()
    while time.time() - start < 12:
        if task_id in tasks_results:
            return jsonify(tasks_results.pop(task_id))
        time.sleep(0.2)
    return jsonify({"videos": []})

@app.route('/api/web/extract')
def web_extract():
    video_id = request.args.get('video_id')
    session_id = f"sess_{str(uuid.uuid4())[:12]}"
    task_id = str(uuid.uuid4())
    
    video_buffers[session_id] = []
    tasks_queue.append({
        'task_id': task_id, 
        'type': 'extract', 
        'video_id': video_id, 
        'session_id': session_id
    })
    
    start = time.time()
    while time.time() - start < 10:
        if task_id in tasks_results:
            tasks_results.pop(task_id)
            return jsonify({"session_id": session_id})
        time.sleep(0.2)
    return jsonify({"error": "Node timeout"}), 504

@app.route('/api/stream')
def stream_video():
    session_id = request.args.get('session_id')
    
    def generate():
        while True:
            if session_id in video_buffers and len(video_buffers[session_id]) > 0:
                chunk = video_buffers[session_id].pop(0)
                if chunk == b"":
                    break
                yield chunk
            else:
                time.sleep(0.1)
                if session_id not in video_buffers:
                    break
                    
    return Response(generate(), mimetype='video/mp4')

# =========================================================================
# BACKEND COMMUNICATIONS PORTAL FOR HOME PROXY NODE
# =========================================================================
@app.route('/api/node/tasks')
def node_get_tasks():
    node_ip = request.remote_addr or "Home_Node"
    active_nodes[node_ip] = time.time()
    
    global tasks_queue
    current_tasks = tasks_queue[:]
    tasks_queue = []
    return jsonify(current_tasks)

@app.route('/api/node/submit', methods=['POST'])
def node_submit_task():
    data = request.json
    tasks_results[data['task_id']] = data['result']
    return jsonify({"status": "acknowledged"})

@app.route('/api/node/upload_chunk', methods=['POST'])
def node_upload_chunk():
    session_id = request.args.get('session_id')
    chunk_data = request.data
    if session_id in video_buffers:
        video_buffers[session_id].append(chunk_data)
    return jsonify({"status": "pushed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
