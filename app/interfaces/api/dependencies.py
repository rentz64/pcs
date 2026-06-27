from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.auth_use_cases import AuthUseCases
from app.application.blog_use_cases import BlogPostUseCases
from app.application.content_use_cases import ContentUseCases
from app.domain.entities import User
from app.domain.errors import InvalidToken, UnknownUser
from app.infrastructure.db.repositories import (
    SqlAlchemyAuditRepository,
    SqlAlchemyBlogPostRepository,
    SqlAlchemyContentRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.security.password import Pbkdf2PasswordHasher
from app.infrastructure.security.tokens import HmacTokenService
from app.infrastructure.storage.local import LocalObjectStorage

bearer = HTTPBearer()
storage = LocalObjectStorage()


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


def get_password_hasher() -> Pbkdf2PasswordHasher:
    return Pbkdf2PasswordHasher()


def get_token_service() -> HmacTokenService:
    return HmacTokenService()


def get_storage() -> LocalObjectStorage:
    return storage


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
