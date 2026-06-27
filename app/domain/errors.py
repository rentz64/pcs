class DomainError(Exception):
    """Base error for application/domain failures."""


class InvalidCredentials(DomainError):
    pass


class InvalidToken(DomainError):
    pass


class UnknownUser(DomainError):
    pass


class ContentNotFound(DomainError):
    pass


class StoredObjectNotFound(DomainError):
    pass

