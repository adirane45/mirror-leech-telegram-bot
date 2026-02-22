"""
Phase 11: Recursive Matryoshka Deep Extraction

Recursively extracts supported archives (zip) up to a max depth.
"""

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ExtractionResult:
    extracted_files: List[str]
    archives_processed: int


class RecursiveExtractor:
    """Extract nested archives (zip) with depth limits."""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max(1, max_depth)

    def extract_recursive(self, archive_path: str, output_dir: str) -> ExtractionResult:
        extracted_files: List[str] = []
        archives_processed = 0

        queue = [(Path(archive_path), Path(output_dir), 1)]
        while queue:
            current_path, current_out, depth = queue.pop(0)
            if depth > self.max_depth:
                continue
            if current_path.suffix.lower() != ".zip":
                continue

            current_out.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(current_path, "r") as zip_ref:
                zip_ref.extractall(current_out)
                archives_processed += 1

            for root, _, files in os.walk(current_out):
                for name in files:
                    full_path = Path(root) / name
                    extracted_files.append(str(full_path))
                    if full_path.suffix.lower() == ".zip":
                        next_out = full_path.parent / full_path.stem
                        queue.append((full_path, next_out, depth + 1))

        return ExtractionResult(
            extracted_files=extracted_files,
            archives_processed=archives_processed,
        )
