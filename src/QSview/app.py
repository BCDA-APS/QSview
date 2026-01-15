#!/usr/bin/env python

"""
QSview: Python Qt5 application to control Bluesky Queue Server.

.. autosummary::

    ~gui
    ~main
"""

import logging
import sys

from PyQt5 import QtWidgets

from .mainwindow import MainWindow

logger = None  # to be set by main() from command line option


def gui():
    """Display the main window"""

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setMessage("Application started ...")
    main_window.show()
    sys.exit(app.exec())


def command_line_interface():
    """Parse command-line arguments."""
    import argparse

    from . import __version__

    doc = __doc__.strip().splitlines()[0]
    parser = argparse.ArgumentParser(description=doc)

    # fmt: off
    try:
        choices = [k.lower() for k in logging.getLevelNamesMapping()]
    except AttributeError:
        choices = "critical fatal error warning info debug".split()  # Py < 3.11
    parser.add_argument(
        "--log",
        default="warning",
        help=(
            "Provide logging level. "
            "Example '--log debug'. "
            "Default level: 'warning'"),
        choices=choices,
    )
    # fmt: on

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def main():
    """Command-line entry point."""
    global logger

    options = command_line_interface()

    logging.basicConfig(level=options.log.upper())
    logger = logging.getLogger(__name__)
    logger.info("Logging level: %s", options.log)

    # Silence noisy third-party loggers
    for package in "PyQt5 bluesky_queueserver".split():
        logging.getLogger(package).setLevel(logging.WARNING)

    gui()


if __name__ == "__main__":
    main()
