"""
Phase 10: Batch Operations

Parses and schedules batch link processing.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class BatchEntry:
    entry_id: str
    link: str
    scheduled_at: datetime
    status: str = "queued"
    error: Optional[str] = None


@dataclass
class BatchRequest:
    user_id: int
    links: List[str]
    mode: str = "mirror"
    stagger_seconds: int = 5
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class BatchSummary:
    batch_id: str
    total_links: int
    queued_count: int
    invalid_count: int
    mode: str


class BatchOperationsManager:
    """Manage batch link submissions."""

    def __init__(self) -> None:
        self._batches: Dict[str, List[BatchEntry]] = {}

    def parse_link_list(self, text: str, max_links: int = 1000) -> Tuple[List[str], List[str]]:
        valid_links: List[str] = []
        invalid_lines: List[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = re.split(r"\s+", line)
            for part in parts:
                if part.startswith("#"):
                    break
                if self._is_valid_link(part):
                    valid_links.append(part)
                elif part:
                    invalid_lines.append(part)
            if len(valid_links) >= max_links:
                break

        deduped = list(dict.fromkeys(valid_links))
        return deduped, invalid_lines

    def create_batch(self, request: BatchRequest) -> Tuple[BatchSummary, List[BatchEntry]]:
        batch_id = uuid.uuid4().hex[:12]
        entries: List[BatchEntry] = []
        now = datetime.now(timezone.utc)
        for idx, link in enumerate(request.links):
            scheduled_at = now + timedelta(seconds=idx * max(0, request.stagger_seconds))
            entries.append(BatchEntry(entry_id=uuid.uuid4().hex[:12], link=link, scheduled_at=scheduled_at))

        self._batches[batch_id] = entries

        summary = BatchSummary(
            batch_id=batch_id,
            total_links=len(request.links),
            queued_count=len(entries),
            invalid_count=0,
            mode=request.mode,
        )
        return summary, entries

    def get_batch(self, batch_id: str) -> List[BatchEntry]:
        return self._batches.get(batch_id, [])

    def _is_valid_link(self, link: str) -> bool:
        if link.startswith("magnet:"):
            return True
        parsed = urlparse(link)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
