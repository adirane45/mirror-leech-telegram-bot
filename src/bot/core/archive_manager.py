"""
Archive Management Module - Compress and extract files

This module provides functionality to compress files/folders into archives
and extract archives before upload or after download.

Supported Formats:
- ZIP: Universal format, good compression
- TAR.GZ: Unix standard, excellent compression
- TAR.BZ2: Better compression than gzip
- 7Z: Best compression ratio
- RAR: Extract only (proprietary)

Technologies:
- zipfile: Native Python ZIP support
- tarfile: Native Python TAR support
- py7zr: 7-Zip format support
- subprocess: External tools (7z, rar)

Modified by: justadi
Created: 2026-01-30
"""

import asyncio
import os
import zipfile
import tarfile
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from time import time

LOGGER = logging.getLogger(__name__)


class ArchiveManager:
    """
    Manages archive operations for the bot
    
    Features:
    - Multi-format compression (zip, tar.gz, tar.bz2, 7z)
    - Multi-format extraction (all above + rar)
    - Progress tracking during operations
    - Recursive directory compression
    - Selective extraction
    - Size estimation before compression
    
    Usage:
        manager = ArchiveManager()
        await manager.compress("/path/to/folder", "output.zip", "zip")
        await manager.extract("archive.zip", "/extract/path")
    """
    
    SUPPORTED_COMPRESS = ['zip', 'tar', 'tar.gz', 'tar.bz2', '7z']
    SUPPORTED_EXTRACT = ['zip', 'tar', 'tar.gz', 'tar.bz2', '7z', 'rar']
    
    def __init__(self):
        """Initialize archive manager"""
        self.current_operation = None
        self.progress = 0
        
    async def compress(
        self, 
        source_path: str, 
        output_path: str, 
        format: str = 'zip',
        compression_level: int = 6,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str, dict]:
        """
        Compress files or folders into an archive
        
        Args:
            source_path: Path to file/folder to compress
            output_path: Output archive path
            format: Archive format (zip, tar.gz, tar.bz2, 7z)
            compression_level: 0-9 (0=none, 9=max)
            progress_callback: Function to call with progress updates
            
        Returns:
            Tuple of (success, message, stats_dict)
            stats_dict contains: original_size, compressed_size, ratio, time_taken
            
        Example:
            success, msg, stats = await manager.compress(
                "/downloads/folder",
                "/downloads/archive.zip",
                "zip",
                compression_level=9
            )
        """
        start_time = time()
        self.current_operation = f"Compressing {os.path.basename(source_path)}"
        
        try:
            if not os.path.exists(source_path):
                return False, f"Source path not found: {source_path}", {}
                
            if format not in self.SUPPORTED_COMPRESS:
                return False, f"Unsupported format: {format}. Supported: {', '.join(self.SUPPORTED_COMPRESS)}", {}
            
            # Calculate original size
            original_size = await self._get_size(source_path)
            
            # Perform compression based on format
            if format == 'zip':
                success, msg = await self._compress_zip(source_path, output_path, compression_level, progress_callback)
            elif format in ['tar', 'tar.gz', 'tar.bz2']:
                success, msg = await self._compress_tar(source_path, output_path, format, progress_callback)
            elif format == '7z':
                success, msg = await self._compress_7z(source_path, output_path, compression_level, progress_callback)
            else:
                return False, f"Format {format} not implemented", {}
            
            if not success:
                return False, msg, {}
            
            # Calculate stats
            compressed_size = os.path.getsize(output_path)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            time_taken = time() - start_time
            
            stats = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'ratio': ratio,
                'time_taken': time_taken
            }
            
            return True, f"Successfully compressed to {os.path.basename(output_path)}", stats
            
        except Exception as e:
            LOGGER.error(f"Compression error: {e}")
            return False, f"Compression failed: {str(e)}", {}
        finally:
            self.current_operation = None
    
    async def extract(
        self,
        archive_path: str,
        extract_to: str,
        password: Optional[str] = None,
        files: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str, dict]:
        """
        Extract archive to specified directory
        
        Args:
            archive_path: Path to archive file
            extract_to: Destination directory
            password: Password for encrypted archives
            files: Specific files to extract (None = all)
            progress_callback: Function to call with progress updates
            
        Returns:
            Tuple of (success, message, stats_dict)
            stats_dict contains: file_count, total_size, time_taken
            
        Example:
            success, msg, stats = await manager.extract(
                "/downloads/archive.zip",
                "/downloads/extracted",
                password="secret123"
            )
        """
        start_time = time()
        self.current_operation = f"Extracting {os.path.basename(archive_path)}"
        
        try:
            if not os.path.exists(archive_path):
                return False, f"Archive not found: {archive_path}", {}
            
            # Detect format from extension
            format = self._detect_format(archive_path)
            if format not in self.SUPPORTED_EXTRACT:
                return False, f"Unsupported archive format", {}
            
            # Create extraction directory
            os.makedirs(extract_to, exist_ok=True)
            
            # Perform extraction based on format
            if format == 'zip':
                success, msg, file_count = await self._extract_zip(archive_path, extract_to, password, files, progress_callback)
            elif format in ['tar', 'tar.gz', 'tar.bz2']:
                success, msg, file_count = await self._extract_tar(archive_path, extract_to, files, progress_callback)
            elif format == '7z':
                success, msg, file_count = await self._extract_7z(archive_path, extract_to, password, progress_callback)
            elif format == 'rar':
                success, msg, file_count = await self._extract_rar(archive_path, extract_to, password, progress_callback)
            else:
                return False, f"Format {format} not implemented", {}
            
            if not success:
                return False, msg, {}
            
            # Calculate stats
            total_size = await self._get_size(extract_to)
            time_taken = time() - start_time
            
            stats = {
                'file_count': file_count,
                'total_size': total_size,
                'time_taken': time_taken
            }
            
            return True, f"Successfully extracted {file_count} file(s)", stats
            
        except Exception as e:
            LOGGER.error(f"Extraction error: {e}")
            return False, f"Extraction failed: {str(e)}", {}
        finally:
            self.current_operation = None
    
    async def _compress_zip(self, source_path, output_path, level, callback):
        """Compress using ZIP format"""
        try:
            compression = zipfile.ZIP_DEFLATED if level > 0 else zipfile.ZIP_STORED
            
            with zipfile.ZipFile(output_path, 'w', compression, compresslevel=level) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arcname)
                            if callback:
                                await callback(f"Adding {arcname}")
            
            return True, "ZIP compression complete"
        except Exception as e:
            return False, f"ZIP error: {str(e)}"
    
    async def _compress_tar(self, source_path, output_path, format, callback):
        """Compress using TAR format"""
        try:
            mode_map = {
                'tar': 'w',
                'tar.gz': 'w:gz',
                'tar.bz2': 'w:bz2'
            }
            mode = mode_map.get(format, 'w')
            
            with tarfile.open(output_path, mode) as tar:
                tar.add(source_path, arcname=os.path.basename(source_path))
                if callback:
                    await callback(f"Compressing with {format}")
            
            return True, f"{format.upper()} compression complete"
        except Exception as e:
            return False, f"TAR error: {str(e)}"
    
    async def _compress_7z(self, source_path, output_path, level, callback):
        """Compress using 7z format (requires 7z binary)"""
        try:
            cmd = ['7z', 'a', f'-mx={level}', output_path, source_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, "7Z compression complete"
            else:
                return False, f"7z error: {stderr.decode()}"
        except FileNotFoundError:
            return False, "7z binary not found. Install p7zip-full package."
        except Exception as e:
            return False, f"7Z error: {str(e)}"
    
    async def _extract_zip(self, archive_path, extract_to, password, files, callback):
        """Extract ZIP archive"""
        try:
            pwd = password.encode() if password else None
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                members = files if files else zipf.namelist()
                for member in members:
                    zipf.extract(member, extract_to, pwd=pwd)
                    if callback:
                        await callback(f"Extracted {member}")
                
                return True, "ZIP extraction complete", len(members)
        except Exception as e:
            return False, f"ZIP extraction error: {str(e)}", 0
    
    async def _extract_tar(self, archive_path, extract_to, files, callback):
        """Extract TAR archive"""
        try:
            with tarfile.open(archive_path, 'r:*') as tar:
                members = [tar.getmember(f) for f in files] if files else tar.getmembers()
                tar.extractall(extract_to, members)
                
                if callback:
                    await callback(f"Extracted {len(members)} files")
                
                return True, "TAR extraction complete", len(members)
        except Exception as e:
            return False, f"TAR extraction error: {str(e)}", 0
    
    async def _extract_7z(self, archive_path, extract_to, password, callback):
        """Extract 7z archive"""
        try:
            cmd = ['7z', 'x', archive_path, f'-o{extract_to}', '-y']
            if password:
                cmd.append(f'-p{password}')
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Count extracted files
                file_count = len([f for f in Path(extract_to).rglob('*') if f.is_file()])
                return True, "7Z extraction complete", file_count
            else:
                return False, f"7z error: {stderr.decode()}", 0
        except FileNotFoundError:
            return False, "7z binary not found", 0
        except Exception as e:
            return False, f"7Z error: {str(e)}", 0
    
    async def _extract_rar(self, archive_path, extract_to, password, callback):
        """Extract RAR archive (requires unrar)"""
        try:
            cmd = ['unrar', 'x', '-y', archive_path, extract_to]
            if password:
                cmd.insert(2, f'-p{password}')
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                file_count = len([f for f in Path(extract_to).rglob('*') if f.is_file()])
                return True, "RAR extraction complete", file_count
            else:
                return False, f"unrar error: {stderr.decode()}", 0
        except FileNotFoundError:
            return False, "unrar binary not found", 0
        except Exception as e:
            return False, f"RAR error: {str(e)}", 0
    
    def _detect_format(self, archive_path: str) -> str:
        """Detect archive format from filename"""
        lower = archive_path.lower()
        if lower.endswith('.tar.gz') or lower.endswith('.tgz'):
            return 'tar.gz'
        elif lower.endswith('.tar.bz2') or lower.endswith('.tbz2'):
            return 'tar.bz2'
        elif lower.endswith('.tar'):
            return 'tar'
        elif lower.endswith('.zip'):
            return 'zip'
        elif lower.endswith('.7z'):
            return '7z'
        elif lower.endswith('.rar'):
            return 'rar'
        return 'unknown'
    
    async def _get_size(self, path: str) -> int:
        """Calculate total size of file or directory"""
        if os.path.isfile(path):
            return os.path.getsize(path)
        
        total = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total += os.path.getsize(file_path)
                except (OSError, IOError) as e:
                    logger.debug(f"Could not get size of {file_path}: {e}")
                    pass
        return total
    
    def get_supported_formats(self) -> dict:
        """Get dictionary of supported formats with descriptions"""
        return {
            'compress': {
                'zip': 'Universal format, fast compression',
                'tar': 'Uncompressed archive',
                'tar.gz': 'TAR with gzip (good compression)',
                'tar.bz2': 'TAR with bzip2 (better compression)',
                '7z': 'Best compression ratio'
            },
            'extract': {
                'zip': 'ZIP archives',
                'tar': 'TAR archives',
                'tar.gz': 'Gzipped TAR',
                'tar.bz2': 'Bzipped TAR',
                '7z': '7-Zip archives',
                'rar': 'RAR archives (extract only)'
            }
        }


# Global instance
archive_manager = ArchiveManager()
