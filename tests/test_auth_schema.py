from app.schemas.auth import AuthResponse, AuthUser


def test_auth_response_uses_access_token_contract() -> None:
    response = AuthResponse(
        user=AuthUser(
            id="c000000000000000000000001",
            name="Demo Reviewer",
            email="reviewer@example.com",
            role="reviewer",
        ),
        accessToken="header.payload.signature",
        tokenType="Bearer",
        expiresIn=900,
    )

    assert response.model_dump(mode="json") == {
        "user": {
            "id": "c000000000000000000000001",
            "name": "Demo Reviewer",
            "email": "reviewer@example.com",
            "role": "reviewer",
        },
        "accessToken": "header.payload.signature",
        "tokenType": "Bearer",
        "expiresIn": 900,
    }


def test_auth_response_rejects_old_token_field() -> None:
    fields = AuthResponse.model_fields

    assert "token" not in fields
    assert {"user", "accessToken", "tokenType", "expiresIn"}.issubset(fields)
