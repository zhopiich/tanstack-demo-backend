import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


class InvalidTokenError(Exception):
    pass


def create_access_token(
    *,
    claims: dict[str, Any],
    secret_key: str,
    algorithm: str,
    expires_in_seconds: int,
    now: int | None = None,
) -> str:
    if algorithm != "HS256":
        raise ValueError("Only HS256 is supported")

    issued_at = int(time.time()) if now is None else now
    payload = claims | {"iat": issued_at, "exp": issued_at + expires_in_seconds}
    header = {"alg": algorithm, "typ": "JWT"}
    signing_input = f"{_base64url_json(header)}.{_base64url_json(payload)}".encode(
        "ascii"
    )
    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{signing_input.decode('ascii')}.{_base64url_encode(signature)}"


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str,
    now: int | None = None,
) -> dict[str, Any]:
    if algorithm != "HS256":
        raise InvalidTokenError("Unsupported token algorithm")

    try:
        header_text, payload_text, signature_text = token.split(".")
        header = json.loads(_base64url_decode(header_text))
        payload = json.loads(_base64url_decode(payload_text))
    except ValueError, json.JSONDecodeError:
        raise InvalidTokenError("Invalid token") from None

    if header.get("alg") != algorithm or header.get("typ") != "JWT":
        raise InvalidTokenError("Invalid token")

    signing_input = f"{header_text}.{payload_text}".encode("ascii")
    expected_signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    actual_signature = _base64url_decode(signature_text)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise InvalidTokenError("Invalid token")

    current_time = int(time.time()) if now is None else now
    if int(payload.get("exp", 0)) < current_time:
        raise InvalidTokenError("Invalid token")

    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _base64url_json(value: dict[str, Any]) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(payload)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
