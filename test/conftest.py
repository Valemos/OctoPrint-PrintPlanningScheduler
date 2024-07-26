from pathlib import Path

from pytest import fixture


@fixture
def data_folder():
    return Path(__file__).parent / "data"
