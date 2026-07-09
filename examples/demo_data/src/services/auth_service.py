"""Authentication service module."""


class AuthService:
    def __init__(self) -> None:
        self._valid_tokens = {"demo-token": "user_123"}

    def authenticate_user(self, token: str) -> bool:
        return token in self._valid_tokens


def authenticate_user(token: str) -> bool:
    """Standalone helper for search demo."""
    service = AuthService()
    return service.authenticate_user(token)
