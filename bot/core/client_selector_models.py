"""
Client Selector Models
Data structures for download client selection and routing
"""

from enum import Enum


class LinkType(Enum):
    """Types of download links"""
    DIRECT = "direct"            # HTTP/HTTPS direct downloads
    TORRENT = "torrent"          # Magnet/torrent files
    NZB = "nzb"                  # Usenet NZB files
    GDRIVE = "gdrive"            # Google Drive
    MEDIAFIRE = "mediafire"      # Mediafire
    ZIP_ARCHIVE = "zip_archive"  # Zipped content
    UNKNOWN = "unknown"


class ClientType(Enum):
    """Available download clients"""
    ARIA2 = "aria2"              # Fast, lightweight (direct + torrents)
    QBITTORRENT = "qbittorrent"  # Torrent specialist
    SABNZBD = "sabnzbd"          # Usenet specialist
