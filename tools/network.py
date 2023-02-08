import json
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Literal, NamedTuple, Optional, Tuple
from urllib.parse import urlencode
from uuid import uuid4

from qgis.core import Qgis, QgsBlockingNetworkRequest, QgsNetworkReplyContent
from qgis.PyQt.QtCore import QByteArray, QSettings, QUrl
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest

from ..tools.exceptions import QgsPluginNetworkException
from ..tools.i18n import tr
from ..tools.resources import plugin_name
from .custom_logging import bar_msg

try:
    import requests
    from requests.exceptions import RequestException
except ImportError:
    requests = None  # type: ignore
    RequestException = None  # type: ignore

__copyright__ = "Copyright 2020-2023, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

LOGGER = logging.getLogger(__name__)
ENCODING = "utf-8"
CONTENT_DISPOSITION_HEADER = "Content-Disposition"
CONTENT_DISPOSITION_BYTE_HEADER = QByteArray(
    bytes(CONTENT_DISPOSITION_HEADER, ENCODING)
)


class FileInfo(NamedTuple):
    file_name: str
    content: bytes
    content_type: str


class FileField(NamedTuple):
    field_name: str
    file_info: FileInfo


def fetch(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    params: Optional[Dict[str, str]] = None,
) -> str:
    """
    Fetch resource from the internet. Similar to requests.get(url) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param params: Dictionary to send in the query string
    :return: encoded string of the content
    """
    content, _ = fetch_raw(url, encoding, authcfg_id, params)
    return content.decode(ENCODING)


def post(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    data: Optional[Dict[str, str]] = None,
    files: Optional[List[FileField]] = None,
) -> str:
    """
    Post resource. Similar to requests.post(url, data, files) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param data: Dictionary to send in the request body
    :param files: Files to send multipart-encoded. Same format as requests.
    :return: encoded string of the content
    """
    content, _ = post_raw(url, encoding, authcfg_id, data, files)
    return content.decode(ENCODING)


def fetch_raw(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    params: Optional[Dict[str, str]] = None,
) -> Tuple[bytes, str]:
    """
    Fetch resource from the internet. Similar to requests.get(url) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param params: Dictionary to send in the query string
    :return: bytes of the content and default name of the file or empty string
    """
    return request_raw(url, "get", encoding, authcfg_id, params)


def post_raw(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    data: Optional[Dict[str, str]] = None,
    files: Optional[List[FileField]] = None,
) -> Tuple[bytes, str]:
    """
    Post resource. Similar to requests.post(url, data, files) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param data: Dictionary to send in the request body
    :param files: Files to send multipart-encoded. Same format as requests.
    :return: bytes of the content and default name of the file or empty string
    """
    return request_raw(url, "post", encoding, authcfg_id, None, data, files)


