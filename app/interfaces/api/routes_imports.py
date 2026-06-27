from fastapi import APIRouter, Depends, HTTPException

from app.application.dto import CreateImportJobCommand, RegisterExternalAccountCommand, RegisterExternalSourceCommand
from app.application.import_use_cases import ImportUseCases
from app.domain.entities import User
from app.domain.errors import ExternalAccountNotFound, ExternalSourceNotFound, ImportAdapterNotFound, ImportJobNotFound
from app.domain.imports import ExternalAccount, ExternalSource, ImportJob
from app.interfaces.api.dependencies import current_user, get_import_use_cases
from app.interfaces.api.schemas import (
    ContentTypesOut,
    ExternalAccountCreate,
    ExternalAccountOut,
    ExternalSourceCreate,
    ExternalSourceOut,
    ImportJobCreate,
    ImportJobOut,
)

router = APIRouter(prefix="/imports")


def _source_out(source: ExternalSource) -> ExternalSourceOut:
    return ExternalSourceOut(id=source.id, name=source.name, source_type=source.source_type, created_at=source.created_at)


def _account_out(account: ExternalAccount) -> ExternalAccountOut:
    return ExternalAccountOut(
        id=account.id,
        source_id=account.source_id,
        name=account.name,
        external_account_ref=account.external_account_ref,
        created_at=account.created_at,
    )


def _job_out(job: ImportJob) -> ImportJobOut:
    return ImportJobOut(
        id=job.id,
        source_id=job.source_id,
        account_id=job.account_id,
        content_types=list(job.content_types),
        status=job.status.value,
        imported_count=job.imported_count,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/sources", response_model=ExternalSourceOut)
def register_source(
    payload: ExternalSourceCreate,
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> ExternalSourceOut:
    return _source_out(imports.register_source_command(user, RegisterExternalSourceCommand(payload.name, payload.source_type)))


@router.get("/sources", response_model=list[ExternalSourceOut])
def list_sources(
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> list[ExternalSourceOut]:
    return [_source_out(source) for source in imports.list_sources(user)]


@router.post("/accounts", response_model=ExternalAccountOut)
def register_account(
    payload: ExternalAccountCreate,
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> ExternalAccountOut:
    try:
        return _account_out(
            imports.register_account_command(
                user,
                RegisterExternalAccountCommand(payload.source_id, payload.name, payload.external_account_ref),
            )
        )
    except ExternalSourceNotFound:
        raise HTTPException(status_code=404, detail="External source not found")


@router.get("/accounts", response_model=list[ExternalAccountOut])
def list_accounts(
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> list[ExternalAccountOut]:
    return [_account_out(account) for account in imports.list_accounts(user)]


@router.get("/sources/{source_id}/content-types", response_model=ContentTypesOut)
def list_source_content_types(
    source_id: int,
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> ContentTypesOut:
    try:
        return ContentTypesOut(content_types=list(imports.list_supported_content_types(user, source_id)))
    except ExternalSourceNotFound:
        raise HTTPException(status_code=404, detail="External source not found")
    except ImportAdapterNotFound:
        raise HTTPException(status_code=404, detail="Import adapter not found")


@router.post("/jobs", response_model=ImportJobOut)
def create_and_execute_job(
    payload: ImportJobCreate,
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> ImportJobOut:
    try:
        job = imports.create_import_job_command(
            user,
            CreateImportJobCommand(payload.source_id, payload.account_id, tuple(payload.content_types)),
        )
        return _job_out(imports.execute_import_job(user, job.id))
    except ExternalSourceNotFound:
        raise HTTPException(status_code=404, detail="External source not found")
    except ExternalAccountNotFound:
        raise HTTPException(status_code=404, detail="External account not found")
    except ImportAdapterNotFound:
        raise HTTPException(status_code=404, detail="Import adapter not found")


@router.get("/jobs", response_model=list[ImportJobOut])
def list_jobs(
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> list[ImportJobOut]:
    return [_job_out(job) for job in imports.list_import_jobs(user)]


@router.get("/jobs/{job_id}", response_model=ImportJobOut)
def get_job(
    job_id: int,
    imports: ImportUseCases = Depends(get_import_use_cases),
    user: User = Depends(current_user),
) -> ImportJobOut:
    try:
        return _job_out(imports.get_import_job_status(user, job_id))
    except ImportJobNotFound:
        raise HTTPException(status_code=404, detail="Import job not found")
