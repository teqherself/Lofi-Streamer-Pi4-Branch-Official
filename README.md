# 📹 RTMP Camera Streamer for Raspberry Pi 4

A professional-grade camera streaming solution for Raspberry Pi 4/5 with a beautiful web dashboard. Stream to YouTube, Twitch, or any RTMP service using your Raspberry Pi camera.

![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204%2F5-red?style=for-the-badge&logo=raspberrypi)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## ✨ Features

### 🎥 Streaming
- **RTMP Support**: Stream to YouTube, Twitch, Restream, or any RTMP service
- **H.264 Encoding**: Hardware-accelerated video encoding
- **Configurable Quality**: Adjust resolution, bitrate, and framerate
- **Auto-Reconnect**: Automatic reconnection on stream failure
- **Multiple Resolutions**: Support for HD, Full HD, 2K, and 4K streaming

### 🖥️ Dashboard
- **Real-Time Monitoring**: Live CPU, memory, temperature, and disk usage
- **Stream Controls**: Start, stop, and restart streams with one click
- **Configuration UI**: Easy-to-use settings interface
- **Live Logs**: View streaming logs in real-time
- **System Stats**: Monitor network usage and system uptime
- **Secure Login**: Password-protected access

### 🔧 Technical Features
- **picamera2 Integration**: Modern camera interface for Raspberry Pi
- **FFmpeg Pipeline**: Professional-grade video encoding
- **systemd Services**: Reliable service management
- **Flask Dashboard**: Responsive web interface
- **JSON Configuration**: Easy configuration management

## 📋 Requirements

### Hardware
- Raspberry Pi 4 (4GB or 8GB recommended) or Raspberry Pi 5
- Raspberry Pi Camera Module (v2, v3, or HQ Camera)
- MicroSD card (16GB minimum, 32GB recommended)
- Stable internet connection (5+ Mbps upload for 1080p)
- Power supply (official 3A adapter recommended)

### Software
- Raspberry Pi OS (64-bit recommended)
- Python 3.9+
- picamera2
- FFmpeg

## 🚀 Quick Installation

Run this one-line installer on your Raspberry Pi:

```bash
bash <(curl -s https://raw.githubusercontent.com/YOUR_USERNAME/rtmp-streamer/main/install.sh)
```

Or manual installation:

```bash
git clone https://github.com/YOUR_USERNAME/rtmp-streamer.git
cd rtmp-streamer
chmod +x install.sh
./install.sh
```

The installer will:
1. Check Pi compatibility
2. Install system dependencies (Python, picamera2, FFmpeg)
3. Install Python packages (Flask, psutil)
4. Create directory structure
5. Set up systemd services
6. Configure sudo permissions
7. Start the dashboard

## 🎮 Usage

### First Time Setup

1. **Access the Dashboard**
   ```
   http://<your-pi-ip>:5000
   ```
   Find your Pi's IP: `hostname -I`

2. **Login**
   - Default password: `admin`
   - Change it immediately after first login!

3. **Configure Stream Settings**
   - Click "⚙️ Settings"
   - Enter your RTMP URL (e.g., `rtmp://a.rtmp.youtube.com/live2/`)
   - Enter your stream key from YouTube/Twitch
   - Select resolution (1920x1080 recommended for Pi 4)
   - Choose framerate (30 fps recommended)
   - Set bitrate (2500-4000 kbps for 1080p)
   - Click "💾 Save Settings"

4. **Start Streaming**
   - Click "▶️ Start Stream"
   - Monitor the stream status and system stats
   - Check logs if any issues occur

### RTMP URLs for Popular Services

**YouTube Live:**
```
rtmp://a.rtmp.youtube.com/live2/
```

**Twitch:**
```
rtmp://live.twitch.tv/app/
```

**Restream.io:**
```
rtmp://live.restream.io/live/
```

**Facebook Live:**
```
rtmps://live-api-s.facebook.com:443/rtmp/
```

## 📁 File Structure

```
/home/pi/streamer/
├── streamer.py          # Main streaming service
├── dashboard.py         # Web dashboard
├── config.json          # Stream configuration
├── status.json          # Current stream status
├── templates/
│   ├── dashboard.html   # Main dashboard UI
│   └── login.html       # Login page
└── logs/
    └── streamer.log     # Stream logs
```

## ⚙️ Configuration

### Stream Settings (config.json)

```json
{
  "rtmp_url": "rtmp://a.rtmp.youtube.com/live2/",
  "stream_key": "YOUR_STREAM_KEY",
  "resolution": [1920, 1080],
  "framerate": 30,
  "bitrate": 2500000,
  "gop_size": 60,
  "preset": "medium",
  "audio_enabled": false
}
```

