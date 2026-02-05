"""
Media Info Extraction Module - Analyze video/audio files

This module extracts technical information from media files using FFmpeg/FFprobe.
Provides detailed codec, resolution, bitrate, and quality information.

Technologies:
- FFprobe: Media file analysis (part of FFmpeg)
- subprocess: Execute FFprobe commands
- json: Parse FFprobe JSON output

Use Cases:
- Pre-download quality verification
- Codec compatibility checking
- Bandwidth estimation
- File integrity validation

Modified by: justadi
Created: 2026-01-30
"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, List
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class MediaInfoExtractor:
    """
    Extract and format media file information
    
    Features:
    - Video stream analysis (codec, resolution, fps, bitrate)
    - Audio stream analysis (codec, channels, sample rate)
    - Subtitle stream detection
    - Container format information
    - Duration and file size
    - Thumbnail extraction
    
    Usage:
        extractor = MediaInfoExtractor()
        info = await extractor.get_media_info("/path/to/video.mp4")
        formatted = extractor.format_info(info)
    """
    
    def __init__(self):
        """Initialize media info extractor"""
        self.ffprobe_path = "ffprobe"
        self.ffmpeg_path = "ffmpeg"
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if FFmpeg/FFprobe are available"""
        try:
            # Will be checked at runtime
            pass
        except Exception as e:
            LOGGER.warning(f"FFmpeg check warning: {e}")
    
    async def get_media_info(self, file_path: str) -> Optional[Dict]:
        """
        Extract comprehensive media information
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dictionary containing:
            - format: Container format info (name, duration, size, bitrate)
            - video_streams: List of video stream details
            - audio_streams: List of audio stream details
            - subtitle_streams: List of subtitle tracks
            - metadata: Title, artist, album, etc.
            
        Example:
            info = await extractor.get_media_info("movie.mkv")
            print(f"Duration: {info['format']['duration']}s")
            print(f"Resolution: {info['video_streams'][0]['resolution']}")
        """
        try:
            if not os.path.exists(file_path):
                LOGGER.error(f"File not found: {file_path}")
                return None
            
            # Run ffprobe command
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                LOGGER.error(f"FFprobe error: {stderr.decode()}")
                return None
            
            # Parse JSON output
            data = json.loads(stdout.decode())
            
            # Process and organize information
            media_info = {
                'format': self._parse_format(data.get('format', {})),
                'video_streams': [],
                'audio_streams': [],
                'subtitle_streams': [],
                'metadata': data.get('format', {}).get('tags', {})
            }
            
            # Parse streams
            for stream in data.get('streams', []):
                codec_type = stream.get('codec_type', '')
                
                if codec_type == 'video':
                    media_info['video_streams'].append(self._parse_video_stream(stream))
                elif codec_type == 'audio':
                    media_info['audio_streams'].append(self._parse_audio_stream(stream))
                elif codec_type == 'subtitle':
                    media_info['subtitle_streams'].append(self._parse_subtitle_stream(stream))
            
            return media_info
            
        except FileNotFoundError:
            LOGGER.error("FFprobe not found. Install FFmpeg package.")
            return None
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse FFprobe output: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"Media info extraction error: {e}")
            return None
    
    def _parse_format(self, format_data: dict) -> dict:
        """Parse container format information"""
        return {
            'filename': os.path.basename(format_data.get('filename', 'Unknown')),
            'format_name': format_data.get('format_name', 'Unknown'),
            'format_long_name': format_data.get('format_long_name', 'Unknown'),
            'duration': float(format_data.get('duration', 0)),
            'size': int(format_data.get('size', 0)),
            'bitrate': int(format_data.get('bit_rate', 0)),
            'probe_score': format_data.get('probe_score', 0)
        }
    
    def _parse_video_stream(self, stream: dict) -> dict:
        """Parse video stream information"""
        width = stream.get('width', 0)
        height = stream.get('height', 0)
        
        # Calculate FPS
        fps = 0
        if 'r_frame_rate' in stream:
            try:
                num, den = map(int, stream['r_frame_rate'].split('/'))
                fps = num / den if den != 0 else 0
            except:
                fps = 0
        
        return {
            'index': stream.get('index', 0),
            'codec_name': stream.get('codec_name', 'Unknown'),
            'codec_long_name': stream.get('codec_long_name', 'Unknown'),
            'profile': stream.get('profile', 'Unknown'),
            'width': width,
            'height': height,
            'resolution': f"{width}x{height}",
            'aspect_ratio': stream.get('display_aspect_ratio', 'N/A'),
            'fps': round(fps, 2),
            'bitrate': int(stream.get('bit_rate', 0)),
            'pix_fmt': stream.get('pix_fmt', 'Unknown'),
            'color_space': stream.get('color_space', 'Unknown'),
            'duration': float(stream.get('duration', 0))
        }
    
    def _parse_audio_stream(self, stream: dict) -> dict:
        """Parse audio stream information"""
        return {
            'index': stream.get('index', 0),
            'codec_name': stream.get('codec_name', 'Unknown'),
            'codec_long_name': stream.get('codec_long_name', 'Unknown'),
            'channels': stream.get('channels', 0),
            'channel_layout': stream.get('channel_layout', 'Unknown'),
            'sample_rate': int(stream.get('sample_rate', 0)),
            'bitrate': int(stream.get('bit_rate', 0)),
            'language': stream.get('tags', {}).get('language', 'Unknown'),
            'title': stream.get('tags', {}).get('title', ''),
            'duration': float(stream.get('duration', 0))
        }
    
    def _parse_subtitle_stream(self, stream: dict) -> dict:
        """Parse subtitle stream information"""
        return {
            'index': stream.get('index', 0),
            'codec_name': stream.get('codec_name', 'Unknown'),
            'language': stream.get('tags', {}).get('language', 'Unknown'),
            'title': stream.get('tags', {}).get('title', ''),
            'forced': stream.get('disposition', {}).get('forced', 0) == 1
        }
    
    def format_info(self, media_info: Dict, detailed: bool = True) -> str:
        """
        Format media info into readable text
        
        Args:
            media_info: Dictionary from get_media_info()
            detailed: Include detailed stream information
            
        Returns:
            Formatted string for display
            
        Example:
            info = await extractor.get_media_info("video.mp4")
            text = extractor.format_info(info)
            await message.reply(text)
        """
        if not media_info:
            return "❌ Unable to extract media information"
        
        lines = []
        fmt = media_info['format']
        
        # Header
        lines.append("📊 <b>Media Information</b>\n")
        
        # File info
        lines.append(f"📁 <b>File:</b> {fmt['filename']}")
        lines.append(f"📦 <b>Format:</b> {fmt['format_name'].upper()}")
        lines.append(f"⏱ <b>Duration:</b> {self._format_duration(fmt['duration'])}")
        lines.append(f"💾 <b>Size:</b> {self._format_size(fmt['size'])}")
        lines.append(f"📡 <b>Bitrate:</b> {self._format_bitrate(fmt['bitrate'])}\n")
        
        # Video streams
        if media_info['video_streams']:
            lines.append("🎬 <b>Video Streams:</b>")
            for i, video in enumerate(media_info['video_streams'], 1):
                lines.append(f"  <b>Stream {i}:</b>")
                lines.append(f"    • Codec: {video['codec_name'].upper()} ({video['profile']})")
                lines.append(f"    • Resolution: {video['resolution']} @ {video['fps']} FPS")
                lines.append(f"    • Aspect Ratio: {video['aspect_ratio']}")
                if video['bitrate'] > 0:
                    lines.append(f"    • Bitrate: {self._format_bitrate(video['bitrate'])}")
                if detailed:
                    lines.append(f"    • Pixel Format: {video['pix_fmt']}")
                    lines.append(f"    • Color Space: {video['color_space']}")
            lines.append("")
        
        # Audio streams
        if media_info['audio_streams']:
            lines.append("🔊 <b>Audio Streams:</b>")
            for i, audio in enumerate(media_info['audio_streams'], 1):
                title = f" - {audio['title']}" if audio['title'] else ""
                lang = f" ({audio['language']})" if audio['language'] != 'Unknown' else ""
                lines.append(f"  <b>Stream {i}{title}{lang}:</b>")
                lines.append(f"    • Codec: {audio['codec_name'].upper()}")
                lines.append(f"    • Channels: {audio['channels']} ({audio['channel_layout']})")
                lines.append(f"    • Sample Rate: {audio['sample_rate']} Hz")
                if audio['bitrate'] > 0:
                    lines.append(f"    • Bitrate: {self._format_bitrate(audio['bitrate'])}")
            lines.append("")
        
        # Subtitles
        if media_info['subtitle_streams']:
            lines.append("💬 <b>Subtitle Streams:</b>")
            for i, sub in enumerate(media_info['subtitle_streams'], 1):
                title = f" - {sub['title']}" if sub['title'] else ""
                lang = f" ({sub['language']})" if sub['language'] != 'Unknown' else ""
                forced = " [FORCED]" if sub['forced'] else ""
                lines.append(f"  {i}. {sub['codec_name'].upper()}{lang}{title}{forced}")
            lines.append("")
        
        # Metadata
        if detailed and media_info['metadata']:
            meta = media_info['metadata']
            lines.append("ℹ️ <b>Metadata:</b>")
            for key in ['title', 'artist', 'album', 'date', 'genre', 'comment']:
                if key in meta:
                    lines.append(f"  • {key.capitalize()}: {meta[key]}")
        
        return '\n'.join(lines)
    
    def _format_duration(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _format_size(self, bytes: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def _format_bitrate(self, bitrate: int) -> str:
        """Format bitrate to Kbps or Mbps"""
        if bitrate == 0:
            return "N/A"
        
        kbps = bitrate / 1000
        if kbps >= 1000:
            return f"{kbps/1000:.2f} Mbps"
        else:
            return f"{kbps:.0f} Kbps"
    
    async def extract_thumbnail(self, file_path: str, output_path: str, timestamp: str = "00:00:05") -> bool:
        """
        Extract thumbnail from video at specified timestamp
        
        Args:
            file_path: Path to video file
            output_path: Path to save thumbnail
            timestamp: Time position (HH:MM:SS format)
            
        Returns:
            True if successful
            
        Example:
            success = await extractor.extract_thumbnail(
                "video.mp4",
                "thumb.jpg",
                "00:00:10"
            )
        """
        try:
            cmd = [
                self.ffmpeg_path,
                '-ss', timestamp,
                '-i', file_path,
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            return process.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            LOGGER.error(f"Thumbnail extraction error: {e}")
            return False
    
    def get_quality_rating(self, media_info: Dict) -> str:
        """
        Rate video quality based on technical specs
        
        Returns:
            Quality rating string (Low/Medium/High/Excellent)
        """
        if not media_info or not media_info['video_streams']:
            return "Unknown"
        
        video = media_info['video_streams'][0]
        height = video['height']
        bitrate = video['bitrate']
        
        # Resolution-based rating
        if height >= 2160:  # 4K
            quality = "Excellent (4K)"
        elif height >= 1080:  # Full HD
            quality = "High (1080p)"
        elif height >= 720:  # HD
            quality = "Medium (720p)"
        elif height >= 480:  # SD
            quality = "Low (480p)"
        else:
            quality = "Very Low"
        
        # Adjust based on bitrate
        if bitrate > 0:
            expected_bitrate = height * video['width'] * video['fps'] * 0.1
            if bitrate < expected_bitrate * 0.5:
                quality += " ⚠️ Low Bitrate"
        
        return quality


# Global instance
media_info_extractor = MediaInfoExtractor()
