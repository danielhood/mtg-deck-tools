"""Serve configuration and uvicorn launcher for ``mtg-deck-tools serve``."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from mtg_deck_tools.paths import WEB_UI_DIST_DIR, resolve_static_ui_dir

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
SERVE_APP_FACTORY = "mtg_deck_tools.api.serve:create_serve_app"


@dataclass(frozen=True)
class ServeConfig:
    host: str
    port: int
    reload: bool
    static_dir: Path | None
    db_path: Path | None


def serve_config_from_options(
    *,
    host: str | None = None,
    port: int | None = None,
    reload: bool = False,
    with_ui: bool = False,
    ui_dir: Path | None = None,
    db_path: Path | None = None,
) -> ServeConfig:
    resolved_host = host or os.environ.get("MTG_SERVE_HOST", DEFAULT_HOST)
    env_port = os.environ.get("MTG_SERVE_PORT")
    resolved_port = port if port is not None else int(env_port) if env_port else DEFAULT_PORT

    static_dir: Path | None = None
    if with_ui or ui_dir is not None:
        static_dir = ui_dir or resolve_static_ui_dir() or WEB_UI_DIST_DIR

    return ServeConfig(
        host=resolved_host,
        port=resolved_port,
        reload=reload,
        static_dir=static_dir,
        db_path=db_path,
    )


def apply_serve_env(config: ServeConfig) -> None:
    if config.db_path is not None:
        os.environ["MTG_DB_PATH"] = str(config.db_path.resolve())
    if config.static_dir is not None:
        os.environ["MTG_SERVE_STATIC_DIR"] = str(config.static_dir.resolve())
    elif "MTG_SERVE_STATIC_DIR" in os.environ:
        del os.environ["MTG_SERVE_STATIC_DIR"]


def create_serve_app():
    """Uvicorn factory entrypoint (supports ``--reload``)."""
    from mtg_deck_tools.api.app import create_app

    return create_app(static_dir=resolve_static_ui_dir())


def run_server(config: ServeConfig) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            'HTTP server requires the [web] extra: pip install -e ".[web]"'
        ) from exc

    apply_serve_env(config)

    if config.reload:
        uvicorn.run(
            SERVE_APP_FACTORY,
            factory=True,
            host=config.host,
            port=config.port,
            reload=True,
        )
        return

    from mtg_deck_tools.api.app import create_app

    app = create_app(static_dir=config.static_dir)
    uvicorn.run(app, host=config.host, port=config.port, reload=False)
