#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa
import argparse
import os
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List
from zipfile import ZipFile

from ..tools.resources import plugin_name, plugin_path, resources_path
from .plugin_creator import ROOT_DIR, PluginCreator

__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"


def is_windows():
    return "win" in sys.platform and "darwin" not in sys.platform


PLUGINNAME = plugin_name()

SUBMODULES = ["qgis_plugin_tools"]
# This should be only edited for windows environment
QGIS_INSTALLATION_DIR = os.path.join("C:", "OSGeo4W64", "bin")

# Add files for any locales you want to support here
LOCALES: List[str] = []

# If locales are enabled, set the name of the lrelease binary on your system. If
# you have trouble compiling the translations, you may have to specify the full path to
# lrelease
LRELEASE = "lrelease"  # 'lrelease-qt4'

PYRCC = "pyrcc5"

# Name of the QGIS profile you are using in development
PROFILE = "default"

# Resource files
RESOURCES_SRC: List[str] = []

EXTRAS = ["metadata.txt"]

EXTRA_DIRS = ["resources"]

COMPILED_RESOURCE_FILES = ["resources.py"]

"""
#################################################
# Normally you would not need to edit below here
#################################################
"""

STARTUP_BAT = r"""
@echo off
set IDE={ide}
set REPOSITORY={repository}
set OSGEO4W_ROOT={qgis_root}
set QGIS_PREFIX_PATH={qgis_prefix_path}
set TEMP_PATH=%PATH%
call "%OSGEO4W_ROOT%"\bin\o4w_env.bat
call "%OSGEO4W_ROOT%"\bin\qt5_env.bat
call "%OSGEO4W_ROOT%"\bin\py3_env.bat
call "%OSGEO4W_ROOT%"\apps\grass\grass78\etc\env.bat
path %QGIS_PREFIX_PATH%\bin;%PATH%
path %PATH%;%OSGEO4W_ROOT%\apps\Qt5\bin
path %PATH%;%OSGEO4W_ROOT%\apps\Python37\Scripts
path %QGIS_PREFIX_PATH%\bin;%PATH%
:: Add original PATH
path %PATH%;%TEMP_PATH%
set GDAL_FILENAME_IS_UTF8=YES
:: Set VSI cache to be used as buffer, see #6448
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%QGIS_PREFIX_PATH%\qtplugins;%OSGEO4W_ROOT%\apps\Qt5\plugins
set PYTHONPATH=%QGIS_PREFIX_PATH%\python;%OSGEO4W_ROOT%\apps\Qt5\plugins;%PYTHONPATH%

start "Start your IDE aware of QGIS" /B %IDE% %REPOSITORY%
"""

# self.qgis_dir points to the location where your plugin should be installed.
# This varies by platform, relative to your HOME directory:
# 	* Linux:
# 	  .local/share/QGIS/QGIS3/profiles/default/python/plugins/
# 	* Mac OS X:
# 	  Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins
# 	* Windows:
# 	  AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins'

if sys.platform == "linux":
    dr = os.path.join(".local", "share")
elif is_windows():
    dr = os.path.join("AppData", "Roaming")
else:
    dr = os.path.join("Library", "Application Support")

VERBOSE = False


def echo(*args, **kwargs):
    if VERBOSE or kwargs.get("force", False):
        print(*args)


