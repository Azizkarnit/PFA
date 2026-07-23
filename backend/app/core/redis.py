import redis
import time
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


class InMemoryRedisMock:
    """
    Fallback in-memory store used when Redis is unavailable.
    NOTE: This is NOT safe across multiple worker processes. It is intended
    only for single-process development/testing scenarios where Redis is absent.
    """
    def __init__(self):
        self.store = {}
        self.expiries = {}

    def _is_expired(self, key):
        if key in self.expiries:
            if time.time() > self.expiries[key]:
                self.delete(key)
                return True
        return False

    def exists(self, key):
        if self._is_expired(key):
            return 0
        return 1 if key in self.store else 0

    def delete(self, key):
        self.store.pop(key, None)
        self.expiries.pop(key, None)
        return 1

    def expire(self, key, seconds):
        if key in self.store:
            self.expiries[key] = time.time() + seconds
            return True
        return False

    def hset(self, key, mapping):
        self.store[key] = dict(mapping)
        return len(mapping)

    def hgetall(self, key):
        if self._is_expired(key):
            return {}
        return self.store.get(key, {})

    def hincrby(self, key, field, amount):
        if self._is_expired(key):
            return 0
        if key not in self.store:
            self.store[key] = {}
        val = int(self.store[key].get(field, 0)) + amount
        self.store[key][field] = str(val)
        return val

    def setex(self, key, seconds, value):
        self.store[key] = str(value)
        self.expiries[key] = time.time() + seconds
        return True

    def get(self, key):
        if self._is_expired(key):
            return None
        return self.store.get(key)

    def incr(self, key):
        if self._is_expired(key):
            self.store[key] = "0"
        val = int(self.store.get(key, 0)) + 1
        self.store[key] = str(val)
        return val

    def keys(self, pattern="*"):
        import fnmatch
        return [k for k in self.store.keys() if not self._is_expired(k) and fnmatch.fnmatch(k, pattern)]

    def ttl(self, key):
        if self._is_expired(key) or key not in self.store:
            return -2
        if key not in self.expiries:
            return -1
        return int(self.expiries[key] - time.time())


_use_mock = False
_mock_client = None


def get_redis_client():
    global _use_mock, _mock_client
    if _use_mock:
        if not _mock_client:
            _mock_client = InMemoryRedisMock()
        return _mock_client
    try:
        client = redis.Redis(connection_pool=redis_pool)
        client.ping()
        return client
    except Exception as e:
        logger.warning(
            f"Failed to connect to Redis at {settings.REDIS_URL} (error: {e}). "
            "Falling back to InMemory storage. NOTE: This is NOT safe for multi-process deployments."
        )
        _use_mock = True
        _mock_client = InMemoryRedisMock()
        return _mock_client


# ── OTP ───────────────────────────────────────────────────────────────────────

def set_otp(user_id: int, code: str, expiration_minutes: int):
    """Stores OTP code in Redis with attempts counter. Expires after expiration_minutes."""
    client = get_redis_client()
    key = f"otp:{user_id}"
    client.hset(key, mapping={"code": code, "attempts": 0})
    client.expire(key, expiration_minutes * 60)


def get_otp(user_id: int):
    """Retrieves OTP info. Returns dict with 'code' and 'attempts' or None."""
    client = get_redis_client()
    key = f"otp:{user_id}"
    result = client.hgetall(key)
    if not result:
        return None
    return {"code": result.get("code"), "attempts": int(result.get("attempts", 0))}


def increment_otp_attempts(user_id: int):
    """Increments the attempt counter for an OTP."""
    client = get_redis_client()
    key = f"otp:{user_id}"
    if client.exists(key):
        return client.hincrby(key, "attempts", 1)
    return 0


def delete_otp(user_id: int):
    """Deletes an OTP from Redis."""
    client = get_redis_client()
    key = f"otp:{user_id}"
    client.delete(key)


# ── Password Reset ─────────────────────────────────────────────────────────────

