from app.domain.entities import AuditEntry, User
from app.domain.errors import InvalidCredentials, InvalidToken, UnknownUser
from app.domain.repositories import AuditRepository, PasswordHasher, TokenService, UserRepository


class AuthUseCases:
    def __init__(
        self,
        users: UserRepository,
        audits: AuditRepository,
        passwords: PasswordHasher,
        tokens: TokenService,
    ):
        self.users = users
        self.audits = audits
        self.passwords = passwords
        self.tokens = tokens

    def login(self, username: str, password: str) -> str:
        user = self.users.get_by_username(username)
        if not user or not self.passwords.verify(password, user.password_hash):
            raise InvalidCredentials()
        self.audits.add(AuditEntry(id=None, user_id=user.id, action="login", entity_type="user", entity_id=str(user.id)))
        return self.tokens.create(user.username)

    def current_user_from_token(self, token: str) -> User:
        username = self.tokens.decode_username(token)
        if not username:
            raise InvalidToken()
        user = self.users.get_by_username(username)
        if not user:
            raise UnknownUser()
        return user

