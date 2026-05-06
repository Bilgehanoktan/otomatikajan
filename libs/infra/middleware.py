from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from libs.config import ALLOWED_HEADERS, ALLOWED_METHODS, ALLOWED_ORIGINS, APP_ENV
from services.observability.logging import RequestTracingMiddleware


def configure_middleware(app: FastAPI) -> None:
    # Request tracing first so all downstream handlers inherit trace/system headers.
    app.add_middleware(RequestTracingMiddleware)

    allow_origins = ALLOWED_ORIGINS

    if APP_ENV == "production":
        allow_origins = [origin for origin in allow_origins if origin != "*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
        max_age=3600,
    )
