# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import logging
from pathlib import Path

import dftbplus_step
import seamm
import seamm.data
from seamm_util import Q_, units_class
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
        if not P:
            P = self.parameters.values_to_dict()

        text = (
            f"Structural optimization using the {P['optimization method']} "
            f"method with a convergence criterion of {P['MaxForceComponent']}."
            f" A maximum of {P['MaxSteps']} will be used."
        )

        return self.header + "\n" + __(text, indent=4 * " ").__str__()

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
        self.description.append(__(self.description_text(PP), **PP, indent=self.indent))

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

    def analyze(self, indent="", data={}, out=[]):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        # Get the parameters used
        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Update the structure
        if "final structure" in data:
            sdata = data["final structure"]

            system, starting_configuration = self.get_system_configuration(None)
            periodicity = starting_configuration.periodicity
            if (
                "structure handling" in P
                and P["structure handling"] == "Create a new configuration"
            ):
                configuration = system.create_configuration(
                    periodicity=periodicity,
                    atomset=starting_configuration.atomset,
                    bondset=starting_configuration.bondset,
                    cell_id=starting_configuration.cell_id,
                )
            else:
                configuration = starting_configuration

            configuration.atoms.set_coordinates(
                sdata["coordinates"],
                fractionals=sdata["coordinate system"] == "fractional",
            )

            if "lattice vectors" in sdata:
                configuration.cell.from_vectors(sdata["lattice vectors"])

            # And the name of the configuration.
            if "configuration name" in P:
                if P["configuration name"] == "optimized with <Hamiltonian>":
                    hamiltonian = self.parent._dataset
                    if self.parent._subset is not None:
                        hamiltonian += " + " + self.parent._subset

                    configuration.name = f"optimized with {hamiltonian}"
                elif P["configuration name"] == "keep current name":
                    pass
                elif P["configuration name"] == "use SMILES string":
                    configuration.name = configuration.smiles
                elif P["configuration name"] == "use Canonical SMILES string":
                    configuration.name = configuration.canonical_smiles
                elif P["configuration name"] == "use configuration number":
                    configuration.name = str(configuration.n_configurations)

        # Print the key results
        data["nsteps"] = 25
        text = (
            "The geometry optimization converged in {nsteps} steps to a total "
            "energy of {total_energy:.6f} Ha."
        )
        # Calculate the energy of formation
        if self.parent._reference_energy is not None:
            dE = data["total_energy"] - self.parent._reference_energy
            dE = Q_(dE, "hartree").to("kJ/mol").magnitude
            text += f" The calculated formation energy is {dE:.2f} kJ/mol."
            data["energy of formation"] = dE
        else:
            text += " Could not calculate the formation energy because some reference "
            text += "energies are missing."
            data["energy of formation"] = None

        printer.normal(__(text, **data, indent=self.indent + 4 * " "))

        # Put any requested results into variables or tables
        self.store_results(
            data=data,
            properties=dftbplus_step.properties,
            results=self.parameters["results"].value,
            create_tables=self.parameters["create tables"].get(),
        )
