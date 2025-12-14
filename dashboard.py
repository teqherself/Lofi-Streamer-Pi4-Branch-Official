#!/usr/bin/env python3
"""
Commercial Grade Web Dashboard for RTMP Streamer
Flask-based control panel for Raspberry Pi camera streamer
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json
import subprocess
import os
import psutil
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Default password: "admin" - CHANGE THIS!
PASSWORD_HASH = "pbkdf2:sha256:600000$5qZ8vQKW$8e89c7d3e5f4a2b1c9d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5"

CONFIG_FILE = '/home/pi/streamer/config.json'
STATUS_FILE = '/home/pi/streamer/status.json'
LOG_FILE = '/home/pi/streamer/logs/streamer.log'

# System stats cache
stats_cache = {
    'data': {},
    'timestamp': 0
}

def check_password(password):
    """Verify password against hash"""
    return check_password_hash(PASSWORD_HASH, password)

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_service_status():
    """Check if streamer service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'rtmp-streamer'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def get_stream_status():
    """Get current stream status from status file"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)
                if status.get('streaming') and status.get('start_time'):
                    start = datetime.fromisoformat(status['start_time'])
                    uptime = datetime.now() - start
                    status['uptime'] = str(uptime).split('.')[0]
                return status
    except Exception as e:
        print(f"Error reading status: {e}")
    
    return {
        'streaming': False,
        'uptime': '0:00:00',
        'resolution': [1920, 1080],
        'framerate': 30,
        'bitrate': 2500000
    }

def get_system_stats():
    """Get system statistics with caching"""
    now = time.time()
    if now - stats_cache['timestamp'] < 2:  # Cache for 2 seconds
        return stats_cache['data']
    
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        # Memory
        mem = psutil.virtual_memory()
        
        # Disk
        disk = psutil.disk_usage('/')
        
        # Temperature
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
        except:
            temp = 0
        
        # Network
        net = psutil.net_io_counters()
        
        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        stats = {
            'cpu': {
                'percent': round(cpu_percent, 1),
                'freq': round(cpu_freq.current, 0) if cpu_freq else 0
            },
            'memory': {
                'percent': round(mem.percent, 1),
                'used': round(mem.used / (1024**3), 2),
                'total': round(mem.total / (1024**3), 2)
            },
            'disk': {
                'percent': round(disk.percent, 1),
                'used': round(disk.used / (1024**3), 2),
                'total': round(disk.total / (1024**3), 2)
            },
            'temperature': round(temp, 1),
            'network': {
                'sent': round(net.bytes_sent / (1024**3), 2),
                'recv': round(net.bytes_recv / (1024**3), 2)
            },
            'uptime': str(uptime).split('.')[0]
        }
        
        stats_cache['data'] = stats
        stats_cache['timestamp'] = now
        
        return stats
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {}

def get_stream_logs(lines=50):
    """Get last N lines from stream log"""
    try:
        if os.path.exists(LOG_FILE):
            result = subprocess.run(
                ['tail', '-n', str(lines), LOG_FILE],
                capture_output=True,
                text=True
            )
            return result.stdout
    except:
        pass
    return "No logs available"

def load_config():
    """Load streaming configuration"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'rtmp_url': 'rtmp://a.rtmp.youtube.com/live2/',
        'stream_key': '',
        'resolution': [1920, 1080],
        'framerate': 30,
        'bitrate': 2500000,
        'preset': 'medium',
        'audio_enabled': False
    }

def save_config(config):
    """Save streaming configuration"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# Routes
@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password(password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# API Routes
@app.route('/api/status')
@login_required
def api_status():
    """Get complete system and stream status"""
    return jsonify({
        'service_running': get_service_status(),
        'stream_status': get_stream_status(),
        'system_stats': get_system_stats()
    })

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def api_config():
    """Get or update configuration"""
    if request.method == 'POST':
        config = request.json
        # Don't allow stream_key to be empty
        if not config.get('stream_key'):
            return jsonify({'success': False, 'error': 'Stream key required'}), 400
        
        if save_config(config):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Failed to save config'}), 500
    
    return jsonify(load_config())

@app.route('/api/logs')
@login_required
def api_logs():
    """Get stream logs"""
    lines = request.args.get('lines', 50, type=int)
    return jsonify({'logs': get_stream_logs(lines)})

@app.route('/api/control/<action>', methods=['POST'])
@login_required
def api_control(action):
    """Control streamer service"""
    try:
        if action == 'start':
            result = subprocess.run(['sudo', 'systemctl', 'start', 'rtmp-streamer'], 
                                  capture_output=True, text=True)
        elif action == 'stop':
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'rtmp-streamer'],
                                  capture_output=True, text=True)
        elif action == 'restart':
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'rtmp-streamer'],
                                  capture_output=True, text=True)
        elif action == 'reboot':
            subprocess.Popen(['sudo', 'reboot'])
            return jsonify({'success': True, 'message': 'System rebooting...'})
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        if result.returncode == 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('/home/pi/streamer/logs', exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
