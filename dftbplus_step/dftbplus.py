# -*- coding: utf-8 -*-

"""Non-graphical part of the DFTB+ step in a SEAMM flowchart
"""

import collections

try:
    import importlib.metadata as implib
except Exception:
    import importlib_metadata as implib
import json
import logging
from pathlib import Path
import pprint  # noqa: F401
import sys
import traceback

import dftbplus_step
import seamm
import seamm_util
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

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


def deep_merge(d, u):
    """Do a deep merge of one dict into another.

    This will update d with values in u, but will not delete keys in d
    not found in u at some arbitrary depth of d. That is, u is deeply
    merged into d.

    Args -
        d, u: dicts

    Note: this is destructive to d, but not u.

    Returns: None

    Written by djpinne @
    https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """  # noqa: E501
    stack = [(d, u)]
    while stack:
        d, u = stack.pop(0)
        for k, v in u.items():
            if not isinstance(v, collections.Mapping):
                # u[k] is not a dict, nothing to merge, so just set it,
                # regardless if d[k] *was* a dict
                d[k] = v
            else:
                # note: u[k] is a dict

                # get d[k], defaulting to a dict, if it doesn't previously
                # exist
                dv = d.setdefault(k, {})

                if not isinstance(dv, collections.Mapping):
                    # d[k] is not a dict, so just set it to u[k],
                    # overriding whatever it was
                    d[k] = v
                else:
                    # both d[k] and u[k] are dicts, push them on the stack
                    # to merge
                    stack.append((dv, v))


def dict_to_hsd(d, indent=0):
    """Convert a dictionary into human-friendly structured data (HSD).

    Parameters
    ----------
    d : dict
        The input dictionary to transform

    Return
    ------
    hsd : str
        The HSD text.
    """
    hsd = ""
    for key, value in d.items():
        if isinstance(value, collections.Mapping):
            hsd += indent * " " + key + " {\n"
            hsd += dict_to_hsd(value, indent + 4)
            hsd += indent * " " + "}\n"
        else:
            hsd += indent * " " + f"{key} = {value}\n"

    return hsd


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


