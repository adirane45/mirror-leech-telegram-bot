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
import logging
import os
import tarfile
import zipfile
from pathlib import Path
from time import time
from typing import Awaitable, Callable, Dict, List, Literal, Optional, Tuple, TypeAlias

LOGGER = logging.getLogger(__name__)

ProgressCallback: TypeAlias = Callable[[str], Awaitable[None]]
ArchiveStats: TypeAlias = Dict[str, int | float]


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

    def __init__(self) -> None:
        """Initialize archive manager"""
        self.current_operation: Optional[str] = None
        self.progress = 0

    async def compress(
        self,
        source_path: str,
        output_path: str,
        format: str = 'zip',
        compression_level: int = 6,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Tuple[bool, str, ArchiveStats]:
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
            if not await asyncio.to_thread(os.path.exists, source_path):
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
            compressed_size = await asyncio.to_thread(os.path.getsize, output_path)
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
        progress_callback: Optional[ProgressCallback] = None
    ) -> Tuple[bool, str, ArchiveStats]:
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
            if not await asyncio.to_thread(os.path.exists, archive_path):
                return False, f"Archive not found: {archive_path}", {}

            # Detect format from extension
            format = self._detect_format(archive_path)
            if format not in self.SUPPORTED_EXTRACT:
                return False, f"Unsupported archive format", {}

            # Create extraction directory
            await asyncio.to_thread(os.makedirs, extract_to, exist_ok=True)

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

    async def _compress_zip(
        self,
        source_path: str,
        output_path: str,
        level: int,
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str]:
        """Compress using ZIP format"""
        try:
            if callback:
                await callback("Starting ZIP compression")

            await asyncio.to_thread(self._compress_zip_sync, source_path, output_path, level)

            if callback:
                await callback("ZIP compression completed")

            return True, "ZIP compression complete"
        except Exception as e:
            return False, f"ZIP error: {str(e)}"

    async def _compress_tar(
        self,
        source_path: str,
        output_path: str,
        format: str,
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str]:
        """Compress using TAR format"""
        try:
            if callback:
                await callback(f"Compressing with {format}")

            await asyncio.to_thread(self._compress_tar_sync, source_path, output_path, format)

            return True, f"{format.upper()} compression complete"
        except Exception as e:
            return False, f"TAR error: {str(e)}"

    async def _compress_7z(
        self,
        source_path: str,
        output_path: str,
        level: int,
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str]:
        """Compress using 7z format (requires 7z binary)"""
        try:
            cmd = ['7z', 'a', f'-mx={level}', output_path, source_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()

            if process.returncode == 0:
                return True, "7Z compression complete"
            else:
                return False, f"7z error: {stderr.decode()}"
        except FileNotFoundError:
            return False, "7z binary not found. Install p7zip-full package."
        except Exception as e:
            return False, f"7Z error: {str(e)}"

    async def _extract_zip(
        self,
        archive_path: str,
        extract_to: str,
        password: Optional[str],
        files: Optional[List[str]],
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str, int]:
        """Extract ZIP archive"""
        try:
            file_count = await asyncio.to_thread(
                self._extract_zip_sync,
                archive_path,
                extract_to,
                password,
                files,
            )
            if callback:
                await callback(f"Extracted {file_count} files")

            return True, "ZIP extraction complete", file_count
        except Exception as e:
            return False, f"ZIP extraction error: {str(e)}", 0

    async def _extract_tar(
        self,
        archive_path: str,
        extract_to: str,
        files: Optional[List[str]],
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str, int]:
        """Extract TAR archive"""
        try:
            file_count = await asyncio.to_thread(
                self._extract_tar_sync,
                archive_path,
                extract_to,
                files,
            )

            if callback:
                await callback(f"Extracted {file_count} files")

            return True, "TAR extraction complete", file_count
        except Exception as e:
            return False, f"TAR extraction error: {str(e)}", 0

    async def _extract_7z(
        self,
        archive_path: str,
        extract_to: str,
        password: Optional[str],
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str, int]:
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
            _, stderr = await process.communicate()

            if process.returncode == 0:
                # Count extracted files
                file_count = await asyncio.to_thread(self._count_files, extract_to)
                return True, "7Z extraction complete", file_count
            else:
                return False, f"7z error: {stderr.decode()}", 0
        except FileNotFoundError:
            return False, "7z binary not found", 0
        except Exception as e:
            return False, f"7Z error: {str(e)}", 0

    async def _extract_rar(
        self,
        archive_path: str,
        extract_to: str,
        password: Optional[str],
        callback: Optional[ProgressCallback],
    ) -> Tuple[bool, str, int]:
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
            _, stderr = await process.communicate()

            if process.returncode == 0:
                file_count = await asyncio.to_thread(self._count_files, extract_to)
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
        return await asyncio.to_thread(self._get_size_sync, path)

    def _compress_zip_sync(self, source_path: str, output_path: str, level: int) -> None:
        """Blocking ZIP compression implementation."""
        compression = zipfile.ZIP_DEFLATED if level > 0 else zipfile.ZIP_STORED

        with zipfile.ZipFile(output_path, 'w', compression, compresslevel=level) as zipf:
            if os.path.isfile(source_path):
                zipf.write(source_path, os.path.basename(source_path))
                return

            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)

    def _compress_tar_sync(self, source_path: str, output_path: str, format: str) -> None:
        """Blocking TAR compression implementation."""
        mode: Literal['w', 'w:gz', 'w:bz2']
        if format == 'tar.gz':
            mode = 'w:gz'
        elif format == 'tar.bz2':
            mode = 'w:bz2'
        else:
            mode = 'w'

        with tarfile.open(output_path, mode=mode) as tar:
            tar.add(source_path, arcname=os.path.basename(source_path))

    def _extract_zip_sync(
        self,
        archive_path: str,
        extract_to: str,
        password: Optional[str],
        files: Optional[List[str]],
    ) -> int:
        """Blocking ZIP extraction implementation."""
        pwd = password.encode() if password else None

        with zipfile.ZipFile(archive_path, 'r') as zipf:
            members = files if files else zipf.namelist()
            for member in members:
                zipf.extract(member, extract_to, pwd=pwd)
            return len(members)

    def _extract_tar_sync(
        self,
        archive_path: str,
        extract_to: str,
        files: Optional[List[str]],
    ) -> int:
        """Blocking TAR extraction implementation."""
        with tarfile.open(archive_path, 'r:*') as tar:
            members = [tar.getmember(f) for f in files] if files else tar.getmembers()
            tar.extractall(extract_to, members)
            return len(members)

    def _count_files(self, path: str) -> int:
        """Count all files recursively in a path."""
        return len([f for f in Path(path).rglob('*') if f.is_file()])

    def _get_size_sync(self, path: str) -> int:
        """Blocking total size calculation for file or directory."""
        if os.path.isfile(path):
            return os.path.getsize(path)

        total = 0
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total += os.path.getsize(file_path)
                except (OSError, IOError) as e:
                    LOGGER.debug(f"Could not get size of {file_path}: {e}")
        return total

    def get_supported_formats(self) -> Dict[str, Dict[str, str]]:
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
