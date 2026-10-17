#!/usr/bin/env python3
"""NeonFrame entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from neonframe.app import create_app

    app, _window = create_app()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
