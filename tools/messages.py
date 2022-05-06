import logging
import sys
from typing import Any, Dict, Optional

from .custom_logging import bar_msg


class MessageBarLogger:
    """
    logging.Logger like interface to push messages to the
    message bar where necessary with info/warning/etc methods.

    Setup with a logger name that has a message bar set.
    """

    def __init__(self, logger_name: str) -> None:
        self._logger = logging.getLogger(logger_name)
        self._logger_kwargs: Dict[str, Any] = (
            {}
            if sys.version_info.major == 3 and sys.version_info.minor < 8
            else {"stacklevel": 2}
        )

    def info(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
    ) -> None:
        """
        Logs info messages to message bar and to other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        """

        self._logger.info(
            str(message),
            extra=bar_msg(details, duration, success),
            **self._logger_kwargs
        )
        if details != "":
            self._logger.info(str(details), **self._logger_kwargs)

    def warning(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
    ) -> None:
        """
        Logs warning messages to message bar and to other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        """
        self._logger.warning(
            str(message),
            extra=bar_msg(details, duration, success),
            **self._logger_kwargs
        )
        if details != "":
            self._logger.warning(str(details), **self._logger_kwargs)

    def error(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
    ) -> None:
        """
        Logs error without traceback of risen exception to message bar and to
        other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        """
        self._logger.error(
            str(message),
            extra=bar_msg(details, duration, success),
            **self._logger_kwargs
        )
        if details != "":
            self._logger.error(str(details), **self._logger_kwargs)

    def exception(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
    ) -> None:
        """
        Logs error with traceback of risen exception to message bar and to
        other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        """
        self._logger.exception(
            str(message),
            extra=bar_msg(details, duration, success),
            **self._logger_kwargs
        )
        if details != "":
            self._logger.error(str(details), **self._logger_kwargs)


# publish the old MsgBar with the default logger name
MsgBar = MessageBarLogger(__name__)