def request_raw(
    url: str,
    method: Literal["get", "post"] = "get",
    encoding: str = ENCODING,
    authcfg_id: str = "",
    params: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, str]] = None,
    files: Optional[List[FileField]] = None,
) -> Tuple[bytes, str]:
    """
    Request resource from the internet. Similar to requests.get(url) and
    requests.post(url, data) but is recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param method: method to use, defaults to 'get'
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param params: Dictionary to send in the query string
    :param data: Dictionary to send in the request body
    :param files: Files to send multipart-encoded. Same format as requests.
    :return: bytes of the content and default name of the file or empty string
    """
    if params:
        url += "?" + urlencode(params)
    LOGGER.debug(url)
    req = QNetworkRequest(QUrl(url))
    # http://osgeo-org.1560.x6.nabble.com/QGIS-Developer-Do-we-have-a-User-Agent-string-for-QGIS-td5360740.html
    user_agent = QSettings().value("/qgis/networkAndProxy/userAgent", "Mozilla/5.0")
    user_agent += " " if len(user_agent) else ""
    # noinspection PyUnresolvedReferences
    user_agent += f"QGIS/{Qgis.QGIS_VERSION_INT}"
    user_agent += f" {plugin_name()}"
    # https://www.riverbankcomputing.com/pipermail/pyqt/2016-May/037514.html
    req.setRawHeader(b"User-Agent", bytes(user_agent, encoding))
    request_blocking = QgsBlockingNetworkRequest()
    if authcfg_id:
        request_blocking.setAuthCfg(authcfg_id)
    # QNetworkRequest *only* supports get and post. No idea why.
    if method == "get":
        _ = request_blocking.get(req)
    elif method == "post":
        if data:
            # Support JSON
            byte_data = bytes(json.dumps(data), encoding)
            req.setRawHeader(
                b"Content-Type",
                bytes(f"application/json; charset={encoding}", encoding),
            )
        elif files:
            # Support multipart binary. Generate boundary like
            # https://github.com/requests/toolbelt/blob/master/requests_toolbelt/multipart/encoder.py
            boundary = uuid4().hex
            byte_boundary = bytes(f"\r\n--{boundary}\r\n", encoding)
            last_byte_boundary = bytes(f"\r\n--{boundary}--\r\n", encoding)

            # each file may have different content type, name and filename
            byte_data = b""
            for file_field in files:
                name = file_field[0]
                file_info = file_field[1]
                file_name = file_info[0]
                content = file_info[1]
                content_type = file_info[2]
                content_disposition_form_data = (
                    f"Content-Disposition: form-data;"
                    f' name="{name}";'
                    f' filename="{file_name}"\r\n'
                )
                content_type_form_data = f"Content-Type: {content_type}\r\n\r\n"
                byte_boundary_with_headers = (
                    byte_boundary
                    + bytes(content_disposition_form_data, encoding)
                    + bytes(content_type_form_data, encoding)
                )
                byte_data += byte_boundary_with_headers + content
            byte_data += last_byte_boundary
            req.setRawHeader(
                b"Content-Type",
                bytes(f"multipart/form-data; boundary={boundary}", encoding),
            )
        else:
            byte_data = b""
        _ = request_blocking.post(req, byte_data)
    else:
        raise Exception(f"Request method {method} not supported.")
    reply: QgsNetworkReplyContent = request_blocking.reply()
    reply_error = reply.error()
    if reply_error != QNetworkReply.NoError:
        # Error content will be empty in older QGIS versions:
        # https://github.com/qgis/QGIS/issues/42442
        message = (
            bytes(reply.content()).decode("utf-8")
            if len(bytes(reply.content()))
            else None
        )
        # bar_msg will just show a generic Qt error string.
        raise QgsPluginNetworkException(
            message=message,
            error=reply_error,
            bar_msg=bar_msg(reply.errorString()),
        )

    # https://stackoverflow.com/a/39103880/10068922
    default_name = ""
    if reply.hasRawHeader(CONTENT_DISPOSITION_BYTE_HEADER):
        header: QByteArray = reply.rawHeader(CONTENT_DISPOSITION_BYTE_HEADER)
        default_name = bytes(header).decode(encoding).split("filename=")[1]
        if default_name[0] in ['"', "'"]:
            default_name = default_name[1:-1]

    return bytes(reply.content()), default_name


def download_to_file(
    url: str,
    output_dir: Path,
    output_name: Optional[str] = None,
    use_requests_if_available: bool = True,
    encoding: str = ENCODING,
) -> Path:
    """
    Downloads a binary file to the file efficiently
    :param url: Url of the file
    :param output_dir: Path to the output directory
    :param output_name: If given, use this as file name. Otherwise reads file name from
    Content-Disposition header or uses the url
    :param use_requests_if_available: Use Python package requests
    if it is available in the environment
    :param encoding: Encoding which will be used to decode the bytes
    :return: Path to the file
    """

    def get_output(default_filename: str) -> Path:
        if output_name is None:
            if default_filename != "":
                out_name = default_filename
            else:
                out_name = url.replace("http://", "").replace("https://", "")
                if len(out_name.split("/")[-1]) > 2:
                    out_name = out_name.split("/")[-1]
        else:
            out_name = output_name
        return Path(output_dir, out_name)

    output = Path()

    if use_requests_if_available and requests is not None:
        # https://stackoverflow.com/a/39217788/10068922

        try:
            with requests.get(url, stream=True) as r:
                try:
                    r.raise_for_status()
                except Exception:
                    raise QgsPluginNetworkException(
                        tr("Request failed with status code {}", r.status_code),
                        bar_msg=bar_msg(r.text),
                    )
                default_filenames = re.findall(
                    "filename=(.+)", r.headers.get(CONTENT_DISPOSITION_HEADER, "")
                )
                default_filename = (
                    default_filenames[0] if len(default_filenames) else ""
                )
                output = get_output(default_filename)
                with open(output, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
        except RequestException as e:
            raise QgsPluginNetworkException(tr("Request failed"), bar_msg=bar_msg(e))
    else:
        # Using simple fetch_raw
        content, default_filename = fetch_raw(url, encoding)
        output = get_output(default_filename)
        with open(output, "wb") as f:
            f.write(content)
    return output
