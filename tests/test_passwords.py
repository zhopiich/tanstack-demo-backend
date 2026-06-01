from app.core.passwords import hash_password, verify_password


def test_hash_password_uses_pbkdf2_format() -> None:
    password_hash = hash_password("password123", salt=b"0123456789abcdef")

    assert password_hash.startswith("pbkdf2_sha256$600000$")
    assert verify_password("password123", password_hash) is True


def test_hash_password_accepts_configured_iterations() -> None:
    password_hash = hash_password(
        "password123",
        salt=b"0123456789abcdef",
        iterations=100,
    )

    assert password_hash.startswith("pbkdf2_sha256$100$")
    assert verify_password("password123", password_hash) is True


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password("password123", salt=b"0123456789abcdef")

    assert verify_password("wrongpass", password_hash) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("password123", "not-a-valid-hash") is False
