from app.config import settings


def build_cors_origins() -> list[str]:
    configured = [
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ]

    # Keep local development working exactly as before.
    for local_origin in (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ):
        if local_origin not in configured:
            configured.append(local_origin)

    return configured
