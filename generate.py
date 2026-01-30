#!/usr/bin/env python3
"""
Agent Health Monitor Dashboard
Generates a real-time overview of all OpenClaw sub-agents
"""

import subprocess
import json
import os
from datetime import datetime

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def get_sessions():
    """Get all sessions from OpenClaw"""
    output = run_command("openclaw sessions list --active-minutes 360 --limit 20 --json")
    try:
        data = json.loads(output)
        return data.get("sessions", [])
    except:
        return []

def format_duration(ms):
    """Format milliseconds to human readable"""
    if not ms:
        return "N/A"
    minutes = ms // 60000
    hours = minutes // 60
    if hours > 0:
        return f"{hours}h {minutes % 60}m"
    return f"{minutes}m"

def format_tokens(tokens):
    """Format token count"""
    if not tokens:
        return "0"
    if tokens >= 1000:
        return f"{tokens/1000:.1f}k"
    return str(tokens)

def get_status(session):
    """Determine agent status"""
    tokens = session.get("totalTokens", 0)
    updated = session.get("updatedAt", 0)
    now = int(datetime.now().timestamp() * 1000)
    idle_time = (now - updated) / 1000 / 60  # minutes
    
    if tokens == 0 and idle_time > 5:
        return "stuck", "⚠️", "#f85149"
    elif idle_time < 2:
        return "active", "🟢", "#3fb950"
    elif tokens > 0:
        return "completed", "✅", "#58a6ff"
    else:
        return "idle", "⚪", "#8b949e"

