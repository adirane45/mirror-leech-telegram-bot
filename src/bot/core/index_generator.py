"""
Phase 10: Index Link Generation

Generates shareable HTML indexes for batches of files.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


CATEGORY_ORDER = [
    "videos",
    "audio",
    "images",
    "documents",
    "archives",
    "other",
]

EXTENSION_CATEGORIES = {
    "videos": {"mp4", "mkv", "avi", "mov", "webm"},
    "audio": {"mp3", "flac", "aac", "m4a", "ogg", "wav"},
    "images": {"jpg", "jpeg", "png", "gif", "webp"},
    "documents": {"pdf", "txt", "doc", "docx", "xls", "xlsx", "ppt", "pptx"},
    "archives": {"zip", "rar", "7z", "tar", "gz", "bz2"},
}


@dataclass
class IndexFileItem:
    name: str
    url: str
    size_bytes: int = 0
    mime_type: str = "application/octet-stream"
    category: str = "other"


@dataclass
class IndexMetadata:
    index_id: str
    title: str
    created_at: datetime
    expires_at: Optional[datetime]
    total_files: int
    total_size_bytes: int
    categories: Dict[str, int] = field(default_factory=dict)


@dataclass
class IndexArtifact:
    html: str
    url: str
    metadata: IndexMetadata


class IndexGenerator:
    """Generate index HTML for a list of files."""

    def __init__(self, title: Optional[str] = None):
        self.default_title = title or "Shared Index"

    def build_index(self, items: List[IndexFileItem], title: Optional[str] = None,
                    expires_in_days: Optional[int] = None) -> IndexMetadata:
        index_id = self._make_index_id(items, title)
        created_at = datetime.now(timezone.utc)
        expires_at = None
        if expires_in_days:
            expires_at = created_at + timedelta(days=expires_in_days)

        categories: Dict[str, int] = {key: 0 for key in CATEGORY_ORDER}
        total_size = 0
        for item in items:
            categories[item.category] = categories.get(item.category, 0) + 1
            total_size += item.size_bytes

        return IndexMetadata(
            index_id=index_id,
            title=title or self.default_title,
            created_at=created_at,
            expires_at=expires_at,
            total_files=len(items),
            total_size_bytes=total_size,
            categories=categories,
        )

    def build_index_html(self, items: List[IndexFileItem], metadata: IndexMetadata) -> str:
        grouped: Dict[str, List[IndexFileItem]] = {key: [] for key in CATEGORY_ORDER}
        for item in items:
            grouped.setdefault(item.category, []).append(item)

        sections = []
        for category in CATEGORY_ORDER:
            if not grouped.get(category):
                continue
            rows = []
            for item in grouped[category]:
                rows.append(
                    "<tr>"
                    f"<td>{escape(item.name)}</td>"
                    f"<td><a href=\"{escape(item.url)}\">download</a></td>"
                    f"<td>{self._format_size(item.size_bytes)}</td>"
                    "</tr>"
                )
            section_html = (
                f"<h3>{escape(category.title())}</h3>"
                "<table>"
                "<tr><th>Name</th><th>Link</th><th>Size</th></tr>"
                + "".join(rows)
                + "</table>"
            )
            sections.append(section_html)

        expiry_text = (
            f"Expires: {metadata.expires_at.isoformat()}"
            if metadata.expires_at else "No expiration"
        )

        html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(metadata.title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #666; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
    th {{ background: #f4f4f4; }}
    a {{ color: #1a73e8; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>{escape(metadata.title)}</h1>
  <div class=\"meta\">Generated: {metadata.created_at.isoformat()} | {expiry_text}</div>
  <div class=\"meta\">Files: {metadata.total_files} | Size: {self._format_size(metadata.total_size_bytes)}</div>
  {"".join(sections)}
</body>
</html>"""
        return html

    def build_items_from_links(self, links: List[str]) -> List[IndexFileItem]:
        items: List[IndexFileItem] = []
        for link in links:
            parsed = urlparse(link)
            name = parsed.path.split("/")[-1] or parsed.netloc
            category = self._guess_category(name)
            items.append(IndexFileItem(name=name, url=link, category=category))
        return items

    def _guess_category(self, filename: str) -> str:
        if "." not in filename:
            return "other"
        ext = filename.rsplit(".", 1)[-1].lower()
        for category, extensions in EXTENSION_CATEGORIES.items():
            if ext in extensions:
                return category
        return "other"

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes <= 0:
            return "-"
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        for unit in units:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _make_index_id(self, items: List[IndexFileItem], title: Optional[str]) -> str:
        seed = (title or self.default_title) + "|" + "|".join(i.url for i in items)
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


class IndexStorage:
    """Mock storage backend for index HTML."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._storage: Dict[str, str] = {}

    def upload_index(self, html: str, index_id: str) -> str:
        token = index_id or hashlib.md5(html.encode("utf-8")).hexdigest()[:10]
        self._storage[token] = html
        if self.base_url:
            return f"{self.base_url}/{token}"
        return f"index://{token}"

    def get_index(self, token: str) -> Optional[str]:
        return self._storage.get(token)