class PluginMaker:
    def __init__(
        self,
        py_files,
        ui_files,
        resources=RESOURCES_SRC,
        extra_dirs=EXTRA_DIRS,
        extras=EXTRAS,
        compiled_resources=COMPILED_RESOURCE_FILES,
        locales=LOCALES,
        profile=PROFILE,
        lrelease=LRELEASE,
        pyrcc=PYRCC,
        verbose=VERBOSE,
        submodules=SUBMODULES,
    ):
        global VERBOSE
        self.py_files = py_files
        self.ui_files = ui_files
        self.resources = resources
        self.extra_dirs = extra_dirs
        self.extras = extras
        self.compiled_resources = compiled_resources
        self.locales = locales
        self.profile = profile
        self.lrelease = lrelease
        self.pyrcc = pyrcc
        self.qgis_dir = os.path.join(dr, "QGIS", "QGIS3", "profiles", profile)
        self.plugin_dir = os.path.join(
            str(Path.home()), self.qgis_dir, "python", "plugins", PLUGINNAME
        )
        self.submodules = submodules
        VERBOSE = verbose

        # git-like usage https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html # noqa
        usage = f"""build.py <command> [<args>]
Commands:
     clean          Cleans resources
     compile        Compiles resources to resources.py
     deploy         Deploys the plugin to the QGIS plugin directory ({self.plugin_dir})
     package        Builds a package that can be uploaded to Github releases
                    or to the plugin repository
     start_ide      Start IDE of your choice. This is required on Windows to
                    assure that the environment is set correctly.
     transup        Search for new strings to be translated
     transcompile   Compile translation files to .qm files.
     venv           Create python virtual environment
Put -h after command to see available optional arguments if any
"""
        parser = ArgumentParser(usage=usage)
        parser.add_argument("command", help="Subcommand to run")
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)

        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def clean(self):
        for fil in self.compiled_resources:
            if os.path.exists(fil):
                echo(f"rm {fil}")
                os.remove(fil)

    def compile(self):
        pre_args = self._get_platform_args()
        for fil in self.resources:
            if os.path.exists(fil):

                args = pre_args + [self.pyrcc, "-o", fil.replace(".qrc", ".py"), fil]
                self.run_command(args)
            else:
                raise ValueError(f"The expected resource file {fil} is missing!")

    def _get_platform_args(self):
        pre_args = []
        if is_windows():
            pre_args = ["cmd", "\c"]  # noqa W605
        return pre_args

    def deploy(self):
        self.compile()
        dst_dir = f"{self.plugin_dir}/"
        os.makedirs(self.plugin_dir, exist_ok=True)
        for dr in self.extra_dirs:
            echo(f"cp -R --parents {dr} {dst_dir}")
            dst = os.path.join(self.plugin_dir, dr)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(dr, dst)
        self.cp_parents(dst_dir, self.extras)
        self.cp_parents(dst_dir, self.compiled_resources)
        self.cp_parents(dst_dir, self.py_files)
        self.cp_parents(dst_dir, self.ui_files)

    def package(self):
        parser = ArgumentParser()
        parser.add_argument(
            "--version",
            type=str,
            help="Version number of the tag (eg. --version v0.0.1",
        )
        parser.add_argument(
            "--tag",
            action="store_true",
            help="Run git tag as well. REMEMBER to update metadata.txt with "
            "your version before this",
        )
        parser.set_defaults(test=False)
        args = parser.parse_args(sys.argv[2:])
        if args.version is None:
            echo("Give valid version number", force=True)
            parser.print_help()
            exit(1)

        if args.tag:
            self.run_command(self._get_platform_args() + ["git", "tag", args.version])

        pkg_command = [
            "git",
            "archive",
            f"--prefix={PLUGINNAME}/",
            "-o",
            f"{PLUGINNAME}.zip",
            args.version,
        ]
        self.run_command(self._get_platform_args() + pkg_command)

        for submodule in self.submodules:
            d = plugin_path(submodule)
            pkg_command = [
                "git",
                "archive",
                f"--prefix={PLUGINNAME}/{submodule}/",
                "-o",
                f"{submodule}.zip",
                "master",
            ]
            self.run_command(self._get_platform_args() + pkg_command, d=d)
        zips = [f"{PLUGINNAME}.zip"] + [
            os.path.abspath(os.path.join(plugin_path(submodule), f"{submodule}.zip"))
            for submodule in self.submodules
        ]
        self.join_zips(zips)
        echo(f"Created package: {PLUGINNAME}.zip")

    def start_ide(self):
        if not is_windows():
            print("This command is only meant to run on Windows environment.")
            return
        parser = ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--ide",
            type=str,
            help=r"Path to your .exe (eg. C:\Program Files\JetBrains\IntelliJ IDEA 2020.3.2\bin\idea64.exe)."
            "Set the path to a environment variable QGIS_DEV_IDE to avoid typing it each time.",
            default=os.environ.get("QGIS_DEV_IDE", ""),
        )
        parser.add_argument(
            "--qgis_root",
            type=str,
            help=r"Path to your QGIS installation directory. (eg. C:\OSGeo4W64 or C:\QGIS_3_16). "
            r"Set the path to a environment variable QGIS_DEV_OSGEO4W_ROOT to avoid typing it each time.",
            default=os.environ.get("QGIS_DEV_OSGEO4W_ROOT", r"C:\OSGeo4W64"),
        )
        parser.add_argument(
            "--qgis_prefix_path",
            type=str,
            help=r"This is a path to OSGEO4W_ROOT/apps/ which is either qgis or qgis-ltr. "
            r"Set the path to a environment variable QGIS_DEV_PREFIX_PATH to avoid typing it each time.",
            default=os.environ.get(
                "QGIS_DEV_PREFIX_PATH", r"C:\OSGeo4W64\apps\qgis-ltr"
            ),
        )
        parser.add_argument(
            "--save_to_disk",
            action="store_true",
            help=r"Saves the startup script  to the disk rather than starting the IDE.",
        )
        args = parser.parse_args(sys.argv[2:])
        if not args.ide:
            print("Add reasonable value to --ide")
            return

        script = STARTUP_BAT.format(
            ide=args.ide if '"' in args.ide or " " not in args.ide else f'"{args.ide}"',
            repository=ROOT_DIR,
            qgis_root=args.qgis_root,
            qgis_prefix_path=args.qgis_prefix_path,
        )

        if args.save_to_disk:
            with open(Path(ROOT_DIR) / "start_ide.bat", "w") as f:
                f.write(script)
                print(
                    f"Script saved successfully to {f.name}. "
                    f"You can move the file whenever you want."
                )
        else:
            process = subprocess.Popen(
                "cmd.exe",
                shell=False,
                universal_newlines=True,
                stdin=subprocess.PIPE,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            process.communicate(script)

    def transup(self):
        files_to_translate = self.py_files + self.ui_files
        for locale in self.locales:
            ts_file = os.path.join(resources_path("i18n"), f"{locale}.ts")
            args = (
                self._get_platform_args()
                + ["pylupdate5", "-noobsolete"]
                + files_to_translate
                + ["-ts", ts_file]
            )
            self.run_command(args, force_show_output=True)

    def transcompile(self):
        pre_args = self._get_platform_args()
        for locale in self.locales:
            fil = os.path.join(resources_path("i18n"), f"{locale}.ts")
            echo(f"Processing {fil}")
            args = pre_args + [self.lrelease, "-qt=qt5", fil]
            self.run_command(args, force_show_output=True)

    def venv(self):
        print("Creating virtual env")
        creator = PluginCreator("", "", "", True)
        creator.create_venv()

    @staticmethod
    def run_command(args, d=None, force_show_output=False):
        cmd = " ".join(args)
        if d is not None:
            cmd = f"cd {d} && " + cmd
        echo(cmd, force=force_show_output)
        pros = subprocess.Popen(
            args,
            cwd=d,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = pros.communicate()
        echo(stdout, force=force_show_output)
        if len(stderr):
            echo(stderr, force=True)
            print(
                "------beging of stderr----------:\n",
                stderr,
                "\n-----end of stderr-----",
            )
            raise ValueError("Stopping now due to error in stderr!")

    @staticmethod
    def cp_parents(target_dir, files):
        """https://stackoverflow.com/a/15340518"""
        dirs = []
        for file in files:
            dirs.append(os.path.dirname(file))
        dirs.sort(reverse=True)
        for i in range(len(dirs)):
            if not dirs[i] in dirs[i - 1]:
                need_dir = os.path.normpath(target_dir + dirs[i])
                echo("mkdir", need_dir)
                os.makedirs(need_dir, exist_ok=True)
        for file in files:
            dest = os.path.normpath(target_dir + file)
            echo(f"cp {file} {dest}")
            shutil.copy(file, dest)

    @staticmethod
    def join_zips(zips):
        """
        https://stackoverflow.com/a/10593823/10068922

        Open the first zip file as append and then read all
        subsequent zip files and append to the first one
        """
        with ZipFile(zips[0], "a") as z1:
            for fname in zips[1:]:
                zf = ZipFile(fname, "r")
                for n in zf.namelist():
                    z1.writestr(n, zf.open(n).read())
