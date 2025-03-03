# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""Handle the installation of the DFTB+ step."""

from .installer import Installer


def run():
    """Handle the extra installation needed.

    * Find and/or install the dftb+ executable.
    * Add or update information in the dftbplus.ini file for DFTB+
    """

    # Create an installer object
    installer = Installer()
    installer.run()


if __name__ == "__main__":
    run()
