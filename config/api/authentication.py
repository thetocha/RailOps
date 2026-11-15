from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    """Session cookie auth that returns 401 (not 403) when no session is present."""

    def authenticate_header(self, request: object) -> str:
        return "Session"
