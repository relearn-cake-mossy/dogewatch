import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

PROXY_NODE_URL = "http://botdic.nethr.nl:10416"

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOGEWATCH v0.0.5 - Cyber Premium</title>
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #070913 0%, #0c0f24 100%);
            --panel-bg: rgba(22, 27, 49, 0.65);
            --panel-border: rgba(255, 255, 255, 0.08);
            --accent-gold: #ffb627;
            --accent-neon: #00f2fe;
            --text-main: #f1f5f9;
            --text-muted: #64748b;
            --glass-blur: blur(16px);
        }

        body {
            background: var(--bg-gradient);
            color: var(--text-main);
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        .sidebar {
            width: 280px;
            background: var(--panel-bg);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            padding: 25px;
            border-right: 1px solid var(--panel-border);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            z-index: 10;
        }

        .brand-zone {
            margin-bottom: 30px;
        }

        .brand {
            font-size: 26px;
            font-weight: 900;
            background: linear-gradient(45deg, var(--accent-gold), #fff3b0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .version {
            font-size: 11px;
            color: #00f2fe;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 2px;
        }

        .status-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--panel-border);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 25px;
            font-size: 13px;
        }

        .pulse-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #ef4444;
            border-radius: 50%;
            margin-right: 6px;
        }

        .pulse-online {
            background-color: #10b981;
            box-shadow: 0 0 10px #10b981;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.7; }
            50% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.7; }
        }

        .menu-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .menu-item {
            padding: 14px 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            color: #94a3b8;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .menu-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
        }

        .menu-item.active {
            background: linear-gradient(90deg, rgba(255,182,39,0.15) 0%, rgba(255,182,39,0) 100%);
            border-left: 4px solid var(--accent-gold);
            color: #fff;
            padding-left: 14px;
        }

        .main-container {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        .header-section {
            margin-bottom: 30px;
        }

        .header-section h2 {
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 800;
        }

        .search-wrapper {
            display: flex;
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            padding: 6px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            max-width: 700px;
            margin-bottom: 20px;
        }

        .search-wrapper input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 12px 16px;
            color: white;
            font-size: 16px;
            outline: none;
        }

        .search-wrapper button {
            background: linear-gradient(135deg, var(--accent-gold) 0%, #e09f1f 100%);
            color: #05070f;
            border: none;
            border-radius: 8px;
            padding: 0 26px;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .search-wrapper button:hover {
            opacity: 0.9;
        }

        .query-log {
            font-size: 13px;
            color: var(--text-muted);
        }
        .query-log span { color: var(--accent-gold); font-weight: bold; }

        .grid-view {
            display: grid;
            gap: 25px;
            margin-top: 15px;
        }

        .grid-videos {
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        }

        .card-video {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 14px;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }

        .card-video:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 182, 39, 0.3);
            box-shadow: 0 10px 25px rgba(255, 182, 39, 0.1);
        }

        .thumb-wrap {
            position: relative;
            width: 100%;
            padding-top: 56.25%;
            background: #000;
        }

        .thumb-img {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover;
        }

        .card-body { padding: 18px; }
        .card-title {
            font-size: 15px;
            font-weight: 600;
            margin: 0 0 10px 0;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .grid-shorts {
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        }

        .card-short {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            overflow: hidden;
            position: relative;
            aspect-ratio: 9 / 16;
            transition: all 0.3s ease;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }

        .card-short:hover {
            transform: scale(1.03);
            border-color: #ff4757;
            box-shadow: 0 12px 30px rgba(255, 71, 87, 0.25);
        }

        .card-short .thumb-wrap {
            padding-top: 100%;
            height: 100%;
            position: absolute;
        }

        .short-overlay {
            position: absolute;
            bottom: 0; left: 0; right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.4) 60%, transparent 100%);
            padding: 15px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            height: 50%;
        }

        .short-title {
            font-size: 13px;
            font-weight: 600;
            margin: 0;
            line-height: 1.4;
            color: #fff;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-shadow: 0 2px 4px rgba(0,0,0,0.6);
        }

        .badge-short {
            position: absolute;
            top: 12px; left: 12px;
            background: #ff4757;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            box-shadow: 0 2px 8px rgba(255,71,87,0.4);
        }

        .grid-channels {
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        }

        .card-channel {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            backdrop-filter: var(--glass-blur);
            transition: all 0.3s ease;
        }

        .card-channel:hover {
            border-color: var(--accent-neon);
            box-shadow: 0 8px 25px rgba(0, 242, 254, 0.15);
            transform: translateY(-4px);
        }

        .channel-avatar {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: linear-gradient(45deg, var(--accent-gold), var(--accent-neon));
            margin: 0 auto 15px auto;
            padding: 3px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }

        .channel-avatar img {
            width: 100%; height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background: #161925;
        }

        .channel-name {
            font-size: 16px;
            font-weight: 700;
            margin: 0 0 6px 0;
            color: #fff;
        }

        .channel-meta {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 15px;
        }

        .btn-visit {
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--panel-border);
            color: #fff;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-visit:hover {
            background: var(--text-main);
            color: #000;
        }

        .status-info {
            padding: 30px;
            background: rgba(255,255,255,0.02);
            border: 1px dashed var(--panel-border);
            border-radius: 12px;
            text-align: center;
            color: var(--text-muted);
            margin-top: 20px;
        }

        .loader {
            display: none;
            text-align: center;
            padding: 40px;
            color: var(--accent-gold);
            font-weight: bold;
        }

        .player-modal {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(3, 5, 12, 0.85);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .player-modal.active {
            opacity: 1;
        }
        .modal-box {
            background: rgba(18, 22, 41, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 24px;
            width: 90%;
            max-width: 960px;
            box-shadow: 0 25px 60px rgba(0,0,0,0.7);
            overflow: hidden;
            position: relative;
            transform: scale(0.9);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .player-modal.active .modal-box {
            transform: scale(1);
        }
        .iframe-container {
            position: relative;
            width: 100%;
            padding-top: 56.25%;
            background: #000;
        }
        .iframe-container iframe {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            border: none;
        }
        .modal-ctrl {
            padding: 15px 24px;
            background: rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--panel-border);
        }
        .modal-video-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--accent-gold);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 75%;
        }
        .btn-close-player {
            background: #ff4757;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 30px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(255,71,87,0.3);
            transition: 0.2s;
        }
        .btn-close-player:hover {
            background: #ff6b81;
            transform: translateY(-1px);
        }
        .modal-box.shorts-mode {
            max-width: 420px;
        }
        .modal-box.shorts-mode .iframe-container {
            padding-top: 177.77%;
        }
    </style>
