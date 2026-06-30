from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.infrastructure.archive_import.scanner import ZipArchiveScanner


def write_zip(path: Path, files: dict[str, bytes]) -> None:
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def test_scanner_detects_standard_takeout_services(tmp_path):
    archive_path = tmp_path / "takeout.zip"
    write_zip(
        archive_path,
        {
            "Takeout/Mail/All mail Including Spam and Trash.mbox": b"From x\nSubject: Hi\n\nBody\n",
            "Takeout/Drive/report.pdf": b"%PDF",
            "Takeout/Calendar/calendar.ics": b"BEGIN:VCALENDAR",
            "Takeout/Contacts/contacts.vcf": b"BEGIN:VCARD",
            "Takeout/Chrome/Bookmarks.html": b"<html></html>",
        },
    )

    summary = ZipArchiveScanner().scan(archive_path)

    assert summary.top_level_folders == ("Takeout",)
    assert summary.counts_by_service["mail"] == 1
    assert summary.counts_by_service["drive"] == 1
    assert summary.counts_by_service["calendar"] == 1
    assert summary.counts_by_service["contacts"] == 1
    assert summary.counts_by_service["chrome"] == 1
    assert summary.entries[1].original_path == "Takeout/Drive/report.pdf"
    assert summary.entries[1].normalised_path == "Drive/report.pdf"


def test_scanner_detects_arbitrary_root_drive_archives(tmp_path):
    archive_path = tmp_path / "drive-split.zip"
    write_zip(
        archive_path,
        {
            "t1/My Drive/Budget.xlsx": b"sheet",
            "t1/photos/photo.jpg": b"jpg",
            "t2/nested/archive.tgz": b"tgz",
        },
    )

    summary = ZipArchiveScanner().scan(archive_path)

    assert summary.top_level_folders == ("t1", "t2")
    assert summary.counts_by_service["drive"] == 3
    assert summary.counts_by_extension[".xlsx"] == 1
    assert summary.entries[0].original_path == "t1/My Drive/Budget.xlsx"
    assert summary.entries[0].normalised_path == "My Drive/Budget.xlsx"
