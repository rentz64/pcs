from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.auth_use_cases import AuthUseCases
from app.application.blog_use_cases import BlogPostUseCases
from app.application.content_use_cases import ContentUseCases
from app.application.import_use_cases import ImportUseCases
from app.application.job_use_cases import JobUseCases
from app.application.email_use_cases import EmailUseCases
from app.application.media_use_cases import MediaUseCases
from app.application.travel_use_cases import TravelUseCases
from app.domain.entities import User
from app.domain.errors import InvalidToken, UnknownUser
from app.infrastructure.db.repositories import (
    SqlAlchemyAuditRepository,
    SqlAlchemyBlogPostRepository,
    SqlAlchemyContentRepository,
    SqlAlchemyExternalAccountRepository,
    SqlAlchemyExternalSourceRepository,
    SqlAlchemyEmailRepository,
    SqlAlchemyImportBatchRepository,
    SqlAlchemyImportJobRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyMediaRepository,
    SqlAlchemyTravelRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.events import InProcessEventPublisher
from app.domain.tasks import TaskRegistry, build_default_task_registry
from app.infrastructure.imports.local_dummy import LocalDummyImportAdapter
from app.infrastructure.imports.fake_email import FakeEmailImportAdapter
from app.infrastructure.db.session import get_db
from app.infrastructure.security.password import Pbkdf2PasswordHasher
from app.infrastructure.security.tokens import HmacTokenService
from app.infrastructure.storage.local import LocalObjectStorage

bearer = HTTPBearer()
storage = LocalObjectStorage()
events = InProcessEventPublisher()
task_registry = build_default_task_registry()


def get_db_session():
    yield from get_db()


def get_user_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_content_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyContentRepository:
    return SqlAlchemyContentRepository(db)


def get_blog_post_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyBlogPostRepository:
    return SqlAlchemyBlogPostRepository(db)


def get_audit_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyAuditRepository:
    return SqlAlchemyAuditRepository(db)


def get_media_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyMediaRepository:
    return SqlAlchemyMediaRepository(db)


def get_email_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyEmailRepository:
    return SqlAlchemyEmailRepository(db)


def get_travel_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyTravelRepository:
    return SqlAlchemyTravelRepository(db)


def get_external_source_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyExternalSourceRepository:
    return SqlAlchemyExternalSourceRepository(db)


def get_external_account_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyExternalAccountRepository:
    return SqlAlchemyExternalAccountRepository(db)


def get_import_job_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyImportJobRepository:
    return SqlAlchemyImportJobRepository(db)


def get_import_batch_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyImportBatchRepository:
    return SqlAlchemyImportBatchRepository(db)


def get_job_repository(db: Session = Depends(get_db_session)) -> SqlAlchemyJobRepository:
    return SqlAlchemyJobRepository(db)


def get_password_hasher() -> Pbkdf2PasswordHasher:
    return Pbkdf2PasswordHasher()


def get_token_service() -> HmacTokenService:
    return HmacTokenService()


def get_storage() -> LocalObjectStorage:
    return storage


def get_event_publisher() -> InProcessEventPublisher:
    return events


def get_task_registry() -> TaskRegistry:
    return task_registry


def get_auth_use_cases(
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
    passwords: Pbkdf2PasswordHasher = Depends(get_password_hasher),
    tokens: HmacTokenService = Depends(get_token_service),
) -> AuthUseCases:
    return AuthUseCases(users, audits, passwords, tokens)


def get_content_use_cases(
    content: SqlAlchemyContentRepository = Depends(get_content_repository),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
    object_storage: LocalObjectStorage = Depends(get_storage),
) -> ContentUseCases:
    return ContentUseCases(content, audits, object_storage)


def get_blog_post_use_cases(
    blog_posts: SqlAlchemyBlogPostRepository = Depends(get_blog_post_repository),
    content: SqlAlchemyContentRepository = Depends(get_content_repository),
) -> BlogPostUseCases:
    return BlogPostUseCases(blog_posts, content)


def get_import_use_cases(
    sources: SqlAlchemyExternalSourceRepository = Depends(get_external_source_repository),
    accounts: SqlAlchemyExternalAccountRepository = Depends(get_external_account_repository),
    jobs: SqlAlchemyImportJobRepository = Depends(get_import_job_repository),
    batches: SqlAlchemyImportBatchRepository = Depends(get_import_batch_repository),
    content: SqlAlchemyContentRepository = Depends(get_content_repository),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
) -> ImportUseCases:
    return ImportUseCases(
        sources,
        accounts,
        jobs,
        batches,
        content,
        audits,
        adapters={"local": LocalDummyImportAdapter()},
    )


def get_media_use_cases(
    media: SqlAlchemyMediaRepository = Depends(get_media_repository),
    content: SqlAlchemyContentRepository = Depends(get_content_repository),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
    object_storage: LocalObjectStorage = Depends(get_storage),
) -> MediaUseCases:
    return MediaUseCases(media, content, audits, object_storage)


def get_email_use_cases(
    emails: SqlAlchemyEmailRepository = Depends(get_email_repository),
    content: SqlAlchemyContentRepository = Depends(get_content_repository),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
    object_storage: LocalObjectStorage = Depends(get_storage),
) -> EmailUseCases:
    return EmailUseCases(emails, content, audits, object_storage)


def get_travel_use_cases(
    travel: SqlAlchemyTravelRepository = Depends(get_travel_repository),
    content: SqlAlchemyContentRepository = Depends(get_content_repository),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
) -> TravelUseCases:
    return TravelUseCases(travel, content, audits)


def get_job_use_cases(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    event_publisher: InProcessEventPublisher = Depends(get_event_publisher),
    audits: SqlAlchemyAuditRepository = Depends(get_audit_repository),
    tasks: TaskRegistry = Depends(get_task_registry),
) -> JobUseCases:
    return JobUseCases(jobs, event_publisher, tasks, audits)


def get_fake_email_adapter() -> FakeEmailImportAdapter:
    return FakeEmailImportAdapter()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    auth: AuthUseCases = Depends(get_auth_use_cases),
) -> User:
    try:
        return auth.current_user_from_token(credentials.credentials)
    except InvalidToken:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except UnknownUser:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
