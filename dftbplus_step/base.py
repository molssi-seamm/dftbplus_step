# -*- coding: utf-8 -*-

"""Non-graphical part of the DFTB+ step in a SEAMM flowchart
"""

import copy

import logging
from pathlib import Path
import pprint
import shutil
import subprocess
import traceback

import pandas
import psutil

import cms_plots
import dftbplus_step
from .dftbplus import deep_merge, dict_to_hsd, parse_gen_file
from molsystem.elements import to_symbols
import seamm
import seamm_util.printing as printing

# In addition to the normal logger, two logger-like printing facilities are
# defined: 'job' and 'printer'. 'job' send output to the main job.out file for
# the job, and should be used very sparingly, typically to echo what this step
# will do in the initial summary of the job.
#
# 'printer' sends output to the file 'step.out' in this steps working
# directory, and is used for all normal output from this step.

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("DFTB+")


def redimension(values, dimensions):
    """Change the dimensions on values to the new dimensions.

    Parameters
    ----------
    values : []
        The incoming values
    dimensions : [int]
        The desired dimensions

    Returns
    -------
    values : [[]...]
        The redimensioned values.
    """
    # Check that the number of values is OK
    nvalues = 1
    for dim in dimensions:
        nvalues *= dim
    if len(values) != nvalues:
        raise ValueError(
            f"Number of values given, {len(values)}, is not equal to the "
            f"dimensions: {dimensions} --> {nvalues} values"
        )
    try:
        _, result = _redimension_helper(values, dimensions)
    except Exception as e:
        print(f"Exception in redimension {type(e)}: {e}")
        print(traceback.format_exc())
        raise

    return result


def _redimension_helper(values, dimensions):
    dim = dimensions[-1]
    remaining = dimensions[0:-1]
    if len(remaining) == 0:
        return values[dim:], values[0:dim]
    else:
        result = []
        for i in range(dim):
            values, tmp = _redimension_helper(values, remaining)
            result.append(tmp)
    return values, result


