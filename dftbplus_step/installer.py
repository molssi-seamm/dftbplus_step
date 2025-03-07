# -*- coding: utf-8 -*-

"""Installer for the DFTB+ plug-in.

This handles any further installation needed after installing the Python
package `dftbplus-step`.
"""

import logging
from pathlib import Path
import pkg_resources
import subprocess

import seamm_installer

logger = logging.getLogger(__name__)


class Installer(seamm_installer.InstallerBase):
    """Handle further installation needed after installing dftbplus-step.

    The Python package `dftbplus-step` should already be installed, using `pip`,
    `conda`, or similar. This plug-in-specific installer then checks for the
    Dftbplus executable, installing it if needed, and registers its
    location in ~/SEAMM/dftbplus.ini.

    There are a number of ways to determine which are the correct Dftbplus
    executables to use. The aim of this installer is to help the user locate
    the executables. There are a number of possibilities:

    1. The correct executables are already available.

        1. If they are already registered in `dftbplus.ini` there is nothing else
           to do.
        2. They may be in the current path, in which case they need to be added
           to `dftbplus.ini`.
        3. If a module system is in use, a module may need to be loaded to give
           access to Dftbplus.
        4. They cannot be found automatically, so the user needs to locate the
           executables for the installer.

    2. Dftbplus is not installed on the machine. In this case they can be
       installed in a Conda environment. There is one choice:

        1. They can be installed in a separate environment, `seamm-dftbplus` by
           default.
    """

    def __init__(self, logger=logger):
        # Call the base class initialization, which sets up the commandline
        # parser, amongst other things.
        super().__init__(logger=logger)

        logger.debug("Initializing the Dftbplus installer object.")

        # Define this step's details
        self.environment = "seamm-dftbplus"
        self.section = "dftbplus-step"
        self.executables = ["dftb+"]
        self.resource_path = Path(pkg_resources.resource_filename(__name__, "data/"))

        # The environment.yaml file for Conda installations.
        logger.debug(f"data directory: {self.resource_path}")
        self.environment_file = self.resource_path / "seamm-dftbplus.yml"

    def exe_version(self, data):
        """Get the version of the Dftbplus executable.

        Parameters
        ----------
        data : {str: any}
            Data about how to run

        Returns
        -------
        str
            The version reported by the executable, or 'unknown'.
        """
        version = "unknown"
        if data["installation"] == "conda":
            try:
                cmd = [
                    data["conda"],
                    "run",
                    "-n",
                    data["conda-environment"],
                    data["code"],
                    " --version",
                ]
                result = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                version = "unknown"
            else:
                version = "unknown"
                lines = result.stdout.splitlines()
                for line in lines:
                    line = line.strip()
                    tmp = line.split()
                    if len(tmp) == 4 and tmp[2] == "release":
                        version = tmp[3]
                        break
        elif data["installation"] == "local":
            cmd = [data["code"], "--version"]
            try:
                result = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                version = "unknown"
            else:
                version = "unknown"
                lines = result.stdout.splitlines()
                for line in lines:
                    line = line.strip()
                    tmp = line.split()
                    if len(tmp) == 4 and tmp[2] == "release":
                        version = tmp[3]
                        break
        else:
            print(f"Cannot yet handle running as {data['installation']}.")

        return "DFTB+", version
