# type: ignore
# flake8: noqa ANN201

__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

from typing import Tuple

import pytest

from ..testing.utilities import TestTaskRunner
from ..tools.custom_logging import (
    LogTarget,
    get_log_level_key,
    setup_logger,
    teardown_logger,
)
from ..tools.resources import plugin_name
from ..tools.settings import set_setting


@pytest.fixture(scope="session")
def initialize_logger(qgis_iface):
    set_setting(get_log_level_key(LogTarget.FILE), "NOTSET")
    setup_logger(plugin_name(), qgis_iface)
    yield
    teardown_logger(plugin_name())


@pytest.fixture()
def task_runner(initialize_logger):
    return TestTaskRunner()


@pytest.fixture()
def file_fixture() -> Tuple[str, bytes, str]:
    with open("test/fixtures/file.xml", "rb") as f:
        yield "file.xml", f.read(), "text/xml"


@pytest.fixture()
def another_file_fixture() -> Tuple[str, bytes, str]:
    with open("test/fixtures/text.txt", "rb") as f:
        yield "text.txt", f.read(), "text/plain"
