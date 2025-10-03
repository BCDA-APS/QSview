"""
Define constants used throughout the code.
"""

import pathlib

__settings_orgName__ = "BCDA-APS"
__package_name__ = "QSviz"
__version__ = (
    "0.0.1"  # extract_version(Path(__file__).parent.parent / "pyproject.toml")
)


ROOT_DIR = pathlib.Path(__file__).parent
UI_DIR = ROOT_DIR / "resources"

APP_DESC = "QSviz: Graphical interface to control the Bluesky Queue Server."
APP_TITLE = __package_name__
AUTHOR_LIST = [
    s.strip()
    for s in """
        Eric Codrea
        Ollivier Gassant
        Pete Jemian
        Fanny Rodolakis
        Rafael Vescovi
    """.strip().splitlines()
]

COPYRIGHT_TEXT = "(c) 2023, UChicago Argonne, LLC, (see LICENSE file for details)"
DOCS_URL = "https://github.com/BCDA-APS/QSviz/blob/main/README.md"
ISSUES_URL = "https://github.com/BCDA-APS/QSviz/issues"
LICENSE_FILE = "LICENSE.txt"
VERSION = __version__
