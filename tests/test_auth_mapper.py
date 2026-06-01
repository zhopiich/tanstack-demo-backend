from datetime import UTC, datetime

from app.domain.auth import AuthRole, AuthUser
from app.mappers.auth_mapper import to_auth_user_schema


def test_to_auth_user_schema_maps_domain_user() -> None:
    user = AuthUser(
        id="c000000000000000000000001",
        name="Reviewer User",
        email="reviewer@example.com",
        role=AuthRole.REVIEWER,
        password_hash="hash",
        created_at=datetime(2026, 5, 29, 8, 0, tzinfo=UTC),
    )

    schema = to_auth_user_schema(user)

    assert schema.model_dump(mode="json") == {
        "id": "c000000000000000000000001",
        "name": "Reviewer User",
        "email": "reviewer@example.com",
        "role": "reviewer",
    }
