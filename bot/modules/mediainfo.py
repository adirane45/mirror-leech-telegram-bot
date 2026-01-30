"""
Media Information Command - Extract video/audio metadata

Commands:
- /mediainfo <file_path> - Get detailed media information
- /mediainfo <file_path> brief - Get brief information
- /thumbnail <file_path> [timestamp] - Extract video thumbnail

Usage Examples:
    /mediainfo /downloads/movie.mkv           - Full media analysis
    /mediainfo video.mp4 brief                - Brief summary
    /thumbnail video.mp4                      - Extract thumbnail at 5 seconds
    /thumbnail video.mp4 00:00:30             - Extract thumbnail at 30 seconds

Technologies Used:
- FFprobe (FFmpeg) - Media file analysis
- FFmpeg - Thumbnail extraction
- JSON parsing - FFprobe output

Modified by: justadi
Created: 2026-01-30
"""

import os
import logging
from bot.core.media_info import media_info_extractor
from bot.helper.ext_utils.bot_utils import new_task, is_premium_user
from bot.helper.telegram_helper.message_utils import send_message, edit_message, send_file
from pyrogram.types import Message

LOGGER = logging.getLogger(__name__)


@new_task
async def get_media_info(_, message: Message):
    """
    Extract and display comprehensive media file information
    
    Usage:
        /mediainfo /path/to/file.mp4              - Full detailed analysis
        /mediainfo video.mkv brief                - Brief summary only
    
    Detailed Output Includes:
    - Container format (MP4, MKV, AVI, etc.)
    - File size and duration
    - Video streams (codec, resolution, fps, bitrate)
    - Audio streams (codec, channels, sample rate)
    - Subtitle streams
    - Metadata (title, artist, album, etc.)
    
    Quality Rating:
    - Very Low (480p or less)
    - Low (480-720p)
    - Medium (720p)
    - High (1080p)
    - Excellent (4K/2160p)
    
    Step-by-Step Example:
    1. Command: /mediainfo movie.mkv
    2. Bot analyzes file with FFprobe
    3. Bot extracts: codecs, resolution, bitrate, streams
    4. Bot displays formatted information
    5. Bot provides quality rating
    
    Modified by: justadi
    """
    parts = message.text.split()
    
    if len(parts) < 2:
        await send_message(message, 
            "❌ <b>Usage:</b> /mediainfo &lt;file_path&gt; [brief]\n\n"
            "<b>Examples:</b>\n"
            "  /mediainfo /path/to/video.mp4\n"
            "  /mediainfo movie.mkv brief\n\n"
            "<b>Shows:</b> Codecs, Resolution, Bitrate, Duration, Audio streams, Subtitles, Metadata")
        return
    
    file_path = parts[1]
    brief_mode = len(parts) > 2 and parts[2].lower() == 'brief'
    
    # Validate file exists
    if not os.path.exists(file_path):
        await send_message(message, f"❌ File not found: {file_path}")
        return
    
    if not os.path.isfile(file_path):
        await send_message(message, f"❌ {file_path} is not a file")
        return
    
    # Check permission
    if not await is_premium_user(message.from_user.id):
        await send_message(message, "⚠️ This feature is available for premium users")
        return
    
    file_name = os.path.basename(file_path)
    
    status_msg = await send_message(
        message,
        f"🔍 Analyzing media file...\n"
        f"📁 File: <code>{file_name}</code>\n\n"
        f"Please wait..."
    )
    
    try:
        # Extract media information
        media_info = await media_info_extractor.get_media_info(file_path)
        
        if media_info:
            # Format information
            info_text = media_info_extractor.format_info(media_info, detailed=not brief_mode)
            
            # Get quality rating
            quality = media_info_extractor.get_quality_rating(media_info)
            info_text += f"\n\n⭐ <b>Quality:</b> {quality}"
            
            await edit_message(status_msg, info_text)
        else:
            await edit_message(status_msg, 
                "❌ Failed to extract media information\n\n"
                "<b>Make sure:</b>\n"
                "• File is a valid media file\n"
                "• FFmpeg is installed on the server\n"
                "• File is readable and not corrupted")
    
    except Exception as e:
        LOGGER.error(f"Media info extraction error: {e}")
        await edit_message(status_msg, f"❌ Error: {str(e)}")


