from app.schemas.auth import AuthUser

DEMO_TOKEN = "dev-reviewer-token"
DEMO_PASSWORD = "password123"
DEMO_USER = AuthUser(
    id="c000000000000000000000001",
    name="Demo Reviewer",
    email="reviewer@example.com",
    role="reviewer",
)


class AuthService:
    def login(self, email: str, password: str) -> tuple[str, AuthUser] | None:
        if email == DEMO_USER.email and password == DEMO_PASSWORD:
            return DEMO_TOKEN, DEMO_USER
        return None

    def get_user_for_token(self, token: str) -> AuthUser | None:
        if token == DEMO_TOKEN:
            return DEMO_USER
        return None
