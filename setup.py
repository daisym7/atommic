# coding=utf-8
# ! /usr/bin/python
import importlib.util
import subprocess
import sys
from pathlib import Path

import setuptools
from setuptools import Command
from setuptools import logging as setuptools_logging

__author__ = "Dimitris Karkalousos"


spec = importlib.util.spec_from_file_location("package_info", "atommic/package_info.py")
package_info = importlib.util.module_from_spec(spec)  # type: ignore
spec.loader.exec_module(package_info)  # type: ignore

__contact_emails__ = package_info.__contact_emails__
__contact_names__ = package_info.__contact_names__
__description__ = package_info.__description__
__download_url__ = package_info.__download_url__
__homepage__ = package_info.__homepage__
__keywords__ = package_info.__keywords__
__license__ = package_info.__license__
__package_name__ = package_info.__package_name__
__repository_url__ = package_info.__repository_url__
__version__ = package_info.__version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
long_description_content_type = "text/markdown"


###############################################################################
#                             Dependency Loading                              #
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% #


def _load_requirements(requirements_file, folder="requirements"):
    """Load requirements from a file."""
    requirements = []
    with open(Path(folder) / Path(requirements_file), "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements


install_requires = _load_requirements("requirements.txt")


###############################################################################
#                            Code style checkers                              #
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% #


class StyleCommand(Command):
    """Run code style checkers."""

    __LINE_WIDTH = 119
    __ISORT_BASE = (
        "isort "
        # These two lines makes isort compatible with black.
        "--multi-line=3 --trailing-comma --force-grid-wrap=0 "
        f"--use-parentheses --line-width={__LINE_WIDTH} -rc -ws"
    )
    __BLACK_BASE = f"black --skip-string-normalization --line-length={__LINE_WIDTH}"
    description = "Run code style checkers."
    user_options = [
        ("scope=", None, "Folder of file to operate within."),
        ("fix", None, "True if tries to fix issues in-place."),
    ]

    def __call_checker(self, base_command, scope, check):
        command = list(base_command)

        command.append(scope)

        if check:
            command.extend(["--check", "--diff"])

        self.announce(msg=f'Running command: {" ".join(command)}', level=setuptools_logging.INFO)

        return subprocess.call(command)

    def _isort(self, scope, check):
        return self.__call_checker(base_command=self.__ISORT_BASE.split(), scope=scope, check=check)

    def _black(self, scope, check):
        return self.__call_checker(base_command=self.__BLACK_BASE.split(), scope=scope, check=check)

    def _pass(self):
        self.announce(msg="\033[32mPASS\x1b[0m", level=setuptools_logging.INFO)

    def _fail(self):
        self.announce(msg="\033[31mFAIL\x1b[0m", level=setuptools_logging.INFO)

    # noinspection PyAttributeOutsideInit
    def initialize_options(self):
        self.scope = "."
        self.fix = ""

    def run(self):
        scope, check = self.scope, not self.fix
        isort_return = self._isort(scope=scope, check=check)
        black_return = self._black(scope=scope, check=check)

        if isort_return == 0 and black_return == 0:
            self._pass()
        else:
            self._fail()
            sys.exit(isort_return if isort_return != 0 else black_return)

    def finalize_options(self):
        raise NotImplementedError()


###############################################################################
#                             Setup                                           #
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% #


setuptools.setup(
    name=__package_name__,
    # Versions should comply with PEP440.  For a discussion on single-sourcing the version across setup.py and the
    # project code, see https://packaging.python.org/en/latest/single_source_version.html
    version=__version__,
    description=__description__,
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    # The project's main homepage.
    url=__repository_url__,
    download_url=__download_url__,
    # Author details
    author=__contact_names__,
    author_email=__contact_emails__,
    # maintainer Details
    maintainer=__contact_names__,
    maintainer_email=__contact_emails__,
    # The licence under which the project is released
    license=__license__,
    classifiers=[
        # How mature is this project? Common values are
        #  1 - Planning
        #  2 - Pre-Alpha
        #  3 - Alpha
        #  4 - Beta
        #  5 - Production/Stable
        #  6 - Mature
        #  7 - Inactive
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        # Indicate what your project relates to
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: Apache Software License",
        # Supported python versions
        "Programming Language :: Python :: 3.10",
        # Additional Setting
        "Environment :: Console",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(include=["atommic", "atommic.*"]),
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    python_requires=">=3.10, <=3.12",
    # Add in any packaged data.
    include_package_data=True,
    exclude=["tools", "tests"],
    package_data={"": ["*.tsv", "*.txt", "*.far", "*.fst", "*.cpp", "Makefile"]},
    zip_safe=False,
    # PyPI package information.
    keywords=__keywords__,
    # Custom commands.
    cmdclass={"style": StyleCommand},
    # entry points
    entry_points={
        "console_scripts": [
            "atommic = atommic.cli:main",
        ],
    },
)

###############################################################################
#                             End of File                                    #
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% #