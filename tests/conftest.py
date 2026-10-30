from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Direct invocation remains available; ordinary discovery uses tests/scripts.
collect_ignore = ["test_script_collection.py"]


@pytest.fixture
def tmp_dir() -> Iterator[Path]:
    """Provide test directories inside the repository instead of global temp."""
    repo_tmp = Path(__file__).resolve().parents[1] / ".tmp"
    repo_tmp.mkdir(exist_ok=True, parents=True)
    with TemporaryDirectory(prefix="pytest-", dir=repo_tmp) as directory:
        yield Path(directory)
    ####
####
