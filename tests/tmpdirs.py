from __future__ import annotations

import contextlib
import shutil
import uuid
from pathlib import Path
from typing import Iterator


@contextlib.contextmanager
def temp_dir(base: Path) -> Iterator[Path]:
    """
    Windows sandbox note:
    `tempfile.TemporaryDirectory()` uses `os.mkdir(..., 0o700)` which can create
    directories we cannot write to in this environment. Use default mkdir perms.
    """

    base.mkdir(parents=True, exist_ok=True)
    d = base / f"tmp-{uuid.uuid4().hex}"
    d.mkdir(parents=True, exist_ok=False)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@contextlib.contextmanager
def temp_project_dir(repo_root: Path, *, name: str = "demo-project") -> Iterator[Path]:
    base = repo_root / "tests_tmp"
    with temp_dir(base) as d:
        root = d / name
        root.mkdir(parents=True, exist_ok=False)
        yield root