def generate_dashboard(sessions):
    """Generate HTML dashboard"""
    
    # Categorize sessions
    active = []
    completed = []
    stuck = []
    
    for s in sessions:
        status, icon, color = get_status(s)
        s["_status"] = status
        s["_icon"] = icon
        s["_color"] = color
        
        if status == "active":
            active.append(s)
        elif status == "completed":
            completed.append(s)
        elif status == "stuck":
            stuck.append(s)
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥷 Agent Health Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border-bottom: 1px solid #30363d;
            padding: 40px 20px;
            text-align: center;
        }
        header h1 { 
            font-size: 2.5rem; 
            background: linear-gradient(135deg, #58a6ff, #a371f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        header p { color: #8b949e; font-size: 1.1rem; }
        .timestamp {
            text-align: center;
            padding: 15px;
            color: #8b949e;
            font-size: 0.9rem;
            border-bottom: 1px solid #21262d;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 0;
        }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-4px); }
        .stat-card h3 {
            font-size: 2.5rem;
            margin-bottom: 8px;
        }
        .stat-card p { color: #8b949e; }
        .stat-card.active { border-color: #3fb950; }
        .stat-card.active h3 { color: #3fb950; }
        .stat-card.completed { border-color: #58a6ff; }
        .stat-card.completed h3 { color: #58a6ff; }
        .stat-card.stuck { border-color: #f85149; }
        .stat-card.stuck h3 { color: #f85149; }
        
        .section {
            margin: 40px 0;
        }
        .section h2 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #30363d;
        }
        .section.active h2 { color: #3fb950; border-color: #3fb950; }
        .section.completed h2 { color: #58a6ff; border-color: #58a6ff; }
        .section.stuck h2 { color: #f85149; border-color: #f85149; }
        
        .agent-grid {
            display: grid;
            gap: 15px;
        }
        .agent-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            display: grid;
            grid-template-columns: auto 1fr auto auto;
            align-items: center;
            gap: 20px;
        }
        .agent-card:hover {
            border-color: #58a6ff;
            background: #1c2128;
        }
        .agent-icon {
            font-size: 1.5rem;
            width: 40px;
            text-align: center;
        }
        .agent-info h3 {
            color: #c9d1d9;
            font-size: 1rem;
            margin-bottom: 4px;
        }
        .agent-info p {
            color: #8b949e;
            font-size: 0.85rem;
        }
        .agent-stats {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
        }
        .agent-stat {
            text-align: center;
        }
        .agent-stat .value {
            color: #58a6ff;
            font-weight: 600;
            display: block;
        }
        .agent-stat .label {
            color: #6e7681;
            font-size: 0.75rem;
        }
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-badge.active {
            background: rgba(63, 185, 80, 0.2);
            color: #3fb950;
        }
        .status-badge.completed {
            background: rgba(88, 166, 255, 0.2);
            color: #58a6ff;
        }
        .status-badge.stuck {
            background: rgba(248, 81, 73, 0.2);
            color: #f85149;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #8b949e;
        }
        footer {
            text-align: center;
            padding: 40px;
            border-top: 1px solid #21262d;
            color: #6e7681;
            font-size: 0.85rem;
        }
        @media (max-width: 768px) {
            .agent-card {
                grid-template-columns: 1fr;
                text-align: center;
            }
            .agent-stats {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>🥷 Agent Health Monitor</h1>
        <p>Real-time overview of all OpenClaw sub-agents</p>
    </header>
    
    <div class="timestamp">
        Last updated: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ''' (refreshes every 30s)
    </div>
    
    <main class="container">
        <div class="stats-grid">
            <div class="stat-card active">
                <h3>''' + str(len(active)) + '''</h3>
                <p>🟢 Active Agents</p>
            </div>
            <div class="stat-card completed">
                <h3>''' + str(len(completed)) + '''</h3>
                <p>✅ Completed</p>
            </div>
            <div class="stat-card stuck">
                <h3>''' + str(len(stuck)) + '''</h3>
                <p>⚠️ Stuck/Idle</p>
            </div>
            <div class="stat-card">
                <h3>''' + str(len(sessions)) + '''</h3>
                <p>📊 Total Tracked</p>
            </div>
        </div>
'''
    
    # Active Agents Section
    if active:
        html += '''
        <div class="section active">
            <h2>🟢 Active Agents</h2>
            <div class="agent-grid">
'''
        for s in active:
            html += render_agent_card(s)
        html += '''
            </div>
        </div>
'''
    
    # Completed Agents Section
    if completed:
        html += '''
        <div class="section completed">
            <h2>✅ Completed Agents</h2>
            <div class="agent-grid">
'''
        for s in completed[:10]:  # Show last 10
            html += render_agent_card(s)
        if len(completed) > 10:
            html += f'<p style="text-align: center; color: #6e7681; padding: 20px;">... and {len(completed) - 10} more</p>'
        html += '''
            </div>
        </div>
'''
    
    # Stuck Agents Section
    if stuck:
        html += '''
        <div class="section stuck">
            <h2>⚠️ Stuck/Need Attention</h2>
            <div class="agent-grid">
'''
        for s in stuck:
            html += render_agent_card(s)
        html += '''
            </div>
        </div>
'''
    
    if not sessions:
        html += '''
        <div class="empty-state">
            <h2>No agents found</h2>
            <p>Run some sub-agents to see them here</p>
        </div>
'''
    
    html += '''
    </main>
    
    <footer>
        <p>Built by Finn 🥷 | Auto-refreshes every 30 seconds</p>
    </footer>
</body>
</html>
'''
    
    return html

def render_agent_card(session):
    """Render a single agent card"""
    label = session.get("label", "unnamed")
    kind = session.get("kind", "unknown")
    tokens = session.get("totalTokens", 0)
    model = session.get("model", "unknown")
    updated = session.get("updatedAt", 0)
    
    status = session.get("_status", "unknown")
    icon = session.get("_icon", "⚪")
    
    # Calculate idle time
    now = int(datetime.now().timestamp() * 1000)
    idle_minutes = int((now - updated) / 1000 / 60)
    
    return f'''
                <div class="agent-card">
                    <div class="agent-icon">{icon}</div>
                    <div class="agent-info">
                        <h3>{label}</h3>
                        <p>{kind} • {model} • Idle: {idle_minutes}m</p>
                    </div>
                    <div class="agent-stats">
                        <div class="agent-stat">
                            <span class="value">{format_tokens(tokens)}</span>
                            <span class="label">tokens</span>
                        </div>
                    </div>
                    <span class="status-badge {status}">{status}</span>
                </div>
'''

def main():
    print("🔍 Fetching agent sessions...")
    sessions = get_sessions()
    print(f"📊 Found {len(sessions)} sessions")
    
    print("🎨 Generating dashboard...")
    html = generate_dashboard(sessions)
    
    output_path = "/Users/patrickaltmann/clawd-second/agent-monitor/index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated: {output_path}")
    print(f"📈 Stats: {len(sessions)} agents tracked")

if __name__ == "__main__":
    main()
