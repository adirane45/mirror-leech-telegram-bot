"""
Archive Management Commands - ZIP and UNZIP operations

Commands:
- /zip <path> [format] [level] - Create archive
- /unzip <path> [destination] - Extract archive
- /zipinfo <path> - Show archive contents

Usage Examples:
    /zip /downloads/folder            - Create ZIP with default compression
    /zip /downloads/video.mp4 zip 9   - Create ZIP with max compression
    /unzip /downloads/archive.zip     - Extract to same directory
    /unzip /downloads/archive.zip /tmp/extract  - Extract to specific path
    /zipinfo archive.zip              - List archive contents

Modified by: justadi
Created: 2026-01-30
"""

import os
import logging
from bot.core.archive_manager import archive_manager
from bot.helper.ext_utils.bot_utils import new_task, is_premium_user
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from pyrogram.types import Message
from pyrogram.filters import command

LOGGER = logging.getLogger(__name__)


@new_task
async def compress_file(_, message: Message):
    """
    Create ZIP/TAR/7Z archive from files or folders
    
    Usage:
        /zip /path/to/source             - Create ZIP (default compression level 6)
        /zip /path/to/source zip         - Specify ZIP format
        /zip /path/to/source 7z 9        - Use 7Z with max compression (9)
        /zip /path/to/source tar.gz      - Use TAR.GZ format
    
    Supported Formats:
        zip     - Universal format (fast compression)
        tar     - Uncompressed TAR archive
        tar.gz  - TAR with GZIP (good compression)
        tar.bz2 - TAR with BZIP2 (better compression)
        7z      - Best compression ratio
    
    Compression Levels (0-9):
        0 - Store only (no compression)
        1-5 - Light to medium compression
        6 - Default (balanced)
        7-9 - High compression (slower)
    
    Modified by: justadi
    """
    parts = message.text.split()
    
    if len(parts) < 2:
        await sendMessage(message, "❌ Usage: /zip <source_path> [format] [level]\n\n"
                         "Formats: zip, tar, tar.gz, tar.bz2, 7z\n"
                         "Levels: 0-9 (0=no compression, 9=max compression)")
        return
    
    source_path = parts[1]
    format_type = parts[2].lower() if len(parts) > 2 else 'zip'
    compression_level = 6
    
    if len(parts) > 3:
        try:
            compression_level = int(parts[3])
            compression_level = max(0, min(9, compression_level))
        except ValueError:
            await sendMessage(message, "❌ Compression level must be 0-9")
            return
    
    # Validate source path
    if not os.path.exists(source_path):
        await sendMessage(message, f"❌ Source not found: {source_path}")
        return
    
    # Check if user has permission
    if not await is_premium_user(message.from_user.id):
        await sendMessage(message, "⚠️ This feature is available for premium users")
        return
    
    # Validate format
    if format_type not in archive_manager.SUPPORTED_COMPRESS:
        formats = ", ".join(archive_manager.SUPPORTED_COMPRESS)
        await sendMessage(message, f"❌ Unsupported format: {format_type}\n\nSupported: {formats}")
        return
    
    # Determine output filename
    source_name = os.path.basename(source_path.rstrip('/'))
    output_path = f"{source_path}.{format_type.replace('tar.', 't')}"
    
    # Inform user about operation start
    status_msg = await sendMessage(
        message,
        f"🔄 Creating {format_type.upper()} archive...\n"
        f"Source: {source_name}\n"
        f"Compression: Level {compression_level}\n\n"
        f"Please wait..."
    )
    
    try:
        # Create archive
        success, msg, stats = await archive_manager.compress(
            source_path=source_path,
            output_path=output_path,
            format=format_type,
            compression_level=compression_level
        )
        
        if success:
            # Format response
            original_size = stats.get('original_size', 0)
            compressed_size = stats.get('compressed_size', 0)
            ratio = stats.get('ratio', 0)
            time_taken = stats.get('time_taken', 0)
            
            response = (
                "✅ <b>Archive Created Successfully!</b>\n\n"
                f"📦 <b>Format:</b> {format_type.upper()}\n"
                f"📁 <b>Filename:</b> <code>{os.path.basename(output_path)}</code>\n"
                f"💾 <b>Original Size:</b> {_format_size(original_size)}\n"
                f"📦 <b>Compressed Size:</b> {_format_size(compressed_size)}\n"
                f"📊 <b>Compression Ratio:</b> {ratio:.1f}%\n"
                f"⏱️ <b>Time Taken:</b> {time_taken:.2f}s\n"
                f"🚀 <b>Speed:</b> {_format_size(original_size/time_taken) if time_taken > 0 else 'N/A'}/s\n\n"
                f"📍 <b>Location:</b> <code>{output_path}</code>"
            )
            
            await editMessage(status_msg, response)
        else:
            await editMessage(status_msg, f"❌ Error: {msg}")
    
    except Exception as e:
        LOGGER.error(f"Archive creation error: {e}")
        await editMessage(status_msg, f"❌ Unexpected error: {str(e)}")


