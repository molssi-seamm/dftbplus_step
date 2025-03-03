# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import logging
from pathlib import Path

import numpy as np

import dftbplus_step
from molsystem import RMSD
import seamm
import seamm.data
from seamm_util import units_class
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("DFTB+")


class Optimization(dftbplus_step.Energy):
    def __init__(self, flowchart=None, title="Optimization", extension=None):
        """Initialize the node"""

        logger.debug("Creating Optimization {}".format(self))

        super().__init__(flowchart=flowchart, title=title, extension=extension)

        self._calculation = "optimization"
        self._model = None
        self._metadata = dftbplus_step.metadata
        self.parameters = dftbplus_step.OptimizationParameters()

        self.description = ["Optimization of DFTB+"]

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
        if P is None:
            P = self.parameters.values_to_dict()

        tmp = super().description_text(P)
        energy_description = "\n".join(tmp.splitlines()[1:])

        text = (
            f"Structural optimization using the {P['optimization method']} "
            f"method with a convergence criterion of {P['MaxForceComponent']} "
            f"and no more than {P['MaxSteps']} steps. "
        )

        if self.model is None:
            kwargs = {}
        else:
            kwargs = {"Hamiltonian": self.model}
        text += seamm.standard_parameters.structure_handling_description(P, **kwargs)

        return (
            self.header
            + "\n"
            + __(text, indent=4 * " ").__str__()
            + "\n\n"
            + energy_description
        )

    def get_input(self):
        """Get the input for an optimization calculation for DFTB+"""
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

        self.description = []
        self.description.append(__(self.description_text(PP), **PP, indent=4 * " "))

        _, configuration = self.get_system_configuration(None)

        # Template
        result = super().get_input()

        method = P["optimization method"]
        block = result["Driver = GeometryOptimization"] = {}

        if "Rational" in method:
            subblock = block["Optimizer = Rational"] = {}
            subblock["DiagLimit"] = P["DiagLimit"]
        elif "LBFGS" in method:
            subblock = block["Optimizer = LBFGS"] = {}
            subblock["Memory"] = P["Memory"]
        elif "FIRE" in method:
            subblock = block["Optimizer = FIRE"] = {}
            subblock["FIRE"] = {}
            for key in (
                "StepSize",
                "nMin",
                "aPar",
                "fInc",
                "fDec",
                "fAlpha",
            ):
                subblock[key] = P[key]
        else:
            raise RuntimeError(f"Don't recognize optimization method '{method}'")

        max_force = P["MaxForceComponent"].to("hartree/bohr")
        block["Convergence"] = {"GradAMax": max_force.magnitude}
        block["MaxSteps"] = P["MaxSteps"]
        if configuration.periodicity == 3:
            block["LatticeOpt"] = P["LatticeOpt"]
        block["OutputPrefix"] = "geom.out"

        return result

    def analyze(self, indent="", data={}, out=[], table=None):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        if table is None:
            table = {
                "Property": [],
                "Value": [],
                "Units": [],
            }

        text = ""

        # Get the parameters used
        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Read the detailed output file to get the number of iterations
        directory = Path(self.directory)
        path = directory / "detailed.out"
        lines = iter(path.read_text().splitlines())
        data["nsteps"] = "unknown number of"
        data["ediff"] = "unknown"
        data["scc error"] = None
        for line in lines:
            if "Geometry optimization step:" in line:
                data["nsteps"] = line.split()[3]
            if "Diff electronic" in line:
                tmp = next(lines).split()
                data["ediff"] = float(tmp[2])

        # Print the key results

        table["Property"].append("Total energy")
        table["Value"].append(f"{data['total_energy']:.6f}")
        table["Units"].append("E_h")

        table["Property"].append("Optimization steps")
        table["Value"].append(f"{data['nsteps']}")
        table["Units"].append("")

        table["Property"].append("Last energy change")
        table["Value"].append(f"{data['ediff']:.6f}")
        table["Units"].append("E_h")

        if P["SCC"] == "Yes" and data["scc error"] is not None:
            table["Property"].append("SCC error")
            table["Value"].append(f"{data['scc error']:.6f}")
            table["Units"].append("")

        # Update the structure
        if "final structure" in data:
            sdata = data["final structure"]

            _, starting_configuration = self.get_system_configuration()
            if starting_configuration.periodicity != 3:
                initial = starting_configuration.to_RDKMol()

            update_structure = P["structure handling"] != "Discard the structure"
            system, configuration = self.get_system_configuration(P)

            if starting_configuration.periodicity == 3:
                if update_structure:
                    (
                        lattice_in,
                        fractionals_in,
                        atomic_numbers,
                        self._mapping_from_primitive,
                        self._mapping_to_primitive,
                    ) = starting_configuration.primitive_cell()

                    tmp = configuration.update(
                        sdata["coordinates"],
                        fractionals=sdata["coordinate system"] == "fractional",
                        atomic_numbers=atomic_numbers,
                        lattice=sdata["lattice vectors"],
                        space_group=starting_configuration.symmetry.group,
                        symprec=0.01,
                    )

                    # Symmetry may have changed
                    if tmp != "":
                        text += f"\n\nWarning: {tmp}\n\n"
                        (
                            lattice,
                            fractionals,
                            atomic_numbers,
                            self._mapping_from_primitive,
                            self._mapping_to_primitive,
                        ) = configuration.primitive_cell()
            else:
                if update_structure:
                    configuration.atoms.set_coordinates(
                        sdata["coordinates"],
                        fractionals=sdata["coordinate system"] == "fractional",
                    )
                    final = configuration.to_RDKMol()
                else:
                    final = starting_configuration.to_RDKMol()
                    final.GetConformer(0).SetPositions(np.array(sdata["coordinates"]))

                result = RMSD(final, initial, symmetry=True, include_h=True)
                data["RMSD with H"] = result["RMSD"]
                data["displaced atom with H"] = result["displaced atom"]
                data["maximum displacement with H"] = result["maximum displacement"]

                # Align the structure
                if update_structure:
                    configuration.from_RDKMol(final)

                result = RMSD(final, initial, symmetry=True)
                data["RMSD"] = result["RMSD"]
                data["displaced atom"] = result["displaced atom"]
                data["maximum displacement"] = result["maximum displacement"]

            # And the name of the configuration.
            text += seamm.standard_parameters.set_names(
                system,
                configuration,
                P,
                _first=True,
                Hamiltonian=self.model,
            )

        if "RMSD" in data:
            tmp = data["RMSD"]
            table["Property"].append("RMSD in Geometry")
            table["Value"].append(f"{tmp:.2f}")
            table["Units"].append("Å")

        if "maximum displacement" in data:
            tmp = data["maximum displacement"]
            table["Property"].append("Largest Displacement")
            table["Value"].append(f"{tmp:.2f}")
            table["Units"].append("Å")

        if "displaced atom" in data:
            tmp = data["displaced atom"]
            table["Property"].append("Displaced Atom")
            table["Value"].append(f"{tmp + 1}")
            table["Units"].append("")

        printer.normal(__(text, **data, indent=8 * " "))

        printer.normal("\n")

        super().analyze(indent=indent, data=data, out=out, table=table)