class DftbBase(seamm.Node):
    """A base class for substeps in the DFTB+ step."""

    def __init__(
        self, flowchart=None, title="Choose Parameters", extension=None, logger=logger
    ):
        self.mapping_from_primitive = None
        self.mapping_to_primitive = None
        self.results = None  # Results of the calculation from the tag file.

        super().__init__(flowchart=flowchart, title=title, extension=extension)

    @property
    def is_runable(self):
        """Indicate whether this not runs or just adds input."""
        return True

    def band_structure(
        self, input_path, sym_points, sym_names, Efermi=[0.0, 0.0], DOS=None
    ):
        """Prepare the graph for the band structure.

        Parameters
        ----------
        path : filename or pathlib.Path
            The path to the band output from DFTB+.
        """
        Band_Structure = self.create_band_structure_data(  # noqa: F841
            input_path, sym_points, sym_names, Efermi=Efermi
        )

        figure = cms_plots.band_structure(
            Band_Structure, DOS=DOS, template="band_structure.graph_template"
        )

        # Write it out.
        wd = Path(self.directory)
        figure.dump(wd / "band_structure.graph")

        options = self.parent.options
        write_html = "html" in options and options["html"]
        if write_html:
            figure.template = "band_structure.html_template"
            figure.dump(wd / "band_structure.html")

    def create_band_structure_data(
        self, input_path, sym_points, sym_names, Efermi=[0.0, 0.0]
    ):
        """Massage the band structure data into a standard form

        Parameters
        ----------
        path : filename or pathlib.Path
            The path to the band output from DFTB+.
        """
        wd = Path(self.directory)
        logger.info(f"Preparing the band structure, {wd}")

        spin_polarized = len(Efermi) == 2
        options = self.parent.options
        exe = Path(options["dftbplus_path"]) / "dp_bands"

        band_path = str(wd / "band")
        if spin_polarized:
            command = f"'{exe}' -s '{input_path}' '{band_path}'"
        else:
            command = f"'{exe}' '{input_path}' '{band_path}'"
        try:
            subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Calling dp_band, returncode = {e.returncode}")
            logger.warning(f"Output: {e.output}")
            return None

        if spin_polarized:
            # Read the spin-up data
            with open(wd / "band_s1.dat", "r") as fd:
                BandStructure = pandas.read_csv(
                    fd,
                    sep=r"\s+",
                    header=None,
                    index_col=0,
                    comment="!",
                )

            mapper = {}
            i = 0
            for column in BandStructure.columns:
                i += 1
                mapper[column] = f"↑ {i}"
                BandStructure[column] -= Efermi[0]
            BandStructure.rename(columns=mapper, inplace=True)

            # Read the spin-up data
            with open(wd / "band_s2.dat", "r") as fd:
                data = pandas.read_csv(
                    fd,
                    sep=r"\s+",
                    header=None,
                    index_col=0,
                    comment="!",
                )

            i = 0
            for column in data.columns:
                i += 1
                label = f"↓ {i}"
                BandStructure[label] = data[column] - Efermi[1]
        else:
            # Read the plot data
            with open(wd / "band_tot.dat", "r") as fd:
                BandStructure = pandas.read_csv(
                    fd,
                    sep=r"\s+",
                    header=None,
                    index_col=0,
                    comment="!",
                )

            mapper = {}
            i = 0
            for column in BandStructure.columns:
                i += 1
                mapper[column] = f"{i}"
                BandStructure[column] -= Efermi[0]
            BandStructure.rename(columns=mapper, inplace=True)

        # Insert a column of labels
        nrows = BandStructure.index.size
        labels = [""] * nrows
        for pt, label in zip(sym_points, sym_names):
            labels[pt - 1] = label
        BandStructure.insert(0, "labels", labels)

        # And labels for each point in the path
        BandStructure.insert(1, "points", self.path)

        BandStructure.to_csv(Path(self.directory) / "BandStructure.csv")

        return BandStructure

    def create_dos_data(self, input_path, Efermi=[0.0]):
        """Create the DOS data

        Parameters
        ----------
        input_path : filename or pathlib.Path
            The path to the band output from DFTB+.
        Efermi : float
            The Fermi energy in eV
        """
        spin_polarized = len(Efermi) == 2

        if spin_polarized and Efermi[0] != Efermi[1]:
            raise NotImplementedError(
                f"Cannot handle different Fermi energies yet: {Efermi}"
            )

        logger.info("Preparing DOS")

        options = self.parent.options

        # Total DOS
        wd = Path(self.directory)
        exe = Path(options["dftbplus_path"]) / "dp_dos"
        dat_file = str(wd / "dos_total.dat")
        command = f"'{exe}' '{input_path}' '{dat_file}'"
        try:
            subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Calling dp_dos, returncode = {e.returncode}")
            logger.warning(f"Output: {e.output}")
            return None

        # Read the total DOS data
        with open(wd / "dos_total.dat", "r") as fd:
            DOS = pandas.read_csv(
                fd,
                sep=r"\s+",
                header=None,
                comment="!",
                index_col=0,
            )

        n_columns = DOS.shape[1]
        if n_columns == 1:
            if spin_polarized:
                raise RuntimeError(
                    "Calculation is spin-polarized but total DOS is not."
                )
            DOS.rename(columns={0: "E", 1: "Total"}, inplace=True)
        elif n_columns == 3:
            if not spin_polarized:
                raise RuntimeError(
                    "Calculation is not spin-polarized but total DOS is."
                )
            DOS.rename(
                columns={0: "E", 1: "Total", 2: "Total ↑", 3: "Total ↓"},
                inplace=True,
            )
        else:
            raise RuntimeError(f"The total DOS has {n_columns} columns of data.")

        # Partial DOS convention is "pdos_{element}.{shell no}.out"
        # Figure out the elements and files for each.
        files = {}
        for path in sorted(wd.glob("pdos*.out")):
            element = path.stem.split("_")[1].split(".")[0]
            if element not in files:
                files[element] = [path]
            else:
                files[element].append(path)

        # Process each element, accumulating the total
        for element, paths in files.items():
            if spin_polarized:
                total_up = None
                total_down = None
            else:
                total = None
            for path in paths:
                out = path.with_suffix(".dat")
                shell_no = int(path.suffixes[0][1:])
                shell = ("s", "p", "d", "f")[shell_no - 1]
                label = element + "_" + shell

                command = f"'{exe}' -w '{path}' '{out}'"
                try:
                    subprocess.check_output(
                        command, shell=True, text=True, stderr=subprocess.STDOUT
                    )
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Calling dp_dos, returncode = {e.returncode}")
                    logger.warning(f"Output: {e.output}")
                    continue

                # Read the plot data
                with open(out, "r") as fd:
                    data = pandas.read_csv(
                        fd,
                        sep=r"\s+",
                        header=None,
                        comment="!",
                        index_col=0,
                    )

                n_columns = data.shape[1]
                if n_columns == 1:
                    if spin_polarized:
                        raise RuntimeError(
                            f"Calculation is spin-polarized but {path} is not."
                        )
                    data.rename(columns={0: "E", 1: label}, inplace=True)

                    # Check the bounds. Sometimes rounding causes different grid sizes.
                    tmp = data.index.isin(DOS.index)
                    if not tmp.all():
                        data = data.loc[tmp]
                    tmp = DOS.index.isin(data.index)
                    if not tmp.all():
                        DOS = DOS.loc[tmp]
                        if total is not None:
                            total = total.loc[tmp]

                    if total is None:
                        total = data[label]
                    else:
                        total += data[label]

                    if not DOS.index.equals(data.index):
                        raise RuntimeError(
                            f"The energy values for partial DOS {label} are  different!"
                            f" ({out})"
                        )

                    DOS[label] = data[label].array
                elif n_columns == 3:
                    if not spin_polarized:
                        raise RuntimeError(
                            f"Calculation is not spin-polarized but {path} is."
                        )
                    data.rename(
                        columns={0: "E", 1: "Total", 2: "Up", 3: "Down"}, inplace=True
                    )
                    # Check the bounds.
                    tmp = data.index.isin(DOS.index)
                    if not tmp.all():
                        data = data.loc[tmp]
                    tmp = DOS.index.isin(data.index)
                    if not tmp.all():
                        DOS = DOS.loc[tmp]
                        if total_up is not None:
                            total_up = total_up.loc[tmp]
                            total_down = total_down.loc[tmp]
                    if total_up is None:
                        total_up = data["Up"]
                        total_down = data["Down"]
                    else:
                        total_up += data["Up"]
                        total_down += data["Down"]

                    if not DOS.index.equals(data.index):
                        raise RuntimeError(
                            f"The energy values for partial DOS {label} are  different!"
                            f" ({out})"
                        )
                    DOS[label + " ↑"] = data["Up"].array
                    DOS[label + " ↓"] = data["Down"].array
                else:
                    raise RuntimeError(f"The {path} has {n_columns} columns of data.")

            if spin_polarized:
                DOS[element + " ↑"] = total_up.array
                DOS[element + " ↓"] = total_down.array
            else:
                DOS[element] = total.array

        # Shift the Fermi level to 0
        DOS.index -= Efermi[0]

        DOS.to_csv(Path(self.directory) / "DOS.csv")

        return DOS

    def dos(self, input_path, Efermi=[0.0]):
        """Prepare the graph for the density of states.

        Parameters
        ----------
        input_path : filename or pathlib.Path
            The path to the band output from DFTB+.
        Efermi : float
            The Fermi energy in eV
        """
        DOS = self.create_dos_data(input_path, Efermi=Efermi)

        figure = cms_plots.dos(DOS, template="line.graph_template")

        # Write it out.
        figure.dump(Path(self.directory) / "DOS.graph")

        options = self.parent.options
        write_html = "html" in options and options["html"]
        if write_html:
            figure.template = "line.html_template"
            figure.dump(Path(self.directory) / "DOS.html")

    def geometry(self):
        """Create the input for DFTB+ for the geometry.

        Example::

            Geometry = {
                TypeNames = { "Ga" "As" }
                TypesAndCoordinates [Angstrom] = {
                    1 0.000000 0.000000 0.000000
                    2 1.356773 1.356773 1.356773
                }
                Periodic = Yes
                LatticeVectors [Angstrom] = {
                    2.713546 2.713546 0.
                    0. 2.713546 2.713546
                    2.713546 0. 2.713546
                }
            }
        """
        _, configuration = self.get_system_configuration(None)

        result = "Geometry = {\n"

        elements = set(configuration.atoms.symbols)
        elements = sorted([*elements])
        names = '{"' + '" "'.join(elements) + '"}'
        result += f"   TypeNames = {names}\n"

        if configuration.periodicity == 0:
            result += "    TypesAndCoordinates [Angstrom] = {\n"
            for element, xyz in zip(
                configuration.atoms.symbols,
                configuration.atoms.get_coordinates(fractionals=False),
            ):
                index = elements.index(element)
                x, y, z = xyz
                result += f"        {index+1:>2} {x:10.6f} {y:10.6f} {z:10.6f}\n"
            result += "    }\n"

            # The reference energy, if available
            if self.parent._reference_energies is None:
                self.parent._reference_energy = None
            else:
                energy = 0.0
                for el in configuration.atoms.symbols:
                    energy += self.parent._reference_energies[el]
                self.parent._reference_energy = energy
        elif configuration.periodicity == 3:
            if "primitive cell" in self.parameters:
                use_primitive_cell = self.parameters["primitive cell"].get(
                    context=seamm.flowchart_variables._data
                )
            else:
                use_primitive_cell = True

            if use_primitive_cell:
                # Write the structure using the primitive cell
                (
                    lattice,
                    fractionals,
                    atomic_numbers,
                    self.mapping_from_primitive,
                    self.mapping_to_primitive,
                ) = configuration.primitive_cell()
            else:
                # Use the full cell
                lattice = configuration.cell.vectors()
                fractionals = configuration.atoms.get_coordinates(fractionals=True)
                atomic_numbers = configuration.atoms.atomic_numbers

                n_atoms = len(atomic_numbers)
                self.mapping_from_primitive = [i for i in range(n_atoms)]
                self.mapping_to_primitive = [i for i in range(n_atoms)]
            symbols = to_symbols(atomic_numbers)

            result += "   Periodic = Yes\n"
            result += "   LatticeVectors [Angstrom] = {\n"

            for xyz in lattice:
                x, y, z = xyz
                result += f"        {x:15.9f} {y:15.9f} {z:15.9f}\n"
            result += "    }\n"
            result += "    TypesAndCoordinates [relative] = {\n"
            for element, xyz in zip(symbols, fractionals):
                index = elements.index(element)
                x, y, z = xyz
                result += f"        {index+1:>2} {x:15.9f} {y:15.9f} {z:15.9f}\n"
            result += "    }\n"

            # The reference energy, if available
            if self.parent._reference_energies is None:
                self.parent._reference_energy = None
            else:
                energy = 0.0
                for el in symbols:
                    energy += self.parent._reference_energies[el]
                self.parent._reference_energy = energy

        result += "}\n"

        return result

    def find_previous_step(self, cls, missing_ok=False):
        """Find the previous step of class 'cls'

        Parameters
        ----------
        cls : class
            The class of the desired step.
        missing_ok : bool = False
            Don't raise an error, but return None if no step found

        Returns
        -------
        seamm.Node
            The node if found, None if not.
        """
        result = None
        for step in self.parent._steps[::-1]:
            if isinstance(step, cls):
                result = step
                break
        return result

    def get_previous_charges(self, missing_ok=False):
        """Copy charges from the previous energy step."""
        directory = Path(self.directory)
        step = self.find_previous_step(dftbplus_step.Energy, missing_ok=missing_ok)
        if step is None:
            if missing_ok:
                return None
            raise RuntimeError("Previous energy/optimization step not found.")
        from_path = Path(step.directory) / "charges.dat"
        if from_path.exists():
            to_path = directory / "charges.dat"
            if not to_path.exists() or not to_path.samefile(from_path):
                shutil.copy2(from_path, to_path)
        else:
            if missing_ok:
                return None
            raise FileNotFoundError("No 'charges.dat' in previous energy step.")
        return step

    def parse_results(self, lines):
        """Digest the data in the results.tag file."""

        properties = dftbplus_step.metadata["results"]

        property_data = {}
        line_iter = enumerate(lines.splitlines(), start=1)

        try:
            while True:
                lineno, line = next(line_iter)
                if line[0] == "#":
                    continue
                if ":" not in line:
                    raise RuntimeError(
                        f"Problem parsing the results.tag file: {lineno}: " f"{line}"
                    )
                key, _type, ndims, rest = line.split(":", maxsplit=3)
                ndims = int(ndims)
                key = key.strip()
                if ndims == 0:
                    # scalar
                    lineno, line = next(line_iter)
                    if _type == "real":
                        property_data[key] = float(line)
                    else:
                        property_data[key] = line
                else:
                    dims = [int(x) for x in rest.split(",")]
                    n_to_read = 1
                    for dim in dims:
                        n_to_read *= dim
                    values = []
                    while len(values) < n_to_read:
                        lineno, line = next(line_iter)
                        values.extend(line.strip().split())

                    if _type == "real":
                        values = [float(x) for x in values]

                    property_data[key] = redimension(values, dims)
                if key not in properties:
                    self.logger.warning("Property '{}' not recognized.".format(key))
                if key in properties and "units" in properties[key]:
                    property_data[key + ",units"] = properties[key]["units"]
        except StopIteration:
            pass

        return property_data

    def run(self, current_input):
        """Run a DFTB+ step.

        Parameters
        ----------
        None

        Returns
        -------
        seamm.Node
            The next node object in the flowchart.
        """
        system, configuration = self.get_system_configuration(None)

        directory = Path(self.directory)
        directory.mkdir(parents=True, exist_ok=True)

        # Access the options
        options = self.parent.options
        seamm_options = self.parent.global_options

        # Get the geometry first, because this sets up the primitive cell if needed
        geom = self.geometry()

        input_data = copy.deepcopy(current_input)
        result = self.get_input()
        deep_merge(input_data, result)

        hsd = dict_to_hsd(input_data)
        hsd += geom

        # The header part of the output
        for value in self.description:
            printer.important(value)

        files = {"dftb_in.hsd": hsd}
        logger.info("dftb_in.hsd:\n" + files["dftb_in.hsd"])

        # If the charge file exists, use it!
        path = directory / "charges.dat"
        if path.exists():
            files["charges.dat"] = path.read_text()

        # Write the input files to the current directory
        for filename in files:
            path = directory / filename
            with path.open(mode="w") as fd:
                fd.write(files[filename])

        # How to run: how many processors does this node have?
        n_cores = psutil.cpu_count(logical=False)
        self.logger.info("The number of cores is {}".format(n_cores))

        if seamm_options["ncores"] != "available":
            n_cores = min(n_cores, int(seamm_options["ncores"]))

        if options["use_openmp"]:
            n_atoms = configuration.n_atoms
            n_atoms_per_core = int(options["natoms_per_core"])
            n_threads = int(round(n_atoms / n_atoms_per_core))
            if n_threads > n_cores:
                n_threads = n_cores
            elif n_threads < 1:
                n_threads = 1
        else:
            n_threads = 1
        self.logger.info(
            f"DFTB+ will use {n_threads} OpenMP threads for {n_atoms} atoms."
        )
        printer.important(
            f"        DFTB+ using {n_threads} OpenMP threads for {n_atoms} atoms.\n"
        )

        env = {
            "OMP_NUM_THREADS": str(n_threads),
        }

        return_files = [
            "*.out",
            "charges.*",
            "dftb_pin.hsd",
            "geom.out.*",
            "output",
            "pdos*",
            "results.tag",
            "*.xml",
            "eigenvec.bin",
        ]  # yapf: disable

        # Run the calculation
        local = seamm.ExecLocal()
        exe = Path(options["dftbplus_path"]) / "dftb+"
        result = local.run(
            cmd=[str(exe)],
            files=files,
            return_files=return_files,
            env=env,
            in_situ=True,
            directory=str(directory),
        )

        if result is None:
            logger.error("There was an error running DFTB+")
            return None

        logger.debug("\n" + pprint.pformat(result))

        logger.info("stdout:\n" + result["stdout"])
        if result["stderr"] != "":
            logger.warning("stderr:\n" + result["stderr"])

        # Write the output files to the current directory
        if "stdout" in result and result["stdout"] != "":
            path = directory / "stdout.txt"
            with path.open(mode="w") as fd:
                fd.write(result["stdout"])

        if result["stderr"] != "":
            self.logger.warning("stderr:\n" + result["stderr"])
            path = directory / "stderr.txt"
            with path.open(mode="w") as fd:
                fd.write(result["stderr"])

        for filename in result["files"]:
            if filename[0] == "@":
                subdir, fname = filename[1:].split("+")
                path = directory / subdir / fname
            else:
                path = directory / filename
                if result[filename]["data"] is not None:
                    if isinstance(result[filename]["data"], bytes):
                        with path.open(mode="wb") as fd:
                            fd.write(result[filename]["data"])
                    else:
                        with path.open(mode="w") as fd:
                            fd.write(result[filename]["data"])
                else:
                    with path.open(mode="w") as fd:
                        fd.write(result[filename]["exception"])

        # Parse the results.tag file
        if "results.tag" in result["files"]:
            self.results = self.parse_results(result["results.tag"]["data"])
        else:
            self.results = {}

        # And a final structure
        if "geom.out.gen" in result["files"]:
            self.results["final structure"] = parse_gen_file(
                result["geom.out.gen"]["data"]
            )

        # Analyze the results
        self.analyze(data=self.results)
        printer.important(" ")

        # Add other citations here or in the appropriate place in the code.
        # Add the bibtex to data/references.bib, and add a self.reference.cite
        # similar to the above to actually add the citation to the references.