@new_task
async def extract_archive(_, message: Message):
    """
    Extract ZIP/TAR/7Z/RAR archive
    
    Usage:
        /unzip /path/to/archive.zip           - Extract to same directory
        /unzip archive.zip /tmp/extract       - Extract to specific directory
        /unzip archive.zip /tmp password123   - Extract with password
    
    Supported Formats:
        zip - ZIP archives
        tar - TAR archives
        tar.gz / tgz - Gzipped TAR
        tar.bz2 / tbz2 - Bzipped TAR
        7z - 7-Zip archives
        rar - RAR archives (requires unrar)
    
    Modified by: justadi
    """
    parts = message.text.split()
    
    if len(parts) < 2:
        await sendMessage(message, "❌ Usage: /unzip <archive_path> [destination] [password]")
        return
    
    archive_path = parts[1]
    extract_to = parts[2] if len(parts) > 2 else os.path.dirname(archive_path) or '.'
    password = parts[3] if len(parts) > 3 else None
    
    # Validate archive path
    if not os.path.exists(archive_path):
        await sendMessage(message, f"❌ Archive not found: {archive_path}")
        return
    
    # Check if file is actually an archive
    if not os.path.isfile(archive_path):
        await sendMessage(message, f"❌ {archive_path} is not a file")
        return
    
    # Check permission
    if not await is_premium_user(message.from_user.id):
        await sendMessage(message, "⚠️ This feature is available for premium users")
        return
    
    # Create extraction directory if needed
    os.makedirs(extract_to, exist_ok=True)
    
    archive_name = os.path.basename(archive_path)
    
    status_msg = await sendMessage(
        message,
        f"🔄 Extracting archive...\n"
        f"Archive: {archive_name}\n"
        f"Destination: {extract_to}\n\n"
        f"Please wait..."
    )
    
    try:
        # Extract archive
        success, msg, stats = await archive_manager.extract(
            archive_path=archive_path,
            extract_to=extract_to,
            password=password
        )
        
        if success:
            file_count = stats.get('file_count', 0)
            total_size = stats.get('total_size', 0)
            time_taken = stats.get('time_taken', 0)
            
            response = (
                "✅ <b>Archive Extracted Successfully!</b>\n\n"
                f"📁 <b>Archive:</b> <code>{archive_name}</code>\n"
                f"📦 <b>Files Extracted:</b> {file_count}\n"
                f"💾 <b>Total Size:</b> {_format_size(total_size)}\n"
                f"⏱️ <b>Time Taken:</b> {time_taken:.2f}s\n"
                f"🚀 <b>Speed:</b> {_format_size(total_size/time_taken) if time_taken > 0 else 'N/A'}/s\n\n"
                f"📍 <b>Destination:</b> <code>{extract_to}</code>"
            )
            
            await editMessage(status_msg, response)
        else:
            await editMessage(status_msg, f"❌ Error: {msg}")
    
    except Exception as e:
        LOGGER.error(f"Archive extraction error: {e}")
        await editMessage(status_msg, f"❌ Unexpected error: {str(e)}")


@new_task
async def list_archive(_, message: Message):
    """
    List contents of ZIP/TAR/7Z archive
    
    Usage:
        /zipinfo /path/to/archive.zip
        /zipinfo archive.zip
    
    Shows:
    - File count
    - Total uncompressed size
    - Compression ratio
    - File listing with individual sizes
    
    Modified by: justadi
    """
    parts = message.text.split()
    
    if len(parts) < 2:
        await sendMessage(message, "❌ Usage: /zipinfo <archive_path>")
        return
    
    archive_path = parts[1]
    
    if not os.path.exists(archive_path):
        await sendMessage(message, f"❌ Archive not found: {archive_path}")
        return
    
    archive_name = os.path.basename(archive_path)
    
    status_msg = await sendMessage(
        message,
        f"🔄 Reading archive contents...\n"
        f"Archive: {archive_name}\n\n"
        f"Please wait..."
    )
    
    try:
        # Get archive stats
        stats = await archive_manager.get_zip_stats(archive_path)
        
        if stats.get('valid'):
            file_count = stats['file_count']
            total_size = stats['total_size']
            compressed_size = stats['compressed_size']
            ratio = stats['compression_ratio']
            
            response = (
                f"📦 <b>Archive Information</b>\n\n"
                f"📁 <b>File:</b> <code>{archive_name}</code>\n"
                f"📊 <b>Files:</b> {file_count}\n"
                f"💾 <b>Original Size:</b> {_format_size(total_size)}\n"
                f"📦 <b>Compressed Size:</b> {_format_size(compressed_size)}\n"
                f"📈 <b>Compression Ratio:</b> {ratio:.1f}%\n\n"
                f"<b>Use /unzip to extract this archive</b>"
            )
            
            await editMessage(status_msg, response)
        else:
            await editMessage(status_msg, "❌ Failed to read archive information")
    
    except Exception as e:
        LOGGER.error(f"Archive info error: {e}")
        await editMessage(status_msg, f"❌ Error: {str(e)}")


def _format_size(bytes_size: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"