### Resolution Options
- **1280x720** (HD) - 1500-2500 kbps
- **1920x1080** (Full HD) - 2500-4000 kbps
- **2560x1440** (2K) - 4000-6000 kbps
- **3840x2160** (4K) - 8000-15000 kbps (Pi 5 only)

### Encoding Presets
- **ultrafast** - Lowest quality, fastest encoding
- **veryfast** - Low quality, very fast
- **fast** - Moderate quality, fast
- **medium** - Good quality, balanced (recommended)
- **slow** - High quality, slow (may drop frames on Pi 4)

## 🔐 Security

### Change Default Password

Generate a new password hash:

```bash
python3 << EOF
from werkzeug.security import generate_password_hash
print(generate_password_hash("YOUR_NEW_PASSWORD"))
EOF
```

Edit `/home/pi/streamer/dashboard.py`:

```python
PASSWORD_HASH = "pbkdf2:sha256:YOUR_HASH_HERE"
```

Restart dashboard:
```bash
sudo systemctl restart rtmp-dashboard
```

### Firewall (Optional)

```bash
sudo apt-get install ufw
sudo ufw allow 5000/tcp
sudo ufw enable
```

## 🛠️ Troubleshooting

### Stream Won't Start

1. **Check camera connection:**
   ```bash
   libcamera-hello
   ```

2. **Verify stream key:**
   - Make sure you've entered the correct stream key
   - Check that YouTube/Twitch streaming is enabled

3. **Check logs:**
   ```bash
   journalctl -u rtmp-streamer -n 50
   ```

### Low Frame Rate / Dropped Frames

1. **Reduce resolution**: Try 1280x720 instead of 1920x1080
2. **Lower bitrate**: Reduce to 2000 kbps
3. **Change preset**: Use "faster" or "veryfast"
4. **Check temperature**: Monitor CPU temperature (should be < 70°C)

### Camera Not Detected

```bash
# Check camera is enabled
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable

# Reboot
sudo reboot
```

### High CPU Usage

- Lower encoding preset (use "veryfast")
- Reduce resolution
- Lower framerate to 24 fps
- Ensure proper cooling

## 📊 System Requirements by Resolution

| Resolution | Bitrate | CPU Usage | Upload Speed |
|------------|---------|-----------|--------------|
| 1280x720   | 2000k   | ~40%      | 2.5 Mbps     |
| 1920x1080  | 2500k   | ~60%      | 3.5 Mbps     |
| 1920x1080  | 4000k   | ~70%      | 5 Mbps       |
| 2560x1440  | 6000k   | ~85%      | 7.5 Mbps     |

## 🔧 Service Management

```bash
# Streamer service
sudo systemctl start rtmp-streamer
sudo systemctl stop rtmp-streamer
sudo systemctl restart rtmp-streamer
sudo systemctl status rtmp-streamer

# Dashboard service
sudo systemctl start rtmp-dashboard
sudo systemctl stop rtmp-dashboard
sudo systemctl restart rtmp-dashboard
sudo systemctl status rtmp-dashboard

# View logs
journalctl -u rtmp-streamer -f
journalctl -u rtmp-dashboard -f

# Enable/disable autostart
sudo systemctl enable rtmp-streamer
sudo systemctl disable rtmp-streamer
```

## 🔄 Updating

```bash
cd rtmp-streamer
git pull
sudo systemctl restart rtmp-streamer
sudo systemctl restart rtmp-dashboard
```

## ❌ Uninstallation

```bash
# Stop and disable services
sudo systemctl stop rtmp-streamer rtmp-dashboard
sudo systemctl disable rtmp-streamer rtmp-dashboard

# Remove service files
sudo rm /etc/systemd/system/rtmp-streamer.service
sudo rm /etc/systemd/system/rtmp-dashboard.service
sudo rm /etc/sudoers.d/rtmp-streamer

# Remove installation directory
rm -rf /home/pi/streamer

# Reload systemd
sudo systemctl daemon-reload
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 🙏 Credits

Built with:
- [picamera2](https://github.com/raspberrypi/picamera2) - Raspberry Pi camera interface
- [FFmpeg](https://ffmpeg.org/) - Video encoding
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [psutil](https://github.com/giampaolo/psutil) - System monitoring

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

## 🗺️ Roadmap

- [ ] Audio support via USB microphone
- [ ] Multi-camera support
- [ ] Overlay text/images on stream
- [ ] Recording to local storage
- [ ] Stream to multiple platforms simultaneously
- [ ] Mobile app for remote control
- [ ] Stream scheduling
- [ ] Automatic restart on disconnect
- [ ] Motion detection triggers

---

Made with ❤️ for the Raspberry Pi community
