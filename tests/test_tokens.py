import pytest

from app.core.tokens import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)


def test_create_and_decode_access_token() -> None:
    token = create_access_token(
        claims={
            "sub": "c000000000000000000000001",
            "email": "reviewer@example.com",
            "name": "Demo Reviewer",
            "role": "reviewer",
        },
        secret_key="test-secret",
        algorithm="HS256",
        expires_in_seconds=900,
        now=1_000,
    )

    claims = decode_access_token(
        token,
        secret_key="test-secret",
        algorithm="HS256",
        now=1_100,
    )

    assert claims["sub"] == "c000000000000000000000001"
    assert claims["email"] == "reviewer@example.com"
    assert claims["name"] == "Demo Reviewer"
    assert claims["role"] == "reviewer"
    assert claims["iat"] == 1_000
    assert claims["exp"] == 1_900


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        claims={
            "sub": "c000000000000000000000001",
            "email": "reviewer@example.com",
            "name": "Demo Reviewer",
            "role": "reviewer",
        },
        secret_key="test-secret",
        algorithm="HS256",
        expires_in_seconds=900,
        now=1_000,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(
            token,
            secret_key="test-secret",
            algorithm="HS256",
            now=1_901,
        )


def test_decode_access_token_rejects_bad_signature() -> None:
    token = create_access_token(
        claims={
            "sub": "c000000000000000000000001",
            "email": "reviewer@example.com",
            "name": "Demo Reviewer",
            "role": "reviewer",
        },
        secret_key="test-secret",
        algorithm="HS256",
        expires_in_seconds=900,
        now=1_000,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(
            token,
            secret_key="wrong-secret",
            algorithm="HS256",
            now=1_100,
        )


def test_refresh_token_generation_and_hashing() -> None:
    token = generate_refresh_token()

    assert isinstance(token, str)
    assert len(token) >= 32
    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != hash_refresh_token(token + "x")
