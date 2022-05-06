__copyright__ = "Copyright 2021, qgis_plugin_tools contributors"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"

import logging
from typing import Callable, Optional, Union

from qgis.core import QgsApplication, QgsTask
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QCloseEvent
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..tools.decorations import log_if_fails
from ..tools.i18n import tr
from ..tools.resources import qgis_plugin_tools_resources

FORM_CLASS: QWidget
FORM_CLASS, _ = uic.loadUiType(qgis_plugin_tools_resources("ui", "progress_dialog.ui"))
LOGGER = logging.getLogger(__name__)


class ProgressDialog(QDialog, FORM_CLASS):
    """
    Dialog containing progress bar to show processes of long running tasks.
    """

    progress_bar: QProgressBar
    status_label: QLabel
    v_layout: QVBoxLayout
    abort_btn_text: str = tr("Abort")

    aborted = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QDialog] = None,
        show_abort_button: bool = False,
        abort_btn_text: str = abort_btn_text,
    ) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        if show_abort_button:
            self.push_btn = QPushButton()
            self.push_btn.setText(abort_btn_text)
            layout = QHBoxLayout()
            spacer = QSpacerItem(
                100, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Expanding
            )
            layout.addSpacerItem(spacer)
            layout.addWidget(self.push_btn)
            self.v_layout.addLayout(layout)
            self.push_btn.clicked.connect(self._aborted)

        self.update_progress_bar(0)

    def set_status(self, status_text: str) -> None:
        LOGGER.debug(f"Status:   {status_text}")
        self.status_label.setText(status_text)

    def update_progress_bar(self, progress: Union[int, float]) -> None:
        """Update progress bar with a progress"""
        self.progress_bar.setValue(int(min(100, progress)))

    def closeEvent(self, close_event: QCloseEvent) -> None:  # noqa: N802
        super().closeEvent(close_event)
        LOGGER.warning("Closing progress bar")
        self.aborted.emit()

    @log_if_fails
    def _aborted(self) -> None:
        LOGGER.warning("Aborted")
        self.close()


def create_simple_continuous_progress_dialog(
    status_text: str,
    parent: Optional[QDialog] = None,
    show_abort_button: bool = False,
    abort_btn_text: str = ProgressDialog.abort_btn_text,
) -> ProgressDialog:
    """
    Creates simple progress dialog with a continuous progress bar.
    """
    progress_dialog = ProgressDialog(parent, show_abort_button, abort_btn_text)
    progress_dialog.progress_bar.setMaximum(0)
    progress_dialog.progress_bar.setMinimum(0)
    progress_dialog.set_status(status_text)
    return progress_dialog


def run_task_with_progress_dialog(
    task: QgsTask,
    status_text: str,
    parent: Optional[QDialog] = None,
    show_abort_button: bool = False,
    abort_btn_text: str = ProgressDialog.abort_btn_text,
    completed_callback: Optional[Callable] = None,
    terminated_callback: Optional[Callable] = None,
) -> None:
    """
    Runs a given task while showing a progress bar dialog.
    """
    progress_dialog = ProgressDialog(parent, show_abort_button, abort_btn_text)
    progress_dialog.set_status(status_text)
    task.progressChanged.connect(progress_dialog.update_progress_bar)
    _make_connections_and_run_task(
        progress_dialog, task, completed_callback, terminated_callback
    )


def run_task_with_continuous_progress_dialog(
    task: QgsTask,
    status_text: str,
    parent: Optional[QDialog] = None,
    show_abort_button: bool = False,
    abort_btn_text: str = ProgressDialog.abort_btn_text,
    completed_callback: Optional[Callable] = None,
    terminated_callback: Optional[Callable] = None,
) -> None:
    """
    Runs a given task while showing a simple continuous progress bar dialog.
    """
    progress_dialog = create_simple_continuous_progress_dialog(
        status_text, parent, show_abort_button, abort_btn_text
    )
    _make_connections_and_run_task(
        progress_dialog, task, completed_callback, terminated_callback
    )


def _make_connections_and_run_task(
    progress_dialog: ProgressDialog,
    task: QgsTask,
    completed_callback: Optional[Callable],
    terminated_callback: Optional[Callable],
) -> None:
    task.taskCompleted.connect(lambda: progress_dialog.close())
    task.taskTerminated.connect(lambda: progress_dialog.close())
    progress_dialog.aborted.connect(task.cancel)
    if completed_callback:
        task.taskCompleted.connect(completed_callback)
    if terminated_callback:
        task.taskTerminated.connect(terminated_callback)
    task_manager = QgsApplication.taskManager()
    task_manager.addTask(task)
    # Wait until task is either completed or terminated
    progress_dialog.exec()
