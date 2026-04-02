#!/usr/bin/env python3
"""Write OpenAPI schema to openapi/openapi.json and openapi/openapi.yaml."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Ensure repo root is on path when invoked as `python scripts/export_openapi.py`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Settings require env: ``.env`` first, then ``tests/test.env`` for any missing keys.
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / "tests" / "test.env", override=False)

from app.main import app  # noqa: E402


def main() -> None:
    out_dir = _ROOT / "openapi"
    out_dir.mkdir(exist_ok=True)
    schema = app.openapi()

    json_path = out_dir / "openapi.json"
    json_path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    yaml_path = out_dir / "openapi.yaml"
    yaml_path.write_text(
        yaml.dump(
            schema,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {json_path.relative_to(_ROOT)}")
    print(f"Wrote {yaml_path.relative_to(_ROOT)}")


if __name__ == "__main__":
    main()
