from pathlib import Path


def preallocate_file_sync(dest_path: str, file_size: int) -> None:
    path = Path(dest_path)
    with path.open("wb") as destination:
        if file_size > 0:
            destination.seek(file_size - 1)
            destination.write(b"\0")
