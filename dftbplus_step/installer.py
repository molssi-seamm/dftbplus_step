# -*- coding: utf-8 -*-

"""Installer for the DFTB+ plug-in.

This handles any further installation needed after installing the Python
package `dftbplus-step`.
"""

import logging
from pathlib import Path
import pkg_resources
import requests
import shutil
import subprocess
import tarfile
import tempfile

import seamm_installer
import seamm_util

logger = logging.getLogger(__name__)


class Installer(seamm_installer.InstallerBase):
    """Handle further installation needed after installing dftbplus-step.

    The Python package `dftbplus-step` should already be installed, using `pip`,
    `conda`, or similar. This plug-in-specific installer then checks for the
    Dftbplus executable, installing it if needed, and registers its
    location in seamm.ini.

    There are a number of ways to determine which are the correct Dftbplus
    executables to use. The aim of this installer is to help the user locate
    the executables. There are a number of possibilities:

    1. The correct executables are already available.

        1. If they are already registered in `seamm.ini` there is nothing else
           to do.
        2. They may be in the current path, in which case they need to be added
           to `seamm.ini`.
        3. If a module system is in use, a module may need to be loaded to give
           access to Dftbplus.
        4. They cannot be found automatically, so the user needs to locate the
           executables for the installer.

    2. Dftbplus is not installed on the machine. In this case they can be
       installed in a Conda environment. There is one choice:

        1. They can be installed in a separate environment, `seamm-dftbplus` by
           default.

    The Slater-Koster potentials also need to be installed if not present. They are
    placed in ~/SEAMM/Parameters/slako by default.
    """

    def __init__(self, logger=logger):
        # Call the base class initialization, which sets up the commandline
        # parser, amongst other things.
        super().__init__(logger=logger)

        logger.debug("Initializing the Dftbplus installer object.")

        self.section = "dftbplus-step"
        self.path_name = "dftbplus-path"
        self.executables = ["dftb+"]
        self.resource_path = Path(pkg_resources.resource_filename(__name__, "data/"))

        self.slako_url = "https://dftb.org/fileadmin/DFTB/public/slako-unpacked.tar.xz"

        # What Conda environment is the default?
        data = self.configuration.get_values(self.section)
        if "conda-environment" in data and data["conda-environment"] != "":
            self.environment = data["conda-environment"]
        else:
            self.environment = "seamm-dftbplus"

        # The environment.yaml file for Conda installations.
        path = Path(pkg_resources.resource_filename(__name__, "data/"))
        logger.debug(f"data directory: {path}")
        self.environment_file = path / "seamm-dftbplus.yml"

    def check(self):
        """Check the installation and fix errors if requested.

        If the option `yes` is present and True, this method will attempt to
        correct any errors in the configuration file. Use `--yes` on the
        command line to enable this.

        The base class handles the DFTB+ executable, ensuring that the following
        is in the [dftbplus] section of the configuration file.

            installation
                How the executables are installed. One of `user`, `modules` or `conda`
            conda-environment
                The Conda environment if and only if `installation` = `conda`
            modules
                The environment modules if `installation` = `modules`
            {self.path_name}
                The path where the executables are. Automatically
                defined if `installation` is `conda` or `modules`, but given
                by the user is it is `user`.

        In addition, this method checks for the Slater-Koster parameters sets,
        installing them if needed and requested.

        Returns
        -------
        bool
            True if everything is OK, False otherwise. If `yes` is given as an
            option, the return value is after fixing the configuration.
        """
        # Check the DFTB+ executable
        result = super().check()

        # And the Slater-Koster parameter files.
        self.logger.debug("Checking the Slater-Koster parameters.")

        # First read in the configuration file in the normal fashion
        # to get the root directory (~/SEAMM usually), which may be needed.
        parser = seamm_util.seamm_parser()
        parser.parse_args([])
        options = parser.get_options("SEAMM")
        root = Path(options["root"]).expanduser().resolve()

        # Get the values from the configuration
        data = self.configuration.get_values(self.section)
        if "slako-dir" in data and data["slako-dir"] != "":
            tmp = data["slako-dir"].replace("${root:SEAMM}", str(root))
            slako_dir = Path(tmp).expanduser().resolve()
            have_key = True
        else:
            slako_dir = root / "Parameters" / "slako"
            have_key = False

        install = "no"
        if not slako_dir.exists():
            standard_dir = root / "Parameters" / "slako"
            if slako_dir != standard_dir:
                if standard_dir.exists():
                    if self.options.yes or self.ask_yes_no(
                        f"The directory for the Slater-Koster files, '{slako_dir}', "
                        "does not exist but it does exist in the standard location "
                        f"'{standard_dir}'.\nUse the standard directory?",
                        default="yes",
                    ):
                        install = "check contents"
                        slako_dir = standard_dir
            if install != "check contents" and (
                self.options.yes
                or self.ask_yes_no(
                    f"The directory for the Slater-Koster files, '{slako_dir}', "
                    "does not exist.\nCreate it and install the Slater-Koster "
                    "files?",
                    default="yes",
                )
            ):
                install = "full"
        else:
            install = "check contents"
            if not have_key:
                if self.options.yes or self.ask_yes_no(
                    f"The location of the Slater-Koster files, '{slako_dir}', is not "
                    "registered in the configuration file.\nDo you want to correct "
                    "this?",
                    default="yes",
                ):
                    self.configuration.set_value(
                        self.section, "slako-dir", str(slako_dir)
                    )
                    self.configuration.save()

        if install == "check contents":
            # How do we do this? Check files, versions, what?
            print(
                "At this time, this install is not able  to check the individual files"
                "\nto see if they are up-to-date or not. Updating currently forces an "
                "update."
            )
        elif install == "full":
            self.install_files(slako_dir)
            self.configuration.set_value(self.section, "slako-dir", str(slako_dir))
            self.configuration.save()
            print("Done!\n")
        else:
            result = False

        return result

    def exe_version(self, path):
        """Get the version of the Dftbplus executable.

        Parameters
        ----------
        path : pathlib.Path
            Path to the executable.

        Returns
        -------
        str
            The version reported by the executable, or 'unknown'.
        """
        try:
            result = subprocess.run(
                [str(path), "--version"],
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

        return version

    def install_files(self, location):
        """Install the Slater-Koster files and update the configuration if needed.

        Parameters
        ----------
        location: Path
           The directory for the installed files.
        """

        filename = "slako-unpacked.tar.xz"
        with tempfile.TemporaryDirectory() as tmpdirname:
            path = Path(tmpdirname) / filename
            print(f"Getting the Slater-Koster files from {self.slako_url}.")
            # Download the Slater-Koster files
            response = requests.get(url=self.slako_url, stream=True)
            with open(path, "wb") as output:
                for chunk in response.iter_content(chunk_size=10240):
                    output.write(chunk)

            print(f"Done!\nNow unpacking the tarfile to {location}.")

            # Now unpack the contents
            contents = tarfile.open(path)

            contents.extractall(location.parent)

    def install(self):
        """Install DFTB+ and the Slater-Koster files

        The base class handles the DFTB+ executable, ensuring that the following
        is in the [dftbplus] section of the configuration file.

            installation
                How the executables are installed. One of `user`, `modules` or `conda`
            conda-environment
                The Conda environment if and only if `installation` = `conda`
            modules
                The environment modules if `installation` = `modules`
            {self.path_name}
                The path where the executables are. Automatically
                defined if `installation` is `conda` or `modules`, but given
                by the user is it is `user`.

        In addition, this method installs the Slater-Koster parameters sets and sets
        `slako-dir` in the [dftbplus] section of the configuration file.
        """
        # Install the DFTB+ executable
        super().install()

        # And the Slater-Koster parameter files.
        self.logger.debug("Installing the Slater-Koster parameters.")

        # First read in the configuration file in the normal fashion
        # to get the root directory (~/SEAMM usually), which may be needed.
        parser = seamm_util.seamm_parser()
        parser.parse_args([])
        options = parser.get_options("SEAMM")
        root = Path(options["root"]).expanduser().resolve()

        # Get the values from the configuration
        data = self.configuration.get_values(self.section)
        if "slako-dir" in data and data["slako-dir"] != "":
            tmp = data["slako-dir"].replace("${root:SEAMM}", str(root))
            slako_dir = Path(tmp).expanduser().resolve()
        else:
            slako_dir = root / "Parameters" / "slako"

        print(f"Installing the Slater-Koster files to {slako_dir}.")
        slako_dir.parent.mkdir(parents=True, exist_ok=True)
        self.install_files(slako_dir)

        self.configuration.set_value(self.section, "slako-dir", str(slako_dir))
        self.configuration.save()

        print("Done!\n")

    def uninstall(self):
        """Uninstall DFTB+ and the Slater-Koster files

        The base class handles the DFTB+ executable, ensuring that the following
        is in the [dftbplus] section of the configuration file.

            installation
                How the executables are installed. One of `user`, `modules` or `conda`
            conda-environment
                The Conda environment if and only if `installation` = `conda`
            modules
                The environment modules if `installation` = `modules`
            {self.path_name}
                The path where the executables are. Automatically
                defined if `installation` is `conda` or `modules`, but given
                by the user is it is `user`.

        In addition, this method uninstalls the Slater-Koster parameters sets and sets
        `slako-dir` to null in the [dftbplus] section of the configuration file.
        """
        # Uninstall the DFTB+ executable
        super().uninstall()

        # And the Slater-Koster parameter files.
        self.logger.debug("Uninstalling the Slater-Koster parameters.")

        # Get the values from the configuration
        data = self.configuration.get_values(self.section)
        if "slako-dir" in data and data["slako-dir"] != "":
            # First read in the configuration file in the normal fashion
            # to get the root directory (~/SEAMM usually), which may be needed.
            parser = seamm_util.seamm_parser()
            parser.parse_args([])
            options = parser.get_options("SEAMM")
            root = Path(options["root"]).expanduser().resolve()

            tmp = data["slako-dir"].replace("${root:SEAMM}", str(root))
            slako_dir = Path(tmp).expanduser().resolve()

            print(f"Deleting the Slater-Koster files in {slako_dir}.")
            print(f"{data['slako-dir']=}")

            shutil.rmtree(slako_dir, ignore_errors=True)

            self.configuration.set_value(self.section, "slako-dir", "")
            self.configuration.save()
            print("Done!\n")
        else:
            print("The Slater-Koster files were not installed, so nothing to do.")

    def update(self):
        """Update DFTB+ and the Slater-Koster files

        The base class handles the DFTB+ executable, ensuring that the following
        is in the [dftbplus] section of the configuration file.

            installation
                How the executables are installed. One of `user`, `modules` or `conda`
            conda-environment
                The Conda environment if and only if `installation` = `conda`
            modules
                The environment modules if `installation` = `modules`
            {self.path_name}
                The path where the executables are. Automatically
                defined if `installation` is `conda` or `modules`, but given
                by the user is it is `user`.

        In addition, this method updates the Slater-Koster parameters sets.
        """
        # Update the DFTB+ executable
        super().update()

        # And the Slater-Koster parameter files.
        self.logger.debug("Updating the Slater-Koster parameters.")

        # Get the values from the configuration
        data = self.configuration.get_values(self.section)
        if "slako-dir" in data and data["slako-dir"] != "":
            # First read in the configuration file in the normal fashion
            # to get the root directory (~/SEAMM usually), which may be needed.
            parser = seamm_util.seamm_parser()
            parser.parse_args([])
            options = parser.get_options("SEAMM")
            root = Path(options["root"]).expanduser().resolve()

            tmp = data["slako-dir"].replace("${root:SEAMM}", str(root))
            slako_dir = Path(tmp).expanduser().resolve()

            if not slako_dir.exists():
                print(
                    f"The Slater-Koster files are not installed at {slako_dir}, "
                    "\nwhere the configuration file indicates they should be."
                    "\nFixing the configuration file."
                )
                self.configuration.set_value(self.section, "slako-dir", "")
                self.configuration.save()
            else:
                print(f"Updating the Slater-Koster files in {slako_dir}.")
                slako_dir.parent.mkdir(parents=True, exist_ok=True)
                self.install_files(slako_dir)

            print("Done!\n")
        else:
            print(
                "The Slater-Koster files do not appear to be installed, so doing "
                "nothing."
            )
