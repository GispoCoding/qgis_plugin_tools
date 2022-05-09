from threading import Thread
from unittest.mock import MagicMock

from qgis.PyQt.QtCore import QCoreApplication

from ..tools.custom_logging import SimpleMessageBarProxy


def test_message_log_proxies_between_threads():
    mock_msg_bar = MagicMock()
    proxy = SimpleMessageBarProxy(mock_msg_bar)

    def mock_thread():
        proxy.emit_message("title", "text", 1, 2)

    thread = Thread(target=mock_thread)
    thread.start()

    mock_msg_bar.pushMessage.assert_not_called()
    thread.join(5)
    assert not thread.is_alive()

    QCoreApplication.processEvents()
    mock_msg_bar.pushMessage.assert_called_once_with(
        title="title", text="text", level=1, duration=2
    )
