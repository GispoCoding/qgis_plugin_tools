__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 2"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

from typing import Any, Callable, Optional

from .exceptions import QgsPluginException
from .i18n import tr
from .messages import MessageBarLogger
from .tasks import FunctionTask


def log_if_fails(
    fn: Optional[Callable] = None, /, *, logger_name: str = __name__
) -> Callable:
    """
    Use this as a decorator with functions and methods that
    might throw uncaught exceptions.
    """
    from functools import wraps

    # caller is at depth 3 (MessageBarLogger log call, this function, actual call)
    message_bar = MessageBarLogger(logger_name, stack_level=3)

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> None:  # noqa: ANN001
            try:
                # Qt injects False into some signals
                if args[1:] != (False,):
                    fn(*args, **kwargs)
                else:
                    fn(*args[:-1], **kwargs)
            except QgsPluginException as e:
                message_bar.exception(e, **e.bar_msg, stack_info=True)
            except Exception as e:
                message_bar.exception(
                    tr("Unhandled exception occurred"), e, stack_info=True
                )

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)


def taskify(fn: Callable) -> Callable:
    """
    Decoration used to turn any function or method into a FunctionTask task.
    """
    from functools import wraps

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> FunctionTask:  # noqa: ANN001
        return FunctionTask(lambda: fn(*args, **kwargs))

    return wrapper