@new_task
async def extract_thumbnail(_, message: Message):
    """
    Extract thumbnail/frame from video file
    
    Usage:
        /thumbnail /path/to/video.mp4              - Extract at 5 seconds (default)
        /thumbnail video.mp4 00:00:30              - Extract at 30 seconds
        /thumbnail movie.mkv 00:02:45              - Extract at 2 minutes 45 seconds
    
    Parameters:
        file_path: Path to video file
        timestamp: Position in HH:MM:SS format (default: 00:00:05)
    
    Output:
        - Thumbnail image (JPEG, 320px width)
        - Saved to same directory as video
        - Filename: video_thumbnail.jpg
    
    Time Format:
        - 00:00:05 = 5 seconds
        - 00:00:30 = 30 seconds
        - 00:01:00 = 1 minute
        - 00:02:45 = 2 minutes 45 seconds
        - 01:30:00 = 1 hour 30 minutes
    
    Step-by-Step Example:
    1. User: /thumbnail movie.mkv 00:00:30
    2. Bot uses FFmpeg to seek to 30 seconds
    3. Bot extracts video frame at that position
    4. Bot scales to 320px width for preview
    5. Bot sends thumbnail image to user
    
    Modified by: justadi
    """
    parts = message.text.split()
    
    if len(parts) < 2:
        await send_message(message,
            "❌ <b>Usage:</b> /thumbnail &lt;file_path&gt; [timestamp]\n\n"
            "<b>Examples:</b>\n"
            "  /thumbnail /path/to/video.mp4\n"
            "  /thumbnail movie.mkv 00:00:30\n"
            "  /thumbnail film.avi 00:02:15\n\n"
            "<b>Format:</b> HH:MM:SS (default: 00:00:05)")
        return
    
    file_path = parts[1]
    timestamp = parts[2] if len(parts) > 2 else "00:00:05"
    
    # Validate file
    if not os.path.exists(file_path):
        await send_message(message, f"❌ File not found: {file_path}")
        return
    
    if not os.path.isfile(file_path):
        await send_message(message, f"❌ {file_path} is not a file")
        return
    
    # Validate timestamp format
    try:
        time_parts = timestamp.split(':')
        if len(time_parts) != 3:
            raise ValueError("Invalid format")
        for part in time_parts:
            int(part)
    except:
        await send_message(message, 
            "❌ Invalid timestamp format\n\n"
            "Use HH:MM:SS format (e.g., 00:00:30)")
        return
    
    # Check permission
    if not await is_premium_user(message.from_user.id):
        await send_message(message, "⚠️ This feature is available for premium users")
        return
    
    file_name = os.path.basename(file_path)
    
    status_msg = await send_message(
        message,
        f"🎬 Extracting thumbnail...\n"
        f"📁 File: <code>{file_name}</code>\n"
        f"⏱️ Timestamp: {timestamp}\n\n"
        f"Please wait..."
    )
    
    try:
        # Generate thumbnail path
        file_dir = os.path.dirname(file_path) or '.'
        file_base = os.path.splitext(file_name)[0]
        thumbnail_path = os.path.join(file_dir, f"{file_base}_thumbnail.jpg")
        
        # Extract thumbnail
        success = await media_info_extractor.extract_thumbnail(
            file_path=file_path,
            output_path=thumbnail_path,
            timestamp=timestamp
        )
        
        if success and os.path.exists(thumbnail_path):
            # Send thumbnail
            await edit_message(status_msg, 
                f"✅ Thumbnail extracted successfully!\n\n"
                f"📁 Source: <code>{file_name}</code>\n"
                f"⏱️ Timestamp: {timestamp}\n"
                f"💾 Size: {os.path.getsize(thumbnail_path)} bytes")
            
            # Send the image
            await send_file(message, thumbnail_path, 
                caption=f"Thumbnail from {file_name} @ {timestamp}")
        else:
            await edit_message(status_msg,
                "❌ Failed to extract thumbnail\n\n"
                "<b>Make sure:</b>\n"
                "• Video file is valid and readable\n"
                "• FFmpeg is installed\n"
                "• Timestamp is valid")
    
    except Exception as e:
        LOGGER.error(f"Thumbnail extraction error: {e}")
        await edit_message(status_msg, f"❌ Error: {str(e)}")


@new_task
async def quick_media_stats(_, message: Message):
    """
    Quick media statistics (brief version)
    
    Usage:
        /mstats /path/to/file.mp4
    
    Shows only essential information:
    - Resolution and FPS
    - Duration and file size
    - Codec information
    - Quality rating
    
    Useful for quick checks without detailed analysis
    
    Modified by: justadi
    """
    parts = message.text.split()
    
    if len(parts) < 2:
        await send_message(message, "❌ Usage: /mstats <file_path>")
        return
    
    file_path = parts[1]
    
    if not os.path.exists(file_path):
        await send_message(message, f"❌ File not found: {file_path}")
        return
    
    file_name = os.path.basename(file_path)
    
    status_msg = await send_message(
        message,
        f"📊 Getting quick stats...\n"
        f"📁 File: <code>{file_name}</code>"
    )
    
    try:
        media_info = await media_info_extractor.get_media_info(file_path)
        
        if media_info:
            fmt = media_info['format']
            quality = media_info_extractor.get_quality_rating(media_info)
            
            lines = [
                "📊 <b>Quick Media Stats</b>\n",
                f"📁 <b>File:</b> {file_name}",
                f"📦 <b>Format:</b> {fmt['format_name'].upper()}",
                f"⏱️ <b>Duration:</b> {_format_duration(fmt['duration'])}",
                f"💾 <b>Size:</b> {_format_size(fmt['size'])}",
            ]
            
            if media_info['video_streams']:
                v = media_info['video_streams'][0]
                lines.extend([
                    f"🎬 <b>Resolution:</b> {v['resolution']} @ {v['fps']} FPS",
                    f"📹 <b>Video Codec:</b> {v['codec_name'].upper()}",
                ])
            
            if media_info['audio_streams']:
                a = media_info['audio_streams'][0]
                lines.extend([
                    f"🔊 <b>Audio Codec:</b> {a['codec_name'].upper()}",
                    f"🎙️ <b>Channels:</b> {a['channels']} ({a['channel_layout']})",
                ])
            
            lines.append(f"\n⭐ <b>Quality:</b> {quality}")
            
            await edit_message(status_msg, '\n'.join(lines))
        else:
            await edit_message(status_msg, "❌ Failed to extract media information")
    
    except Exception as e:
        LOGGER.error(f"Quick stats error: {e}")
        await edit_message(status_msg, f"❌ Error: {str(e)}")


def _format_duration(seconds: float) -> str:
    """Convert seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def _format_size(bytes_size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"
