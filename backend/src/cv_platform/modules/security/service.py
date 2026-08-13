import hashlib
import hmac
import secrets
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from time import monotonic
from uuid import UUID, uuid4


class UserRole(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    username: str
    role: UserRole
    password_salt: bytes
    password_hash: bytes
    enabled: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Session:
    token: str
    user_id: UUID
    username: str
    role: UserRole
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuditEvent:
    timestamp: datetime
    actor: str
    method: str
    path: str
    status_code: int
    request_id: str


class LocalAuthService:
    def __init__(self, username: str, password: str, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._users: dict[UUID, User] = {}
        self._by_username: dict[str, UUID] = {}
        self._sessions: dict[str, Session] = {}
        self._lock = RLock()
        self.create_user(username, password, UserRole.ADMIN)

    def create_user(self, username: str, password: str, role: UserRole) -> User:
        normalized = username.strip().lower()
        if not normalized or len(normalized) > 128:
            raise ValueError("invalid username")
        if len(password) < 12:
            raise ValueError("password must contain at least 12 characters")
        with self._lock:
            if normalized in self._by_username:
                raise ValueError("username already exists")
            salt = secrets.token_bytes(16)
            user = User(
                id=uuid4(),
                username=normalized,
                role=role,
                password_salt=salt,
                password_hash=self._derive(password, salt),
                enabled=True,
                created_at=datetime.now(UTC),
            )
            self._users[user.id] = user
            self._by_username[user.username] = user.id
            return user

    def list_users(self) -> list[User]:
        with self._lock:
            return sorted(self._users.values(), key=lambda item: item.created_at)

    def find_by_username(self, username: str) -> User | None:
        normalized = username.strip().lower()
        with self._lock:
            user_id = self._by_username.get(normalized)
            return self._users.get(user_id) if user_id else None

    def update_user(
        self,
        user_id: UUID,
        *,
        role: UserRole | None = None,
        enabled: bool | None = None,
    ) -> User:
        from dataclasses import replace

        with self._lock:
            user = self._users.get(user_id)
            if user is None:
                raise ValueError("user does not exist")
            updated = replace(
                user,
                role=role or user.role,
                enabled=user.enabled if enabled is None else enabled,
            )
            self._users[user_id] = updated
            if not updated.enabled:
                self._sessions = {
                    token: session
                    for token, session in self._sessions.items()
                    if session.user_id != user_id
                }
            return updated

    @property
    def initial_admin_id(self) -> UUID:
        with self._lock:
            return next(iter(self._users))

    def login(self, username: str, password: str) -> Session | None:
        with self._lock:
            user_id = self._by_username.get(username.strip().lower())
            user = self._users.get(user_id) if user_id else None
        if (
            user is None
            or not user.enabled
            or not hmac.compare_digest(
                user.password_hash,
                self._derive(password, user.password_salt),
            )
        ):
            return None
        session = Session(
            token=secrets.token_urlsafe(32),
            user_id=user.id,
            username=user.username,
            role=user.role,
            expires_at=datetime.now(UTC) + timedelta(seconds=self._ttl),
        )
        with self._lock:
            self._sessions[session.token] = session
        return session

    def authenticate(self, token: str | None) -> Session | None:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            user = self._users.get(session.user_id) if session else None
            if session and user and user.enabled and session.expires_at > datetime.now(UTC):
                return session
            self._sessions.pop(token, None)
        return None

    def logout(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    @staticmethod
    def _derive(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
        )


class InMemoryAuditLog:
    def __init__(self, capacity: int = 10_000) -> None:
        self._events: deque[AuditEvent] = deque(maxlen=capacity)
        self._lock = RLock()

    def add(self, event: AuditEvent) -> None:
        with self._lock:
            self._events.appendleft(event)

    def list(self, limit: int = 200) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)[: min(max(limit, 1), 1000)]


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = RLock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= now - self._window:
                requests.popleft()
            if len(requests) >= self._limit:
                return False
            requests.append(now)
            return True
