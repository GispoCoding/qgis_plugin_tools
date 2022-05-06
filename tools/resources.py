"""Tools to work with resource files."""
import configparser
import sys
from os.path import abspath, dirname, exists, join, pardir
from pathlib import Path
from typing import Dict, Optional

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QWidget

__copyright__ = (
    "Copyright 2019, 3Liz, 2020-2021 Gispo Ltd, 2022 National Land Survey of Finland"
)
__license__ = "GPL version 3"
__email__ = "info@3liz.org"
__revision__ = "$Format:%H$"

from qgis.core import QgsApplication

PLUGIN_NAME: str = ""
SLUG_NAME: str = ""


_TOP_LEVEL_NAME = __name__.split(".", maxsplit=1)[0]
_IS_SUBMODULE_USAGE = not _TOP_LEVEL_NAME == "qgis_plugin_tools"


def _plugin_path_submodule() -> str:
    # assume qgis_plugin_tools is inside the plugin package,
    # use the path to the top level module name

    module_file = sys.modules[_TOP_LEVEL_NAME].__file__

    if module_file is not None:
        path = str(Path(module_file).parent.resolve())
    else:
        # maybe possible to have __file__ as none? fall back to default
        # structure with qgis_plugin_tools directly under plugin package
        path = dirname(dirname(__file__))
        path = abspath(abspath(join(path, pardir)))

    return path


def _plugin_path_dependency() -> str:
    # go up the stack until first metadata.txt is found
    # relative to the calling modules top level package name
    # probably inefficient, but if the runtime is not a dependency
    # but a subtree instead this might not need any optimizations?
    import inspect

    for frame_info in inspect.stack():
        module_name: Optional[str] = frame_info.frame.f_globals.get("__name__")
        if module_name is not None:
            top_level_name, *_ = module_name.split(".", maxsplit=1)
            top_level_module = sys.modules.get(top_level_name)
            if top_level_module is not None:
                top_level_directory = Path(inspect.getfile(top_level_module)).parent
                if (top_level_directory / "metadata.txt").exists():
                    return str(top_level_directory)

    # fall back to default directory tree
    return _plugin_path_submodule()


def plugin_path(*args: str) -> str:
    """Get the path to plugin package folder.

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    :type args: str

    :return: Absolute path to the resource.
    :rtype: str
    """
    if _IS_SUBMODULE_USAGE:
        path = _plugin_path_submodule()
    else:
        path = _plugin_path_dependency()

    for item in args:
        path = abspath(join(path, item))

    return path


def root_path(*args: str) -> str:
    """Get the path to plugin root folder.

    NOTE: the assumed root is the parent of the plugin package folder.

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    :type args: str

    :return: Absolute path to the resource.
    :rtype: str
    """
    return plugin_path(pardir, *args)


def profile_path(*args: str) -> str:
    """
    Get the path inside profile folder.
    return: Absolute path to the resource.
    """
    path = QgsApplication.qgisSettingsDirPath()
    for item in args:
        path = abspath(join(path, item))

    return path


def plugin_name() -> str:
    """Return the plugin name according to metadata.txt.

    :return: The plugin name.
    :rtype: basestring
    """
    global PLUGIN_NAME, _IS_SUBMODULE_USAGE

    if PLUGIN_NAME != "":
        return PLUGIN_NAME

    try:
        metadata = metadata_config()
        name: str = metadata["general"]["name"]
        name = name.replace(" ", "").strip()
    except KeyError:
        name = "test_plugin"

    # if qgis plugin tools is run as a dependency, global var cannot be set
    # since it might confuse multiple plugins in the same env using this fn
    if not _IS_SUBMODULE_USAGE:
        PLUGIN_NAME = name

    return name


def slug_name() -> str:
    """Return project slug name in .qgis-plugin.ci"""
    global SLUG_NAME, _IS_SUBMODULE_USAGE

    if SLUG_NAME != "":
        return SLUG_NAME

    try:
        metadata = metadata_config()
        name: str = metadata["general"]["repository"]
        slug = name.split("/")[-1]
    except KeyError:
        slug = plugin_name()

    # if qgis plugin tools is run as a dependency, global var cannot be set
    # since it might confuse multiple plugins in the same env using this fn
    if not _IS_SUBMODULE_USAGE:
        SLUG_NAME = slug

    return slug


def task_logger_name() -> str:
    """
    Returns the name for task logger
    """
    return f"{plugin_name()}_task"


def metadata_config() -> configparser.ConfigParser:
    """Get the INI config parser for the metadata file.

    :return: The config parser object.
    :rtype: ConfigParser
    """
    path = plugin_path("metadata.txt")
    config = configparser.ConfigParser()
    config.read(path)
    return config


def qgis_plugin_ci_config() -> Optional[Dict]:
    """
    Get configuration of the ci config or None
    """
    path_str = root_path(".qgis-plugin-ci")
    if not Path(path_str).exists():
        path_str = plugin_path(".qgis-plugin-ci")
    path = Path(path_str)
    if path.exists():
        with open(path) as f:
            config = {}
            for line in f:
                parts = line.split(":")
                config[parts[0]] = ":".join(parts[1:])

        return config
    return None


def plugin_test_data_path(*args: str) -> str:
    """Get the path to the plugin test data path.

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    :type args: str

    :return: Absolute path to the resources folder.
    :rtype: str
    """

    path = abspath(abspath(join(root_path(), "test", "data")))
    if not exists(path):
        path = abspath(abspath(join(plugin_path(), "test", "data")))
    for item in args:
        path = abspath(join(path, item))

    return path


def resources_path(*args: str) -> str:
    """Get the path to our resources folder.

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    :type args: str

    :return: Absolute path to the resources folder.
    :rtype: str
    """
    path = abspath(abspath(join(plugin_path(), "resources")))
    for item in args:
        path = abspath(join(path, item))

    return path


def qgis_plugin_tools_resources(*args: str) -> str:
    """Get the path within the qgis_plugin_tools submodule"""
    return str(Path(__file__, "..", "..", "resources", *args).resolve().absolute())


def load_ui(*args: str) -> QWidget:
    """Get compiled UI file.

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    :type args: str

    :return: Compiled UI file.
    """
    ui_class, _ = uic.loadUiType(resources_path("ui", *args))
    return ui_class


def ui_file_dialog(*ui_file_name_parts: str):  # noqa ANN201
    """DRY helper for building classes from a .ui file"""

    class UiFileDialogClass(QDialog, load_ui(*ui_file_name_parts)):  # type: ignore
        def __init__(
            self,
            parent: Optional[QWidget],
        ) -> None:
            super().__init__(parent)
            self.setupUi(self)  # provided by load_ui FORM_CLASS

    return UiFileDialogClass
