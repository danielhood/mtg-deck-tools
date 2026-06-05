#!/usr/bin/env python3
"""Write docs/specs/web/openapi.yaml from the FastAPI app schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
OUT_PATH = PROJECT_ROOT / "docs" / "specs" / "web" / "openapi.yaml"


def _dump_yaml(data: dict) -> str:
    try:
        import yaml
    except ImportError:
        return json.dumps(data, indent=2)
    return yaml.dump(data, sort_keys=False, default_flow_style=False)


def main() -> None:
    try:
        from mtg_deck_tools.api.app import create_app
    except ModuleNotFoundError as exc:
        print(
            "FastAPI not installed. Install with: pip install -e '.[web]'",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    schema = create_app().openapi()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = _dump_yaml(schema)
    if text.startswith("{"):
        json_path = OUT_PATH.with_suffix(".json")
        json_path.write_text(text, encoding="utf-8")
        print(f"PyYAML not installed; wrote {json_path}", file=sys.stderr)
        raise SystemExit(1)
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
