# flake8: noqa ANN201
import argparse
import os
import shutil
import subprocess
import sys
from types import SimpleNamespace
from venv import EnvBuilder

VENV_NAME = ".venv"

PLUGIN_DIR = os.getcwd()
ROOT_DIR = os.path.abspath(os.path.join(PLUGIN_DIR, os.pardir))
PLUGIN_NAME = os.path.basename(PLUGIN_DIR)

TEMPLATE_DIR = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "template")
)
TEMPLATE_ROOT_DIR = os.path.join(TEMPLATE_DIR, "root")
TEMPLATE_PLUGIN_DIR = os.path.join(TEMPLATE_DIR, "plugin")

ROOT_FILES = [
    ".qgis-plugin-ci",
    ".pre-commit-config.yaml",
    ".editorconfig",
    "setup.cfg",
    "requirements-dev.txt",
    "README.md",
    "LICENSE",
    ".gitignore",
    "docs/development.md",
    "docs/push_translations.yml",
    "CHANGELOG.md",
    ".github/workflows/tests.yml",
    ".github/workflows/release.yml",
    ".github/workflows/code-style.yml",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
]
PLUGIN_FILES = [
    "test/test_1.py",
    "test/__init__.py",
    "test/pytest.ini",
    "test/conftest.py",
    "metadata.txt",
    "build.py",
    "__init__.py",
    "plugin.py",
    ".gitattributes",
    "resources/ui/.gitignore",
    "resources/i18n/.gitignore",
    "resources/.gitignore",
    "resources/icons/.gitignore",
]

VENV_CREATION_SCRIPT = """
python -m venv --system-site-packages --clear {venv_path}
{source}{activator}
python -m pip install --upgrade pip
python -m pip install -r {requirements}
pre-commit install
"""


def is_windows():
    return "win" in sys.platform and "darwin" not in sys.platform


class PluginCreator:
    def __init__(self, organization: str, repo: str, url: str, venv: bool) -> None:
        self.organization = organization
        self.repo = repo
        self.url = url
        self.venv = venv

    def create(self):
        os.chdir(TEMPLATE_ROOT_DIR)
        for f in ROOT_FILES:
            self.copy_and_edit_file(ROOT_DIR, f)

        os.chdir(TEMPLATE_PLUGIN_DIR)
        for f in PLUGIN_FILES:
            self.copy_and_edit_file(PLUGIN_DIR, f)

    def create_venv(self):
        if not self.venv:
            print("Skipping venv creation")
            return
        try:
            from qgis.core import QgsVectorLayer
        except ImportError:
            print("Your python environment has no access to QGIS libraries!")
            return

        if is_windows():
            env = os.environ.copy()
            env[
                "PATH"
            ] += f';{os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Git", "cmd")}'
        else:
            env = os.environ

        print("Installing virtual environment")
        requirements = os.path.join(ROOT_DIR, "requirements-dev.txt")
        script = VENV_CREATION_SCRIPT.format(
            venv_path=os.path.join(ROOT_DIR, VENV_NAME),
            source="source " if not is_windows() else "",
            activator=os.path.join(
                ROOT_DIR,
                VENV_NAME,
                "bin" if not is_windows() else "Scripts",
                "activate",
            ),
            requirements=requirements,
        )

        process = subprocess.Popen(
            "cmd.exe" if is_windows() else "sh",
            shell=False,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env,
        )
        process.communicate(script)

    def copy_and_edit_file(self, dst_dir, f):
        print(f)
        dst_file = os.path.join(dst_dir, f)
        dst_file_dir = os.path.dirname(dst_file)
        if not os.path.exists(dst_file_dir):
            os.makedirs(dst_file_dir)
        shutil.copy2(f, dst_file)
        with open(dst_file) as fil:
            content = fil.read()
        content = (
            content.replace("<plugin_name>", PLUGIN_NAME)
            .replace("<organization>", self.organization)
            .replace("<repo>", self.repo)
            .replace("<url>", self.url)
            .replace("#<commented_out>", "")
            .replace("# <commented_out>", "")  # Automatic formatting might cause these
        )
        with open(dst_file, "w") as fil:
            fil.write(content)


def parse_args():
    parser = argparse.ArgumentParser(prog="PG Initializer")
    parser.add_argument(
        "-o",
        "--organization",
        help="Github / Gitlab organization or user name. "
        "For example GispoCoding in https://github.com/GispoCoding/GlobeBuilder",
        default="",
    )
    parser.add_argument(
        "-r",
        "--repository",
        help="Github / Gitlab repository name. "
        "For example GlobeBuilder in https://github.com/GispoCoding/GlobeBuilder",
        required=True,
    )
    parser.add_argument(
        "-u",
        "--url",
        help="Url of the repository hosting service. "
        "Typically https://github.com or https://gitlab.com",
        default="https://github.com",
    )
    parser.add_argument(
        "--venv", action="store_true", help="Create Python virtual environment"
    )

    if "-" in PLUGIN_NAME or " " in PLUGIN_NAME:
        raise ValueError(f"Plugin name {PLUGIN_NAME} contains illegal characters")

    return parser.parse_args()


def create_plugin():
    args = parse_args()
    creator = PluginCreator(args.organization, args.repository, args.url, args.venv)
    creator.create()
    creator.create_venv()
