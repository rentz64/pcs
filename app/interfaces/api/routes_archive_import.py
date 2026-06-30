from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.application.archive_import_use_cases import ArchiveImportUseCases
from app.domain.archive_import import ArchiveEntry, ArchiveFile, ArchiveImportResult, ArchiveImportSet, ArchiveScanSummary, ImportSetSummary
from app.domain.entities import User
from app.domain.errors import ArchiveFileNotFound, ArchiveImportSetNotFound
from app.interfaces.api.dependencies import current_user, get_archive_import_use_cases
from app.interfaces.api.schemas import (
    ArchiveEntryOut,
    ArchiveFileOut,
    ArchiveImportResultOut,
    ArchiveImportSetCreate,
    ArchiveImportSetOut,
    ArchiveScanSummaryOut,
    ImportSetSummaryOut,
)

router = APIRouter(prefix="/archive-import", tags=["archive-import"])


def _set_out(import_set: ArchiveImportSet) -> ArchiveImportSetOut:
    return ArchiveImportSetOut(
        id=import_set.id,
        owner_id=import_set.owner_id,
        external_source_id=import_set.external_source_id,
        external_account_id=import_set.external_account_id,
        display_name=import_set.display_name,
        source_type=import_set.source_type,
        notes=import_set.notes,
        created_at=import_set.created_at,
    )


def _archive_out(archive: ArchiveFile) -> ArchiveFileOut:
    return ArchiveFileOut(
        id=archive.id,
        import_set_id=archive.import_set_id,
        original_filename=archive.original_filename,
        size_bytes=archive.size_bytes,
        sha256_hash=archive.sha256_hash,
        status=archive.status.value,
        error_message=archive.error_message,
        registered_at=archive.registered_at,
    )


def _entry_out(entry: ArchiveEntry) -> ArchiveEntryOut:
    return ArchiveEntryOut(
        original_path=entry.original_path,
        normalised_path=entry.normalised_path,
        service=entry.service,
        content_type=entry.content_type,
        extension=entry.extension,
        size_bytes=entry.size_bytes,
    )


def _scan_out(summary: ArchiveScanSummary) -> ArchiveScanSummaryOut:
    return ArchiveScanSummaryOut(
        archive_file_id=summary.archive_file_id,
        top_level_folders=list(summary.top_level_folders),
        entries=[_entry_out(entry) for entry in summary.entries],
        counts_by_service=summary.counts_by_service,
        counts_by_content_type=summary.counts_by_content_type,
        counts_by_extension=summary.counts_by_extension,
    )


def _summary_out(summary: ImportSetSummary) -> ImportSetSummaryOut:
    return ImportSetSummaryOut(
        import_set_id=summary.import_set_id,
        archive_count=summary.archive_count,
        entries_count=summary.entries_count,
        counts_by_service=summary.counts_by_service,
        counts_by_content_type=summary.counts_by_content_type,
        counts_by_extension=summary.counts_by_extension,
    )


def _result_out(result: ArchiveImportResult) -> ArchiveImportResultOut:
    return ArchiveImportResultOut(import_set_id=result.import_set_id, imported_count=result.imported_count, email_count=result.email_count)


@router.post("/import-sets", response_model=ArchiveImportSetOut)
def create_import_set(
    payload: ArchiveImportSetCreate,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ArchiveImportSetOut:
    return _set_out(imports.create_import_set(user, payload.display_name, payload.account_label, payload.source_type, payload.notes))


@router.get("/import-sets", response_model=list[ArchiveImportSetOut])
def list_import_sets(
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> list[ArchiveImportSetOut]:
    return [_set_out(import_set) for import_set in imports.list_import_sets(user)]


@router.get("/import-sets/{import_set_id}", response_model=ArchiveImportSetOut)
def get_import_set(
    import_set_id: int,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ArchiveImportSetOut:
    try:
        return _set_out(imports.get_import_set(user, import_set_id))
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")


@router.post("/import-sets/{import_set_id}/archives", response_model=ArchiveFileOut)
def register_archive(
    import_set_id: int,
    file: UploadFile = File(...),
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ArchiveFileOut:
    try:
        return _archive_out(imports.register_archive(user, import_set_id, file.filename or "archive.zip", file.file))
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")


@router.get("/import-sets/{import_set_id}/archives", response_model=list[ArchiveFileOut])
def list_archives(
    import_set_id: int,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> list[ArchiveFileOut]:
    try:
        return [_archive_out(archive) for archive in imports.list_archives(user, import_set_id)]
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")


@router.post("/archives/{archive_id}/scan", response_model=ArchiveScanSummaryOut)
def scan_archive(
    archive_id: int,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ArchiveScanSummaryOut:
    try:
        return _scan_out(imports.scan_archive(user, archive_id))
    except ArchiveFileNotFound:
        raise HTTPException(status_code=404, detail="Archive not found")
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")


@router.post("/import-sets/{import_set_id}/scan", response_model=ImportSetSummaryOut)
def scan_import_set(
    import_set_id: int,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ImportSetSummaryOut:
    try:
        return _summary_out(imports.scan_import_set(user, import_set_id))
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")


@router.post("/import-sets/{import_set_id}/import", response_model=ArchiveImportResultOut)
def import_archive_set(
    import_set_id: int,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ArchiveImportResultOut:
    try:
        return _result_out(imports.import_set(user, import_set_id))
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")


@router.get("/import-sets/{import_set_id}/summary", response_model=ImportSetSummaryOut)
def get_summary(
    import_set_id: int,
    imports: ArchiveImportUseCases = Depends(get_archive_import_use_cases),
    user: User = Depends(current_user),
) -> ImportSetSummaryOut:
    try:
        return _summary_out(imports.get_summary(user, import_set_id))
    except ArchiveImportSetNotFound:
        raise HTTPException(status_code=404, detail="Import set not found")