def set_reset_token(token: str, user_id: int):
    """Stores a password reset token mapped to user_id. Expires in 1 hour."""
    client = get_redis_client()
    key = f"pwd_reset:{token}"
    client.setex(key, 3600, user_id)  # 1 hour = 3600s


def get_reset_token(token: str) -> int | None:
    """Returns user_id if token is valid, else None."""
    client = get_redis_client()
    key = f"pwd_reset:{token}"
    user_id = client.get(key)
    return int(user_id) if user_id else None


def delete_reset_token(token: str):
    """Deletes a password reset token."""
    client = get_redis_client()
    key = f"pwd_reset:{token}"
    client.delete(key)


# ── JWT Blacklist ─────────────────────────────────────────────────────────────

def blacklist_token(jti: str, ttl_seconds: int):
    """Adds a JWT ID (jti) to the blacklist. Expires when the token would have expired."""
    client = get_redis_client()
    key = f"blacklist:{jti}"
    client.setex(key, ttl_seconds, 1)


def is_blacklisted(jti: str) -> bool:
    """Checks if a JWT ID is blacklisted (i.e. the token has been logged out)."""
    client = get_redis_client()
    key = f"blacklist:{jti}"
    return bool(client.exists(key))


# ── Rate Limiting ─────────────────────────────────────────────────────────────

def increment_rate_limit(ip: str, window_minutes: int = 15) -> int:
    """Increments and returns login attempts from an IP within the window."""
    client = get_redis_client()
    key = f"rate_limit:{ip}"
    count = client.incr(key)
    if count == 1:
        client.expire(key, window_minutes * 60)
    return count


# ── Account Lock ──────────────────────────────────────────────────────────────

def set_account_lock(user_id: int, lock_hours: int):
    """Locks a user account for a specific duration. Also records the original lock duration."""
    client = get_redis_client()
    lock_key = f"lock:{user_id}"
    meta_key = f"lock_meta:{user_id}"
    duration_seconds = lock_hours * 3600
    client.setex(lock_key, duration_seconds, 1)
    # Store original lock duration so we can compute "locked since" accurately
    client.setex(meta_key, duration_seconds, duration_seconds)


def is_account_locked(user_id: int) -> bool:
    """Checks if a user account is locked in Redis."""
    client = get_redis_client()
    key = f"lock:{user_id}"
    return bool(client.exists(key))


def clear_account_lock(user_id: int):
    """Clears the Redis lock for a user."""
    client = get_redis_client()
    client.delete(f"lock:{user_id}")
    client.delete(f"lock_meta:{user_id}")


def get_all_locked_accounts() -> list[dict]:
    """Retrieves all locked user accounts from Redis with correct lock timing."""
    client = get_redis_client()
    keys = client.keys("lock:*")
    results = []
    for key in keys:
        try:
            user_id = int(key.split(":")[1])
            ttl_seconds = client.ttl(key)
            if ttl_seconds > 0:
                # Retrieve the original lock duration so UI shows correct "locked since"
                meta_key = f"lock_meta:{user_id}"
                duration_val = client.get(meta_key)
                original_duration = int(duration_val) if duration_val else ttl_seconds
                results.append({
                    "user_id": user_id,
                    "ttl": ttl_seconds,
                    "duration": original_duration
                })
        except Exception as e:
            logger.warning(f"Error parsing lock key {key}: {e}")
            continue
    return results


# ── OTP Resends ───────────────────────────────────────────────────────────────

def increment_otp_resends(user_id: int) -> int:
    """Increments the count of OTP resends for a user (24-hour window)."""
    client = get_redis_client()
    key = f"otp_resends:{user_id}"
    count = client.incr(key)
    if count == 1:
        client.expire(key, 24 * 3600)  # 24 hours
    return count


def get_otp_resends(user_id: int) -> int:
    """Returns the count of OTP resends for a user in the last 24 hours."""
    client = get_redis_client()
    key = f"otp_resends:{user_id}"
    val = client.get(key)
    return int(val) if val else 0
