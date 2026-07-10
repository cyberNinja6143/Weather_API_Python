"""Unit tests for services/auth.py — password hashing and JWT token operations.

Run standalone:  python tests/test_auth_service.py
"""

import sys
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import jwt
import pytest
from fastapi import HTTPException

from services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    """Hashing a plaintext password and verifying it returns True."""
    plain = "secure-p4ss!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_create_access_token_is_valid_jwt() -> None:
    """Token is a non-empty string that starts with the JWT header."""
    token = create_access_token("alice")
    assert isinstance(token, str)
    assert token.startswith("eyJ")


def test_decode_valid_token_returns_username() -> None:
    """Round-trip: create a token for 'alice', decode it, assert sub matches."""
    token = create_access_token("alice")
    username = decode_access_token(token)
    assert username == "alice"


def test_decode_expired_token_raises_401() -> None:
    """A token with an expiry in the past must raise HTTPException(401)."""
    from services.auth import JWT_ALGORITHM, JWT_SECRET
    from datetime import datetime, timezone

    payload = {"sub": "alice", "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}
    expired = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        decode_access_token(expired)
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_decode_tampered_token_raises_401() -> None:
    """Modifying the token payload must result in a 401 invalid-token error."""
    token = create_access_token("alice")
    # Flip one character in the payload portion.
    parts = token.split(".")
    parts[1] = parts[1][:-1] + ("Z" if parts[1][-1] != "Z" else "A")
    tampered = ".".join(parts)
    with pytest.raises(HTTPException) as exc:
        decode_access_token(tampered)
    assert exc.value.status_code == 401


# -- standalone runner ----------------------------------------------------------

def _run(name: str, fn) -> None:
    print(f"\n=== {name} ===")
    try:
        fn()
        print("PASS")
    except Exception as exc:
        print(f"FAIL: {exc}")


if __name__ == "__main__":
    print("Running auth service tests...\n")
    _run("test_hash_and_verify_password", test_hash_and_verify_password)
    _run("test_create_access_token_is_valid_jwt", test_create_access_token_is_valid_jwt)
    _run("test_decode_valid_token_returns_username", test_decode_valid_token_returns_username)
    _run("test_decode_expired_token_raises_401", test_decode_expired_token_raises_401)
    _run("test_decode_tampered_token_raises_401", test_decode_tampered_token_raises_401)
    print("\nAuth service tests completed.")
