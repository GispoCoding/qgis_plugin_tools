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

    def __init__(self, logger_name: str, stack_level: int = 2) -> None:
        self._logger = logging.getLogger(logger_name)
        self._logger_kwargs: Dict[str, Any] = (
            {}
            if sys.version_info.major == 3 and sys.version_info.minor < 8
            else {"stacklevel": stack_level}
        )

    def info(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
        exc_info: Optional[Exception] = None,
        stack_info: bool = False,
    ) -> None:
        """
        Logs info messages to message bar and to other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        :param exc_info: Exception of handled exception for capturing traceback
        :param stack_info: Whether to include stack info
        """

        self._logger.info(
            str(message),
            extra=bar_msg(details, duration, success),
            exc_info=exc_info,
            stack_info=stack_info,
            **self._logger_kwargs,
        )
        if details != "":
            self._logger.info(
                str(details),
                exc_info=exc_info,
                stack_info=stack_info,
                **self._logger_kwargs,
            )

    def warning(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
        exc_info: Optional[Exception] = None,
        stack_info: bool = False,
    ) -> None:
        """
        Logs warning messages to message bar and to other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        :param exc_info: Exception of handled exception for capturing traceback
        :param stack_info: Whether to include stack info
        """
        self._logger.warning(
            str(message),
            extra=bar_msg(details, duration, success),
            exc_info=exc_info,
            stack_info=stack_info,
            **self._logger_kwargs,
        )
        if details != "":
            self._logger.warning(
                str(details),
                exc_info=exc_info,
                stack_info=stack_info,
                **self._logger_kwargs,
            )

    def error(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
        exc_info: Optional[Exception] = None,
        stack_info: bool = False,
    ) -> None:
        """
        Logs error of risen exception to message bar and to other logging handlers
        :param message: Header of the message
        :param details: Longer body of the message. Can be set to empty string.
        :param duration: can be used to specify the message timeout in seconds. If
            ``duration`` is set to 0, then the message must be manually dismissed
            by the user.
        :param success: Whether the message is success message or not
        :param exc_info: Exception of handled exception for capturing traceback
        :param stack_info: Whether to include stack info
        """
        self._logger.error(
            str(message),
            extra=bar_msg(details, duration, success),
            exc_info=exc_info,
            stack_info=stack_info,
            **self._logger_kwargs,
        )
        if details != "":
            self._logger.error(
                str(details),
                exc_info=exc_info,
                stack_info=stack_info,
                **self._logger_kwargs,
            )

    def exception(
        self,
        message: Any,
        details: Any = "",
        duration: Optional[int] = None,
        success: bool = False,
        exc_info: Optional[Exception] = None,
        stack_info: bool = False,
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
        :param exc_info: Exception of handled exception for capturing traceback
        :param stack_info: Whether to include stack info
        """
        # for some reason using logger.exception will essentially have extra stack level
        # even though its not visible on the printed stack (possibly due to exception
        # being a simple helper which calls error internally). use plain error here to
        # have same effective stacklevel on both actual log records. possibly related
        # https://github.com/python/cpython/issues/89334 has been fixed in 3.11+
        self._logger.error(
            str(message),
            extra=bar_msg(details, duration, success),
            stack_info=stack_info,
            exc_info=True,
            **self._logger_kwargs,
        )
        if details != "":
            self._logger.error(
                str(details),
                exc_info=exc_info,
                stack_info=stack_info,
                **self._logger_kwargs,
            )


# publish the old MsgBar with the default logger name
MsgBar = MessageBarLogger(__name__)