</head>
<body>

    <div class="sidebar">
        <div>
            <div class="brand-zone">
                <div class="brand">⚡ DOGEWATCH</div>
                <div class="version">Cluster v0.0.5</div>
            </div>
            
            <div class="status-card">
                <div style="font-weight:bold; color:#94a3b8; margin-bottom:4px;">UPLINK STATUS</div>
                <div style="display:flex; align-items:center;">
                    <span id="node-pulse" class="pulse-dot"></span>
                    <span id="node-text">Checking Node...</span>
                </div>
            </div>

            <div class="menu-list">
                <div class="menu-item" onclick="switchTab('trending', this)">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M8 16c3.314 0 6-2 6-5.5 0-1.5-.5-4-2.5-6 .5 1.5-1 4-2.5 4.5-1 1-1.5 1-2 2-.5.5-.5 1.5-.5 2 0 2 1.5 3 1.5 3zM3.6 10.5c0-2.984 1.416-4.945 2.304-6.079l.011-.014.01-.013c.12-.152.341-.115.41.072l.003.009.002.005.004.015.011.042c.11.41.222.846.336 1.28l.002.008.003.012c.074.288.15.578.232.864.073.256.376.326.546.136.634-.711 1.223-1.677 1.644-2.733.053-.133.242-.119.276.022a16.2 16.2 0 0 1 .18 2.06c.03.627.014 1.402-.178 2.152-.163.639-.462 1.224-.913 1.688-.8.824-1.743 1.255-2.744 1.255-2.115 0-3.731-1.696-3.731-3.805z"/></svg>
                    Trending Home
                </div>
                <div class="menu-item" onclick="switchTab('video', this)">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M0 12V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm6.79-6.907A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814l-3.5-2.5z"/></svg>
                    Search Station
                </div>
                <div class="menu-item" onclick="switchTab('shorts', this)">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M3 5c0-1.103.897-2 2-2h6c1.103 0 2 .897 2 2v6c0 1.103-.897 2-2 2H5c-1.103 0-2-.897-2-2V5zm7 3-3-2v4l3-2z"/></svg>
                    Shorts Station
                </div>
                <div class="menu-item" onclick="switchTab('channel', this)">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2 1H6a4 4 0 0 0-4 4v1h12v-1a4 4 0 0 0-4-4z"/></svg>
                    Channel Hub
                </div>
            </div>
        </div>
        <div style="font-size: 11px; color: var(--text-muted)">Premium Glossy Render Architecture</div>
    </div>

    <div class="main-container">
        <div class="header-section">
            <h2 id="station-title">Trending Home</h2>
            <div class="search-wrapper">
                <input type="text" id="search-core" placeholder="Enter keywords to search...">
                <button onclick="performSearch()">DISCOVER</button>
            </div>
            <div class="query-log" id="query-log" style="display:none;">
                Network Query Index: <span id="log-query">""</span>
            </div>
        </div>

        <div id="loading-spinner" class="loader">🪐 Transmitting uplink signals. Processing data via Home Node Proxy...</div>
        <div id="empty-state" class="status-info">System is ready. Enter keywords and press Discover.</div>

        <div id="results-grid" class="grid-view grid-videos"></div>
    </div>

    <div id="cyber-player-modal" class="player-modal">
        <div id="player-box-layout" class="modal-box">
            <div class="iframe-container">
                <iframe id="native-core-player" src="" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
            </div>
            <div class="modal-ctrl">
                <div id="player-title-display" class="modal-video-title">Connecting signal...</div>
                <button class="btn-close-player" onclick="closeCyberPlayer()">CLOSE PLAYER</button>
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'trending';

        document.addEventListener("DOMContentLoaded", () => {
            const defaultActive = document.querySelector('.menu-item');
            if (defaultActive) {
                defaultActive.classList.add('active');
                switchTab('trending', defaultActive);
            }
        });

        function switchTab(tabType, element) {
            currentTab = tabType;
            document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
            element.classList.add('active');

            const titleEl = document.getElementById('station-title');
            const gridEl = document.getElementById('results-grid');
            gridEl.innerHTML = '';
            document.getElementById('empty-state').style.display = 'block';

            if(tabType === 'trending') {
                titleEl.innerText = "Trending Home";
                gridEl.className = "grid-view grid-videos";
                performSearch();
            } else if(tabType === 'video') {
                titleEl.innerText = "Search Station";
                gridEl.className = "grid-view grid-videos";
            } else if (tabType === 'shorts') {
                titleEl.innerText = "Shorts Station";
                gridEl.className = "grid-view grid-shorts";
            } else if (tabType === 'channel') {
                titleEl.innerText = "Channel Hub";
                gridEl.className = "grid-view grid-channels";
            }
        }

        async function checkNodeHeartbeat() {
            const pulse = document.getElementById('node-pulse');
            const text = document.getElementById('node-text');
            try {
                const res = await fetch('/api/web/status');
                const data = await res.json();
                if (data.online) {
                    pulse.className = "pulse-dot pulse-online";
                    text.innerText = "Uplink Active (0s back)";
                    text.style.color = "#10b981";
                } else {
                    pulse.className = "pulse-dot";
                    text.innerText = "Uplink Offline";
                    text.style.color = "#ef4444";
                }
            } catch {
                pulse.className = "pulse-dot";
                text.innerText = "Heartbeat Error";
                text.style.color = "#ef4444";
            }
        }

        async function performSearch() {
            let queryInput = document.getElementById('search-core').value.trim();
            
            if (!queryInput && currentTab === 'trending') {
                queryInput = "trending";
            }

            if (!queryInput) return;

            document.getElementById('query-log').style.display = 'block';
            document.getElementById('log-query').innerText = `"${queryInput}" [Type: ${currentTab.toUpperCase()}]`;
            document.getElementById('loading-spinner').style.display = 'block';
            document.getElementById('empty-state').style.display = 'none';
            
            const gridEl = document.getElementById('results-grid');
            gridEl.innerHTML = '';

            try {
                const response = await fetch(`/api/web/search?query=${encodeURIComponent(queryInput)}&type=${currentTab}`);
                const data = await response.json();
                
                document.getElementById('loading-spinner').style.display = 'none';

                if (data.videos && data.videos.length > 0) {
                    data.videos.forEach(item => {
                        if (currentTab === 'trending' || currentTab === 'video') {
                            renderVideoCard(item, gridEl);
                        } else if (currentTab === 'shorts') {
                            renderShortsCard(item, gridEl);
                        } else if (currentTab === 'channel') {
                            renderChannelCard(item, gridEl);
                        }
                    });
                } else {
                    showErrorState("No responsive node segments or data matched parameters.");
                }
            } catch (err) {
                document.getElementById('loading-spinner').style.display = 'none';
                showErrorState("Fatal Error: Uplink cross-stream transmission failed.");
            }
        }

        function launchCyberPlayer(videoId, videoTitle, mode) {
            const modal = document.getElementById('cyber-player-modal');
            const box = document.getElementById('player-box-layout');
            const iframe = document.getElementById('native-core-player');
            const titleDisplay = document.getElementById('player-title-display');

            titleDisplay.innerText = videoTitle;
            
            if (mode === 'shorts') {
                box.classList.add('shorts-mode');
                iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&modestbranding=1&rel=0&showinfo=0`;
            } else {
                box.classList.remove('shorts-mode');
                iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&modestbranding=1&rel=0&showinfo=0`;
            }

            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('active'), 20);
        }

        function closeCyberPlayer() {
            const modal = document.getElementById('cyber-player-modal');
            const iframe = document.getElementById('native-core-player');
            
            modal.classList.remove('active');
            setTimeout(() => {
                modal.style.display = 'none';
                iframe.src = ''; 
            }, 300);
        }

        window.onclick = function(event) {
            const modal = document.getElementById('cyber-player-modal');
            if (event.target === modal) {
                closeCyberPlayer();
            }
        }

        function renderVideoCard(video, grid) {
            const card = document.createElement('div');
            card.className = 'card-video';
            const safeTitle = video.title.replace(/'/g, "\\'");
            card.innerHTML = `
                <div class="thumb-wrap">
                    <img class="thumb-img" src="${video.thumbnail}" alt="thumb">
                </div>
                <div class="card-body">
                    <h4 class="card-title">${video.title}</h4>
                    <div style="font-size:12px; color:var(--text-muted); margin-bottom: 12px;">Video ID: ${video.id}</div>
                    <button onclick="launchCyberPlayer('${video.id}', '${safeTitle}', 'video')" class="btn-visit" style="width: 100%;">Watch Stream</button>
                </div>
            `;
            grid.appendChild(card);
        }

        function renderShortsCard(short, grid) {
            const card = document.createElement('div');
            card.className = 'card-short';
            const safeTitle = short.title.replace(/'/g, "\\'");
            card.innerHTML = `
                <span class="badge-short">Shorts</span>
                <div class="thumb-wrap">
                    <img class="thumb-img" src="${short.thumbnail}" alt="short-thumb">
                </div>
                <div class="short-overlay">
                    <p class="short-title">${short.title}</p>
                    <button onclick="launchCyberPlayer('${short.id}', '${safeTitle}', 'shorts')" class="btn-visit" style="margin-top:8px; width:100%;">Open Short</button>
                </div>
            `;
            grid.appendChild(card);
        }

        function renderChannelCard(channel, grid) {
            const card = document.createElement('div');
            card.className = 'card-channel';
            const safeTitle = channel.title.replace(/'/g, "\\'");
            card.innerHTML = `
                <div class="channel-avatar">
                    <img src="${channel.thumbnail || 'https://www.gstatic.com/youtube/img/originals/channels/youtube_profile_avatar_96x96.png'}" alt="avatar">
                </div>
                <div class="channel-name">${channel.title}</div>
                <div class="channel-meta">ID: ${channel.id}</div>
                <button onclick="launchCyberPlayer('${channel.id}', '${safeTitle}', 'video')" class="btn-visit" style="width: 100%;">View Channel</button>
            `;
            grid.appendChild(card);
        }

        function showErrorState(msg) {
            const emptyState = document.getElementById('empty-state');
            emptyState.style.display = 'block';
            emptyState.innerText = msg;
            emptyState.style.color = "#ef4444";
        }

        checkNodeHeartbeat();
        setInterval(checkNodeHeartbeat, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/api/web/status', methods=['GET'])
def web_status():
    try:
        r = requests.get(f"{PROXY_NODE_URL}/", timeout=50)
        if r.status_code == 200:
            return jsonify({"online": True})
        return jsonify({"online": False})
    except:
        return jsonify({"online": False})

@app.route('/api/web/search', methods=['GET'])
def web_search():
    query = request.args.get('query', '')
    search_type = request.args.get('type', 'video')
    
    if not query:
        if search_type == 'trending':
            query = 'trending'
        else:
            return jsonify({"videos": []})
    
    refined_query = query
    if search_type == 'shorts':
        refined_query = f"{query} shorts"
    elif search_type == 'channel':
        refined_query = f"{query} channel"
        
    try:
        response = requests.get(f"{PROXY_NODE_URL}/scrape", params={"query": refined_query}, timeout=25)
        return jsonify(response.json())
    except:
        return jsonify({"error": "Proxy offline", "videos": []}), 504

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
