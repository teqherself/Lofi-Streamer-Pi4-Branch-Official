#!/usr/bin/env python3
"""
Commercial Grade RTMP Camera Streamer for Raspberry Pi 4
Supports YouTube, Twitch, and any RTMP service via Restream
Uses picamera2 for camera control and FFmpeg for encoding
"""

import subprocess
import time
import json
import os
import sys
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FfmpegOutput
import signal

class RTMPStreamer:
    def __init__(self, config_file='/home/pi/streamer/config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.camera = None
        self.encoder = None
        self.output = None
        self.streaming = False
        self.start_time = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.log("Streamer initialized")
    
    def load_config(self):
        """Load streaming configuration"""
        default_config = {
            "rtmp_url": "rtmp://a.rtmp.youtube.com/live2/",
            "stream_key": "YOUR_STREAM_KEY_HERE",
            "resolution": [1920, 1080],
            "framerate": 30,
            "bitrate": 2500000,
            "gop_size": 60,
            "preset": "medium",
            "audio_enabled": False,
            "audio_source": "hw:1,0"
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
        except Exception as e:
            self.log(f"Error loading config: {e}, using defaults")
        
        return default_config
    
    def save_config(self, new_config):
        """Save configuration to file"""
        try:
            self.config.update(new_config)
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.log("Configuration saved")
            return True
        except Exception as e:
            self.log(f"Error saving config: {e}")
            return False
    
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        sys.stdout.flush()
        
        # Also write to log file
        try:
            log_dir = "/home/pi/streamer/logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "streamer.log")
            with open(log_file, 'a') as f:
                f.write(log_msg + "\n")
        except:
            pass
    
    def setup_camera(self):
        """Initialize and configure the camera"""
        try:
            self.log("Initializing camera...")
            self.camera = Picamera2()
            
            # Configure for video streaming
            video_config = self.camera.create_video_configuration(
                main={
                    "size": tuple(self.config['resolution']),
                    "format": "RGB888"
                },
                controls={
                    "FrameRate": self.config['framerate']
                }
            )
            self.camera.configure(video_config)
            
            self.log(f"Camera configured: {self.config['resolution']}@{self.config['framerate']}fps")
            return True
            
        except Exception as e:
            self.log(f"Camera setup error: {e}")
            return False
    
    def build_ffmpeg_command(self):
        """Build FFmpeg RTMP streaming command"""
        rtmp_url = f"{self.config['rtmp_url']}{self.config['stream_key']}"
        
        # Base FFmpeg command for video
        cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f"{self.config['resolution'][0]}x{self.config['resolution'][1]}",
            '-r', str(self.config['framerate']),
            '-i', '-',  # Input from stdin
        ]
        
        # Add audio if enabled
        if self.config.get('audio_enabled', False):
            cmd.extend([
                '-f', 'alsa',
                '-i', self.config.get('audio_source', 'hw:1,0'),
                '-ac', '2',
                '-ar', '44100',
            ])
        
        # Video encoding settings
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', self.config.get('preset', 'medium'),
            '-b:v', str(self.config['bitrate']),
            '-maxrate', str(self.config['bitrate']),
            '-bufsize', str(self.config['bitrate'] * 2),
            '-pix_fmt', 'yuv420p',
            '-g', str(self.config.get('gop_size', 60)),
            '-keyint_min', str(self.config.get('gop_size', 60)),
            '-sc_threshold', '0',
        ])
        
        # Audio encoding if enabled
        if self.config.get('audio_enabled', False):
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '128k',
            ])
        
        # RTMP output settings
        cmd.extend([
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            rtmp_url
        ])
        
        return cmd
    
    def start_stream(self):
        """Start the RTMP stream"""
        if self.streaming:
            self.log("Already streaming")
            return False
        
        try:
            # Setup camera
            if not self.setup_camera():
                return False
            
            # Build FFmpeg command
            ffmpeg_cmd = self.build_ffmpeg_command()
            self.log(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # Create FFmpeg output
            self.output = FfmpegOutput(
                ' '.join(ffmpeg_cmd),
                audio=self.config.get('audio_enabled', False)
            )
            
            # Start camera and encoder
            self.camera.start()
            time.sleep(2)  # Let camera warm up
            
            self.camera.start_recording(self.output)
            
            self.streaming = True
            self.start_time = datetime.now()
            self.log("Stream started successfully")
            
            # Write status file
            self.write_status()
            
            return True
            
        except Exception as e:
            self.log(f"Error starting stream: {e}")
            self.cleanup()
            return False
    
    def stop_stream(self):
        """Stop the RTMP stream"""
        if not self.streaming:
            self.log("Not currently streaming")
            return False
        
        try:
            self.log("Stopping stream...")
            self.cleanup()
            self.streaming = False
            self.start_time = None
            self.log("Stream stopped")
            self.write_status()
            return True
            
        except Exception as e:
            self.log(f"Error stopping stream: {e}")
            return False
    
    def cleanup(self):
        """Clean up camera and encoder resources"""
        try:
            if self.camera:
                if self.streaming:
                    self.camera.stop_recording()
                self.camera.stop()
                self.camera.close()
                self.camera = None
            self.output = None
        except Exception as e:
            self.log(f"Cleanup error: {e}")
    
    def write_status(self):
        """Write current status to file for dashboard"""
        status = {
            "streaming": self.streaming,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "resolution": self.config['resolution'],
            "framerate": self.config['framerate'],
            "bitrate": self.config['bitrate']
        }
        
        try:
            status_file = "/home/pi/streamer/status.json"
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            self.log(f"Error writing status: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log(f"Received signal {signum}, shutting down...")
        self.stop_stream()
        sys.exit(0)
    
    def run(self):
        """Main run loop - keeps stream alive"""
        self.log("Starting streamer service...")
        
        # Start streaming
        if not self.start_stream():
            self.log("Failed to start stream")
            return
        
        # Keep running and update status
        try:
            while self.streaming:
                self.write_status()
                time.sleep(10)
        except KeyboardInterrupt:
            self.log("Keyboard interrupt received")
        finally:
            self.stop_stream()

if __name__ == "__main__":
    streamer = RTMPStreamer()
    streamer.run()
