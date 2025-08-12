import os
import sys


def _ensure_api_dir_on_syspath() -> None:
    """Ensure `api/` directory is on sys.path so `from core.wecom.verify` works.

    Tests live in `api/tests`. Adding the parent directory (`api`) to sys.path
    makes the `core.wecom` package importable from project root.
    """

    tests_dir = os.path.dirname(__file__)
    api_dir = os.path.abspath(os.path.join(tests_dir, os.pardir))
    if api_dir not in sys.path:
        sys.path.insert(0, api_dir)


_ensure_api_dir_on_syspath()
