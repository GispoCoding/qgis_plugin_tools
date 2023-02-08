__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

import json

import pytest

from ..tools.exceptions import QgsPluginNetworkException
from ..tools.network import download_to_file, fetch, post


def test_fetch(qgis_new_project):
    data = fetch("https://httpbin.org/get")
    data = json.loads(data)
    assert data["url"] == "https://httpbin.org/get"


def test_fetch_invalid_url(qgis_new_project):
    with pytest.raises(QgsPluginNetworkException):
        fetch("invalidurl")


def test_fetch_params(qgis_new_project):
    data = fetch("https://httpbin.org/get", params={"foo": "bar"})
    data = json.loads(data)
    assert data["url"] == "https://httpbin.org/get?foo=bar"
    assert data["args"] == {"foo": "bar"}


def test_post(qgis_new_project):
    data = post("https://httpbin.org/post")
    data = json.loads(data)
    assert data["url"] == "https://httpbin.org/post"


def test_post_invalid_url(qgis_new_project):
    with pytest.raises(QgsPluginNetworkException):
        post("invalidurl")


def test_post_data(qgis_new_project):
    data = post("https://httpbin.org/post", data={"foo": "bar"})
    data = json.loads(data)
    assert data["url"] == "https://httpbin.org/post"
    assert data["data"] == json.dumps({"foo": "bar"})


def test_upload_file(qgis_new_project, file_fixture):
    file_name, file_content, file_type = file_fixture
    data = post(
        "https://httpbin.org/post",
        files=[("file", (file_name, file_content, file_type))],
    )
    data = json.loads(data)
    assert data["url"] == "https://httpbin.org/post"
    assert data["files"]
    assert bytes(data["files"]["file"], "utf-8") == file_content


def test_upload_multiple_files(qgis_new_project, file_fixture, another_file_fixture):
    file_name, file_content, file_type = file_fixture
    another_file_name, another_file_content, another_file_type = another_file_fixture
    data = post(
        "https://httpbin.org/post",
        files=[
            ("file", (file_name, file_content, file_type)),
            (
                "another_file",
                (another_file_name, another_file_content, another_file_type),
            ),
        ],
    )
    data = json.loads(data)
    assert data["url"] == "https://httpbin.org/post"
    assert data["files"]
    assert bytes(data["files"]["file"], "utf-8") == file_content
    assert bytes(data["files"]["another_file"], "utf-8") == another_file_content


@pytest.mark.skip(
    "file does not exist. "
    "TODO: search another file to be used using Content-Disposition"
)
def test_download_to_file(qgis_new_project, tmpdir):
    path_to_file = download_to_file(
        "https://twitter.com/gispofinland/status/1324599933337567232/photo/1",
        tmpdir,
        "test_file",
    )
    assert path_to_file.exists()
    assert path_to_file.is_file()


@pytest.mark.skip(
    "file does not exist. "
    "TODO: search another file to be used using Content-Disposition"
)
def test_download_to_file_without_requests(qgis_new_project, tmpdir):
    path_to_file = download_to_file(
        "https://twitter.com/gispofinland/status/1324599933337567232/photo/1",
        tmpdir,
        "test_file",
        use_requests_if_available=False,
    )
    assert path_to_file.exists()
    assert path_to_file.is_file()


def test_download_to_file_with_name(qgis_new_project, tmpdir):
    path_to_file = download_to_file(
        "https://raw.githubusercontent.com/GispoCoding/FMI2QGIS/master/FMI2QGIS/test/data/aq_small.nc",  # noqa E501
        tmpdir,
    )
    assert path_to_file.exists()
    assert path_to_file.is_file()
    assert path_to_file.name == "aq_small.nc"


def test_download_to_file_invalid_url(qgis_new_project, tmpdir):
    with pytest.raises(QgsPluginNetworkException):
        download_to_file("invalidurl", tmpdir)


def test_download_to_file_invalid_url_without_requests(qgis_new_project, tmpdir):
    with pytest.raises(QgsPluginNetworkException):
        download_to_file("invalidurl", tmpdir)
