"""
Phase 11: Salvage Mode (Corrupted Recovery)

Simple recovery helper that copies bytes while skipping known bad ranges.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SalvageResult:
    input_path: str
    output_path: str
    bytes_written: int
    skipped_ranges: List[Tuple[int, int]]


class SalvageMode:
    """Recover data by skipping corrupted ranges."""

    def recover_file(
        self,
        input_path: str,
        output_path: str,
        skip_ranges: List[Tuple[int, int]],
    ) -> SalvageResult:
        skip_ranges_sorted = sorted(skip_ranges, key=lambda r: r[0])
        bytes_written = 0
        cursor = 0

        with open(input_path, "rb") as reader, open(output_path, "wb") as writer:
            for start, end in skip_ranges_sorted:
                if start > cursor:
                    reader.seek(cursor)
                    chunk = reader.read(start - cursor)
                    writer.write(chunk)
                    bytes_written += len(chunk)
                cursor = max(cursor, end)

            reader.seek(cursor)
            tail = reader.read()
            writer.write(tail)
            bytes_written += len(tail)

        return SalvageResult(
            input_path=input_path,
            output_path=output_path,
            bytes_written=bytes_written,
            skipped_ranges=skip_ranges_sorted,
        )
