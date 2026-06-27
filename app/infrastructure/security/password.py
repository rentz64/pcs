import base64
import hashlib
import hmac


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def hash_password(password: str, salt: str = "pcs-local-salt") -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${_b64(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    actual = hash_password(password, salt).split("$", 2)[2]
    return hmac.compare_digest(actual, expected)


class Pbkdf2PasswordHasher:
    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return verify_password(password, password_hash)
