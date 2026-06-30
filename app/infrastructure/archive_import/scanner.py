from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from app.domain.archive_import import ArchiveEntry, ArchiveScanSummary


SERVICE_FOLDERS = {
    "mail": {"mail", "gmail"},
    "drive": {"drive", "my drive"},
    "calendar": {"calendar"},
    "contacts": {"contacts"},
    "tasks": {"tasks"},
    "maps": {"maps", "location history", "timeline", "my maps"},
    "chrome": {"chrome"},
    "photos": {"google photos", "photos"},
}

FILE_TYPES = {
    ".mbox": "email",
    ".pdf": "document",
    ".docx": "document",
    ".xlsx": "spreadsheet",
    ".xls": "spreadsheet",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".mp4": "video",
    ".txt": "document",
    ".zip": "archive",
    ".tgz": "archive",
    ".ics": "calendar",
    ".vcf": "contacts",
    ".json": "data",
    ".html": "document",
}


class ZipArchiveScanner:
    def scan(self, archive_path: Path, archive_file_id: int | None = None) -> ArchiveScanSummary:
        entries: list[ArchiveEntry] = []
        top_levels: set[str] = set()
        with ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                parts = [part for part in Path(info.filename).parts if part not in {"", "."}]
                if not parts:
                    continue
                top_levels.add(parts[0])
                extension = Path(parts[-1]).suffix.lower()
                arbitrary_wrapper = parts[0].casefold() != "takeout" and self._looks_like_wrapper(parts[0], parts[1:])
                normalised_parts = self._normalise_parts(parts)
                normalised_path = "/".join(normalised_parts)
                service = "drive" if arbitrary_wrapper and extension in FILE_TYPES else self._service(normalised_parts)
                entries.append(
                    ArchiveEntry(
                        original_path=info.filename,
                        normalised_path=normalised_path,
                        service=service,
                        content_type=FILE_TYPES.get(extension, "binary"),
                        extension=extension,
                        size_bytes=info.file_size,
                    )
                )
        return ArchiveScanSummary(
            archive_file_id=archive_file_id,
            top_level_folders=tuple(sorted(top_levels)),
            entries=tuple(entries),
            counts_by_service=dict(Counter(entry.service for entry in entries)),
            counts_by_content_type=dict(Counter(entry.content_type for entry in entries)),
            counts_by_extension=dict(Counter(entry.extension for entry in entries)),
        )

    def _normalise_parts(self, parts: list[str]) -> list[str]:
        if parts and parts[0].casefold() == "takeout":
            return parts[1:]
        if len(parts) > 1 and self._looks_like_wrapper(parts[0], parts[1:]):
            return parts[1:]
        return parts

    def _looks_like_wrapper(self, root: str, remainder: list[str]) -> bool:
        if root.casefold() in {"t1", "t2", "t3", "split1", "split2"}:
            return True
        if not remainder:
            return False
        return self._service(remainder) != "unknown" or Path(remainder[-1]).suffix.lower() in FILE_TYPES

    def _service(self, parts: list[str]) -> str:
        lowered = [part.casefold() for part in parts]
        for service, names in SERVICE_FOLDERS.items():
            if any(part in names for part in lowered[:3]):
                return service
        extension = Path(parts[-1]).suffix.lower() if parts else ""
        if extension in {".jpg", ".jpeg", ".png", ".gif", ".mp4"}:
            return "photos"
        if extension in FILE_TYPES:
            return "drive"
        return "unknown"