class Dftbplus(seamm.Node):
    """
    The non-graphical part of a DFTB+ step in a flowchart.

    Attributes
    ----------
    parser : configargparse.ArgParser
        The parser object.

    options : tuple
        It contains a two item tuple containing the populated namespace and the
        list of remaining argument strings.

    subflowchart : seamm.Flowchart
        A SEAMM Flowchart object that represents a subflowchart, if needed.

    parameters : DftbplusParameters
        The control parameters for DFTB+.

    See Also
    --------
    TkDftbplus,
    Dftbplus, DftbplusParameters
    """

    def __init__(
        self,
        flowchart=None,
        title="DFTB+",
        namespace="org.molssi.seamm.dftbplus",
        extension=None,
        logger=logger,
    ):
        """A step for DFTB+ in a SEAMM flowchart.

        You may wish to change the title above, which is the string displayed
        in the box representing the step in the flowchart.

        Parameters
        ----------
        flowchart: seamm.Flowchart
            The non-graphical flowchart that contains this step.

        title: str
            The name displayed in the flowchart.
        namespace : str
            The namespace for the plug-ins of the subflowchart
        extension: None
            Not yet implemented
        logger : Logger = logger
            The logger to use and pass to parent classes

        Returns
        -------
        None
        """
        logger.debug("Creating DFTB+ {}".format(self))
        self.subflowchart = seamm.Flowchart(
            parent=self, name="DFTB+", namespace=namespace
        )  # yapf: disable

        super().__init__(
            flowchart=flowchart,
            title="DFTB+",
            extension=extension,
            module=__name__,
            logger=logger,
        )  # yapf: disable

        self.parameters = dftbplus_step.DftbplusParameters()

        # Get the metadata for the Slater-Koster parameters
        package = self.__module__.split(".")[0]
        files = [p for p in implib.files(package) if p.name == "metadata.json"]
        if len(files) != 1:
            raise RuntimeError("Can't find Slater-Koster metadata.json file")
        data = files[0].read_text()
        self._slako = json.loads(data)

        # Data to pass between substeps
        self._dataset = None  # SLAKO dataset used
        self._subset = None  # SLAKO modifier dataset applied to dataset
        self._reference_energy = None  # for calculating energy of formation

    @property
    def version(self):
        """The semantic version of this module."""
        return dftbplus_step.__version__

    @property
    def git_revision(self):
        """The git version of this module."""
        return dftbplus_step.__git_revision__

    def create_parser(self):
        """Setup the command-line / config file parser"""
        # parser_name = 'dftbplus-step'
        parser_name = self.step_type
        parser = seamm_util.getParser(name="SEAMM")

        # Remember if the parser exists ... this type of step may have been
        # found before
        parser_exists = parser.exists(parser_name)

        # Create the standard options, e.g. log-level
        result = super().create_parser(name=parser_name)

        if parser_exists:
            return result

        # Options for DFTB+
        parser.add_argument(
            parser_name,
            "--dftbplus-path",
            default="",
            help="the path to the DFTB+ executable",
        )

        parser.add_argument(
            parser_name,
            "--slako-dir",
            default="${SEAMM:root}/Parameters/slako",
            help="the path to the Slater-Koster parameter files",
        )

        parser.add_argument(
            parser_name,
            "--use-mpi",
            default=False,
            help="Whether to use mpi",
        )

        parser.add_argument(
            parser_name,
            "--use-openmp",
            default=True,
            help="Whether to use openmp threads",
        )

        parser.add_argument(
            parser_name,
            "--natoms-per-core",
            default=10,
            help="How many atoms to have per core or thread",
        )

        return result

    def set_id(self, node_id):
        """Set the id for node to a given tuple"""
        self._id = node_id

        # and set our subnodes
        self.subflowchart.set_ids(self._id)

        return self.next()

    def description_text(self, P=None):
        """Create the text description of what this step will do.
        The dictionary of control values is passed in as P so that
        the code can test values, etc.

        Parameters
        ----------
        P: dict
            An optional dictionary of the current values of the control
            parameters.
        Returns
        -------
        str
            A description of the current step.
        """
        self.subflowchart.root_directory = self.flowchart.root_directory

        # Get the first real node
        node = self.subflowchart.get_node("1").next()

        text = self.header + "\n\n"
        while node is not None:
            try:
                text += __(node.description_text(), indent=3 * " ").__str__()
            except Exception as e:
                print(
                    "Error describing dftbplus flowchart: {} in {}".format(
                        str(e), str(node)
                    )
                )
                logger.critical(
                    "Error describing dftbplus flowchart: {} in {}".format(
                        str(e), str(node)
                    )
                )
                raise
            except:  # noqa: E722
                print(
                    "Unexpected error describing dftbplus flowchart: {} in {}".format(
                        sys.exc_info()[0], str(node)
                    )
                )
                logger.critical(
                    "Unexpected error describing dftbplus flowchart: {} in {}".format(
                        sys.exc_info()[0], str(node)
                    )
                )
                raise
            text += "\n"
            node = node.next()

        return text

    def run(self):
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
        n_atoms = configuration.n_atoms
        if n_atoms == 0:
            self.logger.error("DFTB+ run(): there is no structure!")
            raise RuntimeError("DFTB+ run(): there is no structure!")

        # Print our header to the main output
        printer.important(self.header)
        printer.important("")

        # Access the options
        options = self.options

        # Add the main citation for DFTB+
        self.references.cite(
            raw=self._bibliography["dftbplus"],
            alias="dftb+",
            module="dftb+ step",
            level=1,
            note="The principle DFTB+ citation.",
        )

        next_node = super().run(printer)
        # Get the first real node
        node = self.subflowchart.get_node("1").next()

        input_data = {
            "Options": {
                "WriteResultsTag": "Yes",
                "WriteChargesAsText": "Yes",
            }
        }  # yapf: disable
        while node is not None:
            result = node.get_input()
            deep_merge(input_data, result)
            node = node.next()

        hsd = dict_to_hsd(input_data)
        hsd += self.geometry()

        files = {"dftb_in.hsd": hsd}
        logger.info("dftb_in.hsd:\n" + files["dftb_in.hsd"])

        # Write the input files to the current directory
        directory = Path(self.directory)
        directory.mkdir(parents=True, exist_ok=True)
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
            with path.open(mode="w") as fd:
                if result[filename]["data"] is not None:
                    fd.write(result[filename]["data"])
                else:
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

        # Add other citations here or in the appropriate place in the code.
        # Add the bibtex to data/references.bib, and add a self.reference.cite
        # similar to the above to actually add the citation to the references.

        return next_node

    def analyze(self, indent="", data=None, **kwargs):
        """Do any analysis of the output from this step.

        Also print important results to the local step.out file using
        'printer'.

        Parameters
        ----------
        indent: str
            An extra indentation for the output
        """
        # Get the first real node
        node = self.subflowchart.get_node("1").next()

        # Loop over the subnodes, asking them to do their analysis
        while node is not None:
            for value in node.description:
                printer.important(value)
                printer.important(" ")

            node.analyze(data=data)

            node = node.next()

    def geometry(self):
        """Create the input for DFTB+ for the geometry.

        Example:

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
        elif configuration.periodicity == 3:
            result += "   Periodic = Yes\n"
            result += "   LatticeVectors [Angstrom] = {\n"
            uvw = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            XYZ = configuration.cell.to_cartesians(uvw)
            for xyz in XYZ:
                x, y, z = xyz
                result += f"        {x:10.6f} {y:10.6f} {z:10.6f}\n"
            result += "    }\n"
            result += "    TypesAndCoordinates [relative] = {\n"
            for element, xyz in zip(
                configuration.atoms.symbols,
                configuration.atoms.get_coordinates(fractionals=True),
            ):
                index = elements.index(element)
                x, y, z = xyz
                result += f"        {index+1:>2} {x:10.6f} {y:10.6f} {z:10.6f}\n"
            result += "    }\n"
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
                        tmp = [float(x) for x in values]
                        values = tmp

                    property_data[key] = redimension(values, dims)
                if key not in properties:
                    self.logger.warning("Property '{}' not recognized.".format(key))
                if key in properties and "units" in properties[key]:
                    property_data[key + ",units"] = properties[key]["units"]
        except StopIteration:
            pass

        return property_data


def parse_gen_file(data):
    """Parse a DFTB+ gen datafile into coordinates, etc.

    Parameters
    ----------
    data : str
        The contents of the file as a string

    Returns
    -------
    dict
       A dictionary with labeled coordinates, periodicity, etc.
    """

    result = {}
    line = iter(data.splitlines())

    try:
        n_atoms, coord_flag = next(line).split()
        n_atoms = int(n_atoms)
        if coord_flag == "C":
            result["periodicity"] = 0
            result["coordinate system"] = "Cartesian"
        elif coord_flag == "S":
            result["periodicity"] = 3
            result["coordinate system"] = "Cartesian"
        elif coord_flag == "F":
            result["periodicity"] = 3
            result["coordinate system"] = "fractional"
        else:
            raise RuntimeError(f"Don't recognize the type of geometry '{coord_flag}'")

        elements = next(line).split()

        # And now the atoms
        coordinates = result["coordinates"] = []
        result["elements"] = []
        for i in range(n_atoms):
            _, index, x, y, z = next(line).split()
            result["elements"].append(elements[int(index) - 1])
            coordinates.append([float(x), float(y), float(z)])

        # Cell information if periodic
        if result["periodicity"] == 3:
            data = next(line).split()
            result["origin"] = [float(x) for x in data]
            lattice = result["lattice vectors"] = []
            for i in range(3):
                data = next(line).split()
                lattice.append([float(x) for x in data])
    except StopIteration:
        raise EOFError("The gen file ended prematurely.")

    return result
