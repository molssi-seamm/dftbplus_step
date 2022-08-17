# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import logging
from pathlib import Path
import textwrap

import numpy as np
import pandas
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


def fix_label(label):
    "Convert a label such as GAMMA to the greek letter."
    if label == "GAMMA":
        return "\N{GREEK CAPITAL LETTER GAMMA}"
    else:
        return label


class BandStructure(DftbBase):
    def __init__(
        self, flowchart=None, title="Band Structure", extension=None, logger=logger
    ):
        """Initialize the node"""

        logger.debug("Creating BandStructure {}".format(self))

        super().__init__(flowchart=flowchart, title=title, extension=extension)

        self.parameters = dftbplus_step.BandStructureParameters()

        self.description = ["Band Structure for DFTB+"]
        self.sym_points = None  # Points along graphs of symmetry lines
        self.sym_labels = None  # Labels of the symmetry lines
        self.path = None  # Coordinates along the path
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

        text = "Calculate the band structure with {nPoints} points."

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

        # Set up the description.
        self.description = []
        self.description.append(__(self.description_text(PP), **PP, indent=self.indent))

        # Currently use the previous energy step as source of the density
        try:
            self.energy_step = self.get_previous_charges()
        except Exception:
            raise RuntimeError("Could not find charges from previous step!")
        energy_in = self.energy_step.get_input()

        H = energy_in["Hamiltonian"]
        if "DFTB" in H:
            dftb = H["DFTB"]
            dftb["MaxSCCIterations"] = 1
            dftb["ReadInitialCharges"] = "Yes"

            dftb["KPointsAndWeights"] = self.kpoints(P["nPoints"])

            # Cannot use initial charges when reading charges from file.
            if "InitialCharges" in dftb:
                del dftb["InitialCharges"]

        result = {
            "Options": {
                "ReadChargesAsText": "Yes",
                "SkipChargeTest": "Yes",
            },
            "Hamiltonian": H,
        }
        return result

    def analyze(self, indent="", data={}, out=[]):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        # Print the key results
        text = "Prepared the band structure graph."

        # Prepare the band structure graph(s)
        if "fermi_level" in self.energy_step.results:
            Efermi = list(
                Q_(self.energy_step.results["fermi_level"], "hartree")
                .to("eV")
                .magnitude
            )
        else:
            raise RuntimeError("Serious problem in the Band Structure: no Fermi level!")

        # Need the DOS information either from a preceding DOS step or the energy step
        step = self.find_previous_step(dftbplus_step.DOS)
        if step is None:
            step = self.energy_step
        else:
            # Is it after the energy step?
            dos_id = int(step._id[-1])
            energy_id = int(self.energy_step._id[-1])
            if dos_id < energy_id:
                step = self.energy_step
        dos_path = Path(step.directory) / "DOS.csv"
        if dos_path.exists():
            DOS = pandas.read_csv(dos_path, index_col=0)
        else:
            DOS = None

        wd = Path(self.directory)
        self.band_structure(
            wd / "band.out",
            self.sym_points,
            self.sym_labels,
            Efermi=Efermi,
            DOS=DOS,
        )

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
        self.sym_points = points = []
        self.sym_labels = labels = []
        self.path = path = []
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
                result.append(f"   1 {x:7.4f} {y:7.4f} {z:7.4f}   # {start_label}")
                total += 1
                points.append(total)
                labels.append(fix_label(start_label))
                path.append(f"{x:6.3f} {y:6.3f} {z:6.3f}")
            last_label = stop_label

            num_points = max(2, int(round(n * segment_length / total_length)))
            x, y, z = stop_coord.tolist()
            result.append(f"{num_points:4} {x:7.4f} {y:7.4f} {z:7.4f}   # {stop_label}")
            delta = (stop_coord - start_coord) / num_points
            for i in range(num_points):
                start_coord += delta
                x, y, z = start_coord.tolist()
                path.append(f"{x:6.3f} {y:6.3f} {z:6.3f}")

            total += num_points
            points.append(total)
            labels.append(fix_label(stop_label))

        result.append("}")
        result = textwrap.indent("\n".join(result), 8 * " ")
        return "Klines {\n" + result
