from app.domain.auth import AuthUser as DomainAuthUser
from app.schemas.auth import AuthUser


def to_auth_user_schema(user: DomainAuthUser) -> AuthUser:
    return AuthUser(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value,
    )
