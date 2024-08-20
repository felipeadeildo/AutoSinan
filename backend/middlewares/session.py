from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        access_token = request.cookies.get("access_token")
        if access_token:
            request.scope["headers"] = [
                (k, v)
                for k, v in request.scope["headers"]
                if k.decode("latin-1").lower() != "authorization"
            ]

            request.scope["headers"].append(
                (
                    "authorization".encode("latin-1"),
                    f"Bearer {access_token}".encode("latin-1"),
                )
            )

        response = await call_next(request)
        return response
