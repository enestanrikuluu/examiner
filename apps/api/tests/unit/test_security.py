import uuid

import pytest

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    password = "s3cret-p@ss"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_access_token() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "student")
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "student"
    assert payload["type"] == "access"


def test_create_and_decode_refresh_token() -> None:
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token("invalid-token-string")


def test_access_token_contains_role() -> None:
    user_id = uuid.uuid4()
    for role in ["student", "instructor", "admin"]:
        token = create_access_token(user_id, role)
        payload = decode_token(token)
        assert payload["role"] == role
