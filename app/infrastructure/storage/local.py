from pathlib import Path
from typing import BinaryIO
from uuid import uuid4
from app.config import settings


class LocalObjectStorage:
    def __init__(self, root: Path | None = None):
        self.root = root or settings.object_storage_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, original_filename: str, content: BinaryIO) -> tuple[str, int]:
        suffix = Path(original_filename or "uploaded.bin").suffix
        stored_name = f"{uuid4().hex}{suffix}"
        target = self.root / stored_name
        size = 0
        with target.open("wb") as out:
            while True:
                chunk = content.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                out.write(chunk)
        return stored_name, size

    def path_for(self, stored_filename: str) -> Path:
        candidate = (self.root / stored_filename).resolve()
        root_resolved = self.root.resolve()
        if root_resolved not in candidate.parents and candidate != root_resolved:
            raise ValueError("Invalid storage path")
        return candidate

    def exists(self, stored_filename: str) -> bool:
        return self.path_for(stored_filename).exists()
