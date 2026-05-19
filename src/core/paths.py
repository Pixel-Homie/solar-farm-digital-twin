"""Resolve bundled asset paths for development and PyInstaller executables."""

from __future__ import annotations

import os
import sys


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def project_root() -> str:
    """Repository root when running from source."""
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )


def bundle_root() -> str:
    """
    Root folder for shipped assets (``data/``, ``Interface/``).

    PyInstaller one-file extracts bundled data under ``sys._MEIPASS``.
    """
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return project_root()


def resource_path(*parts: str) -> str:
    return os.path.join(bundle_root(), *parts)


def data_path(*parts: str) -> str:
    return resource_path("data", *parts)
