# <commented_out>import os
# <commented_out>from .qgis_plugin_tools.infrastructure.debugging import setup_pydevd

# <commented_out>if os.environ.get('QGIS_PLUGIN_USE_DEBUGGER') == 'pydevd':
# <commented_out>    if os.environ.get('IN_TESTS', "0") != "1" and os.environ.get('QGIS_PLUGIN_IN_CI', "0") != "1": # noqa E501
# <commented_out>        setup_pydevd()


def classFactory(iface):  # noqa N802
    from .plugin import Plugin

    return Plugin(iface)
