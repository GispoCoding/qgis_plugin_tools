import time

from qgis.core import Qgis
from qgis.PyQt.QtCore import QCoreApplication, QEventLoop

from ..testing.utilities import SimpleTask, TestTaskRunner
from ..tools.exceptions import QgsPluginException, TaskInterruptedException
from ..tools.tasks import FunctionTask

__copyright__ = "Copyright 2021, qgis_plugin_tools contributors"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"


def fn(*args, **kwargs):  # noqa
    for _ in range(10):
        time.sleep(0.01)
    return args, kwargs


def test_run_simple_task(task_runner: TestTaskRunner):
    task = SimpleTask()
    success = task_runner.run_task(task)

    assert success
    assert task_runner.progress == 100


def test_run_simple_task_canceled(task_runner: TestTaskRunner, qgis_iface):
    task = SimpleTask()
    success = task_runner.run_task(task, cancel=True)

    # for some reason this randomly fails if the signal is not waited for
    QCoreApplication.processEvents(QEventLoop.AllEvents, 100)  # 100 ms wait

    messages = qgis_iface.messageBar().get_messages(Qgis.Warning)

    assert not success
    assert task_runner.fail
    assert (
        "Task SimpleTask was not successful:"
        "Task was cancelled by user or some dependency tasks failed" in messages
    )


def test_run_simple_task_canceled_after_a_while(
    task_runner: TestTaskRunner, qgis_iface
):
    task = SimpleTask()
    success = task_runner.run_task(task, cancel=True, sleep_before_cancel=0.01)
    messages = qgis_iface.messageBar().get_messages(Qgis.Critical)

    assert not success
    assert task_runner.fail
    assert isinstance(task.exception, TaskInterruptedException)
    assert "Task canceled!:" in messages


def test_run_simple_task_failed(task_runner: TestTaskRunner, qgis_iface):
    task = SimpleTask(True)
    success = task_runner.run_task(task)
    messages = qgis_iface.messageBar().get_messages(Qgis.Critical)

    assert not success
    assert task_runner.fail
    assert "Unhandled exception occurred:custom failure" in messages


def test_run_simple_task_failed_with_qgs_plugin_exception(
    task_runner: TestTaskRunner, qgis_iface
):
    task = SimpleTask(True, QgsPluginException)
    success = task_runner.run_task(task)
    messages = qgis_iface.messageBar().get_messages(Qgis.Critical)

    assert not success
    assert task_runner.fail
    assert "custom failure:" in messages


def test_function_task_without_params(task_runner: TestTaskRunner):
    task = FunctionTask(fn)
    success = task_runner.run_task(task)

    assert success
    assert task.result == ((), {})


def test_function_task_with_params(task_runner: TestTaskRunner):
    task = FunctionTask(lambda: fn(1, 2, a=1, b=2))
    success = task_runner.run_task(task)

    assert success
    assert task.result == ((1, 2), {"a": 1, "b": 2})
