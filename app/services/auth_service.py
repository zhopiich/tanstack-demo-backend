from app.schemas.auth import AuthUser

DEMO_PASSWORD = "password123"

DEMO_USERS_BY_EMAIL = {
    "reviewer@example.com": AuthUser(
        id="c000000000000000000000001",
        name="Demo Reviewer",
        email="reviewer@example.com",
        role="reviewer",
    ),
    "admin@example.com": AuthUser(
        id="c000000000000000000000002",
        name="Demo Admin",
        email="admin@example.com",
        role="admin",
    ),
}

DEMO_TOKENS_BY_EMAIL = {
    "reviewer@example.com": "dev-reviewer-token",
    "admin@example.com": "dev-admin-token",
}
DEMO_USERS_BY_TOKEN = {
    token: DEMO_USERS_BY_EMAIL[email] for email, token in DEMO_TOKENS_BY_EMAIL.items()
}


class AuthService:
    def login(self, email: str, password: str) -> tuple[str, AuthUser] | None:
        user = DEMO_USERS_BY_EMAIL.get(email)
        if user is not None and password == DEMO_PASSWORD:
            return DEMO_TOKENS_BY_EMAIL[email], user
        return None

    def get_user_for_token(self, token: str) -> AuthUser | None:
        return DEMO_USERS_BY_TOKEN.get(token)
