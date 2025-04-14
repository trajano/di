import pytest

from di_aio.testing import reset_default_aio_context


@pytest.fixture(autouse=True)
def _reset():
    reset_default_aio_context()
