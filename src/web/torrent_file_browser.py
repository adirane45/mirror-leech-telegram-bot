"""
Torrent file browser - allows interactive selection of files from torrents

Provides:
- Torrent metadata extraction
- File tree structure
- File selection for downloads
- Statistics (size, count, etc.)
"""

import os
from logging import getLogger
from typing import Any, Dict, List, Optional

LOGGER = getLogger(__name__)


class TorrentFileInfo:
    """Information about a single file in a torrent"""

    def __init__(self, path: str, size: int, index: int = 0):
        self.path = path
        self.size = size
        self.index = index
        self.selected = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "index": self.index,
            "selected": self.selected,
            "filename": os.path.basename(self.path)
        }


class TorrentMetadata:
    """Metadata and file information for a torrent"""

    def __init__(self, torrent_hash: str, name: str, size: int):
        self.hash = torrent_hash
        self.name = name
        self.total_size = size
        self.files: List[TorrentFileInfo] = []
        self.selected_size = 0

    def add_file(self, path: str, size: int, index: int = 0):
        """Add a file to the torrent"""
        file_info = TorrentFileInfo(path, size, index)
        self.files.append(file_info)

    def select_file(self, index: int, selected: bool = True):
        """Select or deselect a specific file"""
        if 0 <= index < len(self.files):
            was_selected = self.files[index].selected
            self.files[index].selected = selected

            # Update selected size
            if selected and not was_selected:
                self.selected_size += self.files[index].size
            elif not selected and was_selected:
                self.selected_size -= self.files[index].size

    def select_all(self):
        """Select all files"""
        for file_info in self.files:
            if not file_info.selected:
                file_info.selected = True
                self.selected_size += file_info.size

    def deselect_all(self):
        """Deselect all files"""
        for file_info in self.files:
            file_info.selected = False
        self.selected_size = 0

    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths"""
        return [f.path for f in self.files if f.selected]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        total_selected = sum(f.size for f in self.files if f.selected)

        return {
            "hash": self.hash,
            "name": self.name,
            "total_size": self.total_size,
            "total_files": len(self.files),
            "selected_files_count": sum(1 for f in self.files if f.selected),
            "selected_size": total_selected,
            "files": [f.to_dict() for f in self.files],
            "completion_percent": (total_selected / self.total_size * 100) if self.total_size > 0 else 0
        }


class TorrentFileBrowser:
    """Browser for torrent files with caching"""

    def __init__(self):
        self.torrent_metadata_cache: Dict[str, TorrentMetadata] = {}

    def parse_torrent_metadata(self, torrent_hash: str, torrent_info: Dict[str, Any]) -> TorrentMetadata:
        """Parse torrent metadata from qBittorrent/Aria2 response"""

        name = torrent_info.get("name", f"torrent_{torrent_hash[:8]}")
        total_size = torrent_info.get("size", torrent_info.get("total_size", 0))

        metadata = TorrentMetadata(torrent_hash, name, total_size)

        # Parse files list from qBittorrent format
        if "files" in torrent_info:
            for idx, file_info in enumerate(torrent_info["files"]):
                file_path = file_info.get("name", "")
                file_size = file_info.get("size", 0)
                metadata.add_file(file_path, file_size, idx)

        # Parse from Aria2 format
        elif "bittorrent" in torrent_info:
            files = torrent_info["bittorrent"].get("files", [])
            for idx, file_info in enumerate(files):
                file_path = file_info.get("path", [f"file_{idx}"])[0]
                file_size = file_info.get("length", 0)
                metadata.add_file(file_path, file_size, idx)

        # Cache metadata
        self.torrent_metadata_cache[torrent_hash] = metadata
        return metadata

    def get_file_tree(self, torrent_hash: str) -> Optional[Dict[str, Any]]:
        """Get file tree structure for a torrent"""
        metadata = self.torrent_metadata_cache.get(torrent_hash)
        if not metadata:
            return None

        # Build directory tree
        tree = {
            "name": metadata.name,
            "type": "directory",
            "size": metadata.total_size,
            "children": []
        }

        # Group files by directory
        dir_structure = {}
        for file_info in metadata.files:
            parts = file_info.path.split("/")
            current_dir = dir_structure

            for part in parts[:-1]:
                if part not in current_dir:
                    current_dir[part] = {}
                current_dir = current_dir[part]

            # Add file info to leaf
            if "__files__" not in current_dir:
                current_dir["__files__"] = []
            current_dir["__files__"].append(file_info)

        # Convert structure to tree
        def build_tree_node(dir_dict, parent_path=""):
            children = []

            # Add directories
            for dir_name, dir_content in dir_dict.items():
                if dir_name != "__files__":
                    dir_path = f"{parent_path}/{dir_name}".lstrip("/")
                    children.append({
                        "name": dir_name,
                        "type": "directory",
                        "path": dir_path,
                        "children": build_tree_node(dir_content, dir_path)
                    })

            # Add files
            if "__files__" in dir_dict:
                for file_info in dir_dict["__files__"]:
                    children.append({
                        "name": file_info.path.split("/")[-1],
                        "type": "file",
                        "path": file_info.path,
                        "size": file_info.size,
                        "index": file_info.index,
                        "selected": file_info.selected
                    })

            return sorted(children, key=lambda x: (x["type"] != "directory", x["name"]))

        tree["children"] = build_tree_node(dir_structure)
        tree["stats"] = {
            "total_files": len(metadata.files),
            "selected_files": sum(1 for f in metadata.files if f.selected),
            "total_size": metadata.total_size,
            "selected_size": metadata.selected_size
        }

        return tree

    def select_files_by_pattern(self, torrent_hash: str, pattern: str) -> List[str]:
        """Select files matching a pattern (e.g., "*.mkv", ".*video.*")"""
        import fnmatch
        import re

        metadata = self.torrent_metadata_cache.get(torrent_hash)
        if not metadata:
            return []

        selected = []
        for idx, file_info in enumerate(metadata.files):
            # Try fnmatch for glob patterns
            if fnmatch.fnmatch(file_info.path, pattern):
                metadata.select_file(idx, True)
                selected.append(file_info.path)
            # Try regex patterns
            elif re.search(pattern, file_info.path):
                metadata.select_file(idx, True)
                selected.append(file_info.path)

        return selected

    def get_metadata(self, torrent_hash: str) -> Optional[Dict[str, Any]]:
        """Get torrent metadata as dictionary"""
        metadata = self.torrent_metadata_cache.get(torrent_hash)
        return metadata.to_dict() if metadata else None


# Global instance
file_browser = TorrentFileBrowser()
