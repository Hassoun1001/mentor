"""Single-user authentication.

The plan calls out exactly this shape in §6.I and §14:

> One protected login; all API keys held server-side, never in the browser.
> Single protected login; all API keys and secrets server-side; nothing
> sensitive in the browser or in URLs.

Implementation:

- Username + password verified against a bcrypt hash from settings.
- On success we mint a signed JWT (HS256) with a fixed TTL.
- Middleware verifies the JWT on every protected request.

The constant-time string compare on the username is deliberate. A
timing-attack on a single-user system is academic, but the cost of
doing it right is two lines.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

import bcrypt
from jose import JWTError, jwt

from mentor.config import Settings

_ALGO: Final = "HS256"
_ISSUER: Final = "mentor"


def _prehash(password: str) -> bytes:
    """SHA-256 → base64 the password before bcrypt.

    bcrypt silently truncates input at 72 bytes (and modern bcrypt raises
    on longer input). Pre-hashing to a fixed 44-byte base64 digest removes
    the length ceiling and the null-byte truncation footgun — the standard
    mitigation used by, e.g., Dropbox. The digest is well under 72 bytes.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(plaintext: str) -> str:
    hashed = bcrypt.hashpw(_prehash(plaintext), bcrypt.gensalt())
    return hashed.decode("ascii")


def _verify_password(plaintext: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(plaintext), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


class AuthError(Exception):
    """Raised when authentication or token verification fails."""


@dataclass(frozen=True, slots=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class TokenClaims:
    subject: str
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class IssuedToken:
    access_token: str
    expires_at: datetime
    token_type: str = "bearer"  # noqa: S105 — OAuth token-type literal, not a secret


class AuthService:
    """Single-tenant auth — no user table, just settings + JWT."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def login(self, credentials: Credentials) -> IssuedToken:
        if not self._settings.auth_password_hash:
            raise AuthError(
                "auth not configured — set MENTOR_AUTH_PASSWORD_HASH "
                "(generate via `python -m mentor.cli.hash_password`)."
            )
        # Constant-time compare on the username so failed lookups don't leak timing.
        if not hmac.compare_digest(
            credentials.username.encode("utf-8"),
            self._settings.auth_username.encode("utf-8"),
        ):
            raise AuthError("invalid credentials")
        if not _verify_password(credentials.password, self._settings.auth_password_hash):
            raise AuthError("invalid credentials")
        return self._issue_token()

    def verify(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret.get_secret_value(),
                algorithms=[_ALGO],
                issuer=_ISSUER,
            )
        except JWTError as exc:
            raise AuthError("invalid or expired token") from exc

        subject = payload.get("sub")
        iat = payload.get("iat")
        exp = payload.get("exp")
        if not subject or not iat or not exp:
            raise AuthError("malformed token payload")
        return TokenClaims(
            subject=str(subject),
            issued_at=datetime.fromtimestamp(int(iat), tz=UTC),
            expires_at=datetime.fromtimestamp(int(exp), tz=UTC),
        )

    def _issue_token(self) -> IssuedToken:
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self._settings.jwt_ttl_hours)
        payload = {
            "iss": _ISSUER,
            "sub": self._settings.auth_username,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        token = jwt.encode(
            payload,
            self._settings.jwt_secret.get_secret_value(),
            algorithm=_ALGO,
        )
        return IssuedToken(access_token=token, expires_at=expires_at)
