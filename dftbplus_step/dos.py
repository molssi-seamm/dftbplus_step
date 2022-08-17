# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import logging
from pathlib import Path
import textwrap

import numpy as np
import seekpath

import dftbplus_step
import seamm
import seamm.data
from seamm_util import Q_, units_class
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

from .base import DftbBase


logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("DFTB+")


class DOS(DftbBase):
    def __init__(self, flowchart=None, title="DOS", extension=None, logger=logger):
        """Initialize the node"""

        logger.debug("Creating DOS {}".format(self))

        super().__init__(flowchart=flowchart, title=title, extension=extension)

        self.parameters = dftbplus_step.DOSParameters()

        self.description = ["DOS for DFTB+"]
        self.points = None  # Points along graphs of symmetry lines
        self.labels = None  # Labels of the symmetry lines
        self.energy_step = None  # The step that got the energy and density

    @property
    def header(self):
        """A printable header for this section of output"""
        return "Step {}: {}".format(".".join(str(e) for e in self._id), self.title)

    @property
    def version(self):
        """The semantic version of this module."""
        return dftbplus_step.__version__

    @property
    def git_revision(self):
        """The git version of this module."""
        return dftbplus_step.__git_revision__

    def description_text(self, P=None):
        """Prepare information about what this node will do"""
        if not P:
            P = self.parameters.values_to_dict()

        text = "Calculate the DOS using a "
        kmethod = P["k-grid method"]
        if kmethod == "grid spacing":
            text += (
                f" Monkhorst-Pack grid with a spacing of {P['k-spacing']} will be used."
            )
        elif kmethod == "supercell folding":
            text += (
                f" {P['na']} x{P['nb']} x{P['nc']} Monkhorst-Pack grid will be used."
            )

        return self.header + "\n" + __(text, indent=4 * " ").__str__()

    def get_input(self):
        """Get the input for an initialization calculation for DFTB+"""

        # Create the directory
        directory = Path(self.directory)
        directory.mkdir(parents=True, exist_ok=True)

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Have to fix formatting for printing...
        PP = dict(P)
        for key in PP:
            if isinstance(PP[key], units_class):
                PP[key] = "{:~P}".format(PP[key])

        # Need the configuration for charges, spins, etc.
        system, configuration = self.get_system_configuration(None)
        periodicity = configuration.periodicity

        # Set up the description.
        self.description = []

        # If not periodic, skip!
        if periodicity != 3:
            self.description.append(
                __(
                    "The system is not periodic, so the DOS will not be calculated.",
                    indent=self.indent,
                )
            )
            return None

        self.description.append(__(self.description_text(PP), **PP, indent=self.indent))

        # Currently use the previous energy step as source of the density
        self.energy_step = self.get_previous_charges()
        if self.energy_step is None:
            raise RuntimeError("Could not find charges from previous step!")
        energy_in = self.energy_step.get_input()

        H = energy_in["Hamiltonian"]
        if "DFTB" in H:
            dftb = H["DFTB"]
            # Run one iteration, but need to converge to get projected DOS.
            dftb["MaxSCCIterations"] = 1
            dftb["SCCTolerance"] = 10.0
            dftb["ReadInitialCharges"] = "Yes"

        # Integration grid in reciprocal space
        kmethod = P["k-grid method"]
        if kmethod == "grid spacing":
            lengths = configuration.cell.reciprocal_lengths()
            spacing = P["k-spacing"].to("1/Å").magnitude
            na = round(lengths[0] / spacing)
            nb = round(lengths[0] / spacing)
            nc = round(lengths[0] / spacing)
            na = na if na > 0 else 1
            nb = nb if nb > 0 else 1
            nc = nc if nc > 0 else 1
        elif kmethod == "supercell folding":
            na = P["na"]
            nb = P["nb"]
            nc = P["nc"]
        oa = 0.0 if na % 2 == 1 else 0.5
        ob = 0.0 if nb % 2 == 1 else 0.5
        oc = 0.0 if nc % 2 == 1 else 0.5
        kmesh = (
            "SupercellFolding {\n"
            f"            {na} 0 0\n"
            f"            0 {nb} 0\n"
            f"            0 0 {nc}\n"
            f"            {oa} {ob} {oc}\n"
            "        }"
        )
        dftb["KPointsAndWeights"] = kmesh
        self.description.append(
            __(
                f"The mesh for the Brillouin zone integration is {na} x {nb} x {nc}"
                f" with offsets of {oa}, {ob}, and {oc}",
                indent=self.indent + 4 * " ",
            )
        )
        # Cannot use initial charges when reading charges from file.
        if "InitialCharges" in dftb:
            del dftb["InitialCharges"]

        # Set up for atom based DOS
        if "Analysis" not in energy_in:
            energy_in["Analysis"] = {}
        analysis = energy_in["Analysis"]
        analysis["CalculateForces"] = "No"

        elements = set(configuration.atoms.symbols)
        elements = sorted([*elements])
        dos = {}
        n = 0
        for element in elements:
            n += 1
            dos[f"Region<{n}>"] = {
                "Atoms": element,
                "ShellResolved": "Yes",
                "Label": f'"pdos_{element}"',
            }
        analysis["ProjectStates"] = dos
        result = {
            "Options": {
                "ReadChargesAsText": "Yes",
                "SkipChargeTest": "Yes",
            },
            "Hamiltonian": H,
            "Analysis": analysis,
        }
        return result

    def analyze(self, indent="", data={}, out=[]):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        # Print the key results
        text = "Prepared the DOS graph."

        # Prepare the DOS graph(s)
        if "fermi_level" in self.energy_step.results:
            Efermi = list(
                Q_(self.energy_step.results["fermi_level"], "hartree")
                .to("eV")
                .magnitude
            )
        else:
            raise RuntimeError("Serious problem in the DOS: no Fermi level!")

        wd = Path(self.directory)
        self.dos(wd / "band.out", Efermi=Efermi)

        printer.normal(__(text, **data, indent=self.indent + 4 * " "))

        # Put any requested results into variables or tables
        self.store_results(
            data=data,
            properties=dftbplus_step.properties,
            results=self.parameters["results"].value,
            create_tables=self.parameters["create tables"].get(),
        )

    def kpoints(self, nPoints):
        """Create the lines of kpoints for DFTB+."""
        system, configuration = self.get_system_configuration(None)
        cell_data = configuration.primitive_cell()

        # Get the lines
        seekpath_output = seekpath.get_path(cell_data[0:3], with_time_reversal=True)

        # Get the total length of the path.
        total_length = 0.0
        for start_label, stop_label in seekpath_output["path"]:
            start_coord = np.array(seekpath_output["point_coords"][start_label])
            stop_coord = np.array(seekpath_output["point_coords"][stop_label])
            start_coord_abs = np.dot(
                start_coord, seekpath_output["reciprocal_primitive_lattice"]
            )
            stop_coord_abs = np.dot(
                stop_coord, seekpath_output["reciprocal_primitive_lattice"]
            )
            segment_length = np.linalg.norm(stop_coord_abs - start_coord_abs)
            total_length += segment_length

        # And extra points needed -- 1 at start, and one at each break
        last_label = ""
        extra_points = 0
        for start_label, stop_label in seekpath_output["path"]:
            if start_label != last_label:
                extra_points += 1
            last_label = stop_label

        n = nPoints - extra_points
        result = []
        last_label = ""
        total = 0
        self.points = points = []
        self.labels = labels = []
        for start_label, stop_label in seekpath_output["path"]:
            start_coord = np.array(seekpath_output["point_coords"][start_label])
            stop_coord = np.array(seekpath_output["point_coords"][stop_label])

            start_coord_abs = np.dot(
                start_coord, seekpath_output["reciprocal_primitive_lattice"]
            )
            stop_coord_abs = np.dot(
                stop_coord, seekpath_output["reciprocal_primitive_lattice"]
            )
            segment_length = np.linalg.norm(stop_coord_abs - start_coord_abs)

            # See if we needed an added point at the start
            if start_label != last_label:
                x, y, z = start_coord.tolist()
                result.append(f"   1 {x:.4f} {y:.4f} {z:.4f}   # {start_label}")
                total += 1
                points.append(total)
                labels.append(start_label)
            last_label = stop_label

            num_points = max(2, int(round(n * segment_length / total_length)))
            x, y, z = stop_coord.tolist()
            result.append(f"{num_points:4} {x:.4f} {y:.4f} {z:.4f}   # {stop_label}")
            total += num_points
            points.append(total)
            labels.append(stop_label)

        result.append("}")
        result = textwrap.indent("\n".join(result), 8 * " ")
        return "Klines {\n" + result
