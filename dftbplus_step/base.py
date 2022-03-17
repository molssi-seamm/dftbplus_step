# -*- coding: utf-8 -*-

"""Non-graphical part of the DFTB+ step in a SEAMM flowchart
"""

import copy

import logging
from pathlib import Path
import pprint
import subprocess
import traceback

import pandas

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
        super().__init__(flowchart=flowchart, title=title, extension=extension)

    @property
    def is_runable(self):
        """Indicate whether this not runs or just adds input."""
        return True

    def band_structure(self, input_path, sym_points, sym_names):
        """Prepare the graph for the band structure.

        Parameters
        ----------
        path : filename or pathlib.Path
            The path to the band output from DFTB+.
        """
        wd = Path(self.directory)
        logger.info(f"Preparing the band structure, {wd}")

        options = self.parent.options
        exe = Path(options["dftbplus_path"]) / "dp_bands"

        command = f"{exe} {input_path} {wd / 'band'}"
        try:
            subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Calling dp_band, returncode = {e.returncode}")
            logger.warning(f"Output: {e.output}")
            return None

        # Read the plot data
        with open(wd / "band_tot.dat", "r") as fd:
            data = pandas.read_csv(
                fd,
                sep=r"\s+",
                header=None,
                index_col=0,
                comment="!",
            )
        # Create a graph of the DOS
        figure = self.create_figure(
            module_path=("seamm",),
            template="band_structure.graph_template",
            title="Band Structure",
        )

        plot = figure.add_plot("BandStructure")

        x_axis = plot.add_axis(
            "x",
            label="",
            tickmode="array",
            tickvals=sym_points,
            ticktext=sym_names,
        )
        y_axis = plot.add_axis("y", label="Energy (eV)", anchor=x_axis)
        x_axis.anchor = y_axis

        i = 0
        for label, column in data.items():
            if i > 0:
                plot.add_trace(
                    x_axis=x_axis,
                    y_axis=y_axis,
                    name=f"band {i}",
                    x=list(data.index),
                    xlabel="",
                    xunits="",
                    y=list(column),
                    ylabel="Energy",
                    yunits="eV",
                    color="black",
                )
            i = i + 1
        figure.grid_plots("BandStructure")

        # Write it out.
        figure.dump(wd / "band_structure.graph")

        write_html = "html" in options and options["html"]
        if write_html:
            figure.template = "band_structure.html_template"
            figure.dump(wd / "band_structure.html")

    def dos(self, input_path):
        """Prepare the graph for the density of states.

        Parameters
        ----------
        path : filename or pathlib.Path
            The path to the band output from DFTB+.
        """
        wd = Path(self.directory)
        logger.info(f"Preparing DOS, {wd}")

        options = self.parent.options
        exe = Path(options["dftbplus_path"]) / "dp_dos"

        command = f"{exe} {input_path} {wd / 'dos_total.dat'}"
        try:
            subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Calling dp_dos, returncode = {e.returncode}")
            logger.warning(f"Output: {e.output}")
            return None

        # Read the plot data
        with open(wd / "dos_total.dat", "r") as fd:
            data = pandas.read_csv(
                fd,
                sep=r"\s+",
                header=None,
                comment="!",
                index_col=0,
            )

        n_columns = data.shape[1]
        if n_columns == 1:
            spin_polarized = False
            data.rename(columns={0: "E", 1: "DOS"}, inplace=True)
        elif n_columns == 3:
            spin_polarized = True
            data.rename(columns={0: "E", 1: "DOS", 2: "Up", 3: "Down"}, inplace=True)
        else:
            raise RuntimeError(f"DOS has {n_columns} columns of data.")

        dE = data.index[1] - data.index[0]
        x0 = data.index[0]

        # Create a graph of the DOS
        figure = self.create_figure(
            module_path=("seamm",),
            template="line.graph_template",
            title="Total DOS",
        )

        plot = figure.add_plot("DOS")

        x_axis = plot.add_axis("x", label="Energy (eV)")
        y_axis = plot.add_axis("y", label="DOS", anchor=x_axis)
        x_axis.anchor = y_axis

        if spin_polarized:
            plot.add_trace(
                x_axis=x_axis,
                y_axis=y_axis,
                name="SpinUp",
                x0=x0,
                dx=dE,
                xlabel="t",
                xunits="eV",
                y=list(data["Up"]),
                ylabel="Spin up",
                yunits="",
                color="red",
            )
            plot.add_trace(
                x_axis=x_axis,
                y_axis=y_axis,
                name="SpinDown",
                x0=x0,
                dx=dE,
                xlabel="t",
                xunits="eV",
                y=list(data["Down"]),
                ylabel="Spin down",
                yunits="",
                color="blue",
            )
        else:
            plot.add_trace(
                x_axis=x_axis,
                y_axis=y_axis,
                name="DOS",
                x0=x0,
                dx=dE,
                xlabel="t",
                xunits="eV",
                y=list(data["DOS"]),
                ylabel="DOS",
                yunits="",
                color="black",
            )
        figure.grid_plots("DOS")

        # Write it out.
        figure.dump(wd / "DOS.graph")

        write_html = "html" in options and options["html"]
        if write_html:
            figure.template = "line.html_template"
            figure.dump(wd / "DOS.html")

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
        result += f"    TypeNames = {names}\n"

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
                lattice, fractionals, atomic_numbers = configuration.primitive_cell()
            else:
                # Use the full cell
                lattice = configuration.cell.vectors()
                fractionals = configuration.atoms.get_coordinates(fractionals=True)
                atomic_numbers = configuration.atoms.atomic_numbers

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

    def parse_results(self, lines):
        """Digest the data in the results.tag file."""

        properties = dftbplus_step.properties

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

        input_data = copy.deepcopy(current_input)
        result = self.get_input()
        deep_merge(input_data, result)

        hsd = dict_to_hsd(input_data)
        hsd += self.geometry()

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

        return_files = [
            "*.out",
            "charges.*",
            "dftb_pin.hsd",
            "geom.out.*",
            "output",
            "results.tag",
        ]  # yapf: disable

        # Run the calculation
        local = seamm.ExecLocal()
        exe = Path(options["dftbplus_path"]) / "dftb+"
        result = local.run(
            cmd=[str(exe)], files=files, return_files=return_files
        )  # yapf: disable

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
                    if filename in ("charges.bin",):
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
            results = self.parse_results(result["results.tag"]["data"])
        else:
            results = {}

        # And a final structure
        if "geom.out.gen" in result["files"]:
            results["final structure"] = parse_gen_file(result["geom.out.gen"]["data"])

        # Analyze the results
        self.analyze(data=results)
        printer.important(" ")

        # Add other citations here or in the appropriate place in the code.
        # Add the bibtex to data/references.bib, and add a self.reference.cite
        # similar to the above to actually add the citation to the references.
