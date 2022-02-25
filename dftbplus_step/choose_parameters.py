# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import logging
from pathlib import Path

import dftbplus_step
import seamm
import seamm.data
from seamm_util import units_class
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("DFTB+")


class ChooseParameters(seamm.Node):
    def __init__(
        self, flowchart=None, title="Choose Parameters", extension=None, logger=logger
    ):
        """Initialize the node"""

        logger.debug("Creating ChooseParameters {}".format(self))

        super().__init__(flowchart=flowchart, title=title, extension=extension)

        self.parameters = dftbplus_step.ChooseParametersParameters()

        self.description = ["Choose Slater-Koster parameters for DFTB+"]

    @property
    def is_runable(self):
        """Indicate whether this not runs or just adds input."""
        return False

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

        dataset = P["dataset"]
        subset = P["subset"]

        text = f"Using the '{dataset}' set of Slater-Koster parameters"
        if subset != "none":
            text += f" with the specialized set '{subset}' added."
        else:
            text += "."

        return self.header + "\n" + __(text, indent=4 * " ").__str__()

    def get_input(self):
        """Get the input for the Slater-Koster parameters for DFTB+"""

        # Get the metadata for the Slater-Koster parameters
        metadata = self.parent._metadata
        slako_dir = Path(self.parent.options["slako_dir"]).expanduser()

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

        # The parameter data
        parameter_set = P["dataset"]
        model, parameter_set_name = parameter_set.split(" - ", 1)
        datasets = metadata[model]["datasets"]
        dataset = datasets[parameter_set]

        system_db = self.get_variable("_system_db")
        configuration = system_db.system.configuration
        parameters = {}
        elements = set(configuration.atoms.symbols)
        elements = sorted([*elements])

        if model == "DFTB":
            potentials = metadata[model]["potentials"]
            pairs = dataset["potential pairs"]

            self.parent._hamiltonian = P["dataset"]

            if P["subset"] == "none":
                subset = None
            else:
                self.parent._hamiltonian += " + " + P["subset"].split(" - ")[1]
                subset = datasets[P["subset"]]
                subpairs = subset["potential pairs"]

            # Broadcast to the parent so that other substeps can use
            self.parent._dataset = dataset
            self.parent._subset = subset

            for el1 in elements:
                for el2 in elements:
                    key = f"{el1}-{el2}"
                    # Not sure if flipping the key is valid....
                    key2 = f"{el2}-{el1}"
                    if subset is not None and key in subpairs:
                        md5sum = subpairs[key]["md5sum"]
                    elif key in pairs:
                        md5sum = pairs[key]["md5sum"]
                    elif subset is not None and key2 in subpairs:
                        md5sum = subpairs[key2]["md5sum"]
                    elif key2 in pairs:
                        md5sum = pairs[key2]["md5sum"]
                    else:
                        raise RuntimeError(
                            f"Could not find the Slater-Koster file for {key} "
                            f"for dataset {P['dataset']}, subset {P['subset']}."
                        )
                    parameters[key] = str(slako_dir / potentials[md5sum]["filename"])

            # The maximum angular momentum
            data = dataset["element data"]
            if subset is not None and "element data" in subset:
                subdata = subset["element data"]
            else:
                subdata = None

            references = set()
            max_momentum = {}
            key = "maximum angular momentum"
            for el in elements:
                if subdata is not None and el in subdata and key in subdata[el]:
                    max_momentum[el] = subdata[el][key]
                    if "citations" in subdata[el]:
                        for reference in subdata[el]["citations"]:
                            references.add(reference)
                else:
                    max_momentum[el] = data[el][key]
                    if "citations" in data[el]:
                        for reference in data[el]["citations"]:
                            references.add(reference)

            result = {
                "Hamiltonian": {
                    "DFTB": {
                        "SlaterKosterFiles": parameters,
                        "MaxAngularMomentum": max_momentum,
                    }
                }
            }

            # Check if we have Hubbard derivatives
            key = "Hubbard derivative"
            derivative = {}
            for el in elements:
                if subdata is not None and el in subdata and key in subdata[el]:
                    derivative[el] = subdata[el][key]
                elif el in data and key in data[el]:
                    derivative[el] = data[el][key]
            if len(derivative) > 0:
                result["Hamiltonian"]["DFTB"]["HubbardDerivs"] = derivative

            # Check if we have reference energies
            key = "reference energy"
            tmp = {}
            for el in elements:
                if subdata is not None and el in subdata and key in subdata[el]:
                    tmp[el] = float(subdata[el][key])
                elif el in data and key in data[el]:
                    tmp[el] = float(data[el][key])
                else:
                    tmp = None
                    break
            self.parent._reference_energies = tmp

            # Add the references
            for reference in references:
                self.references.cite(
                    raw=self._bibliography[reference],
                    alias=reference,
                    module="dftb+ step",
                    level=1,
                    note="A reference for the DFTB+ Slater-Koster parameters.",
                )
        elif model == "xTB":
            # Broadcast to the parent so that other substeps can use
            self.parent._hamiltonian = P["dataset"]
            self.parent._dataset = dataset
            self.parent._subset = None

            parameter_set_name = parameter_set_name + "-xTB"
            result = {
                "Hamiltonian": {
                    "xTB": {
                        "Method": parameter_set_name,
                    }
                }
            }

            # Add the references
            references = dataset["citations"]
            for reference in references:
                self.references.cite(
                    raw=self._bibliography[reference],
                    alias=reference,
                    module="dftb+ step",
                    level=1,
                    note="A reference for the xTB method and parameters.",
                )

        return result

    def analyze(self, indent="", data={}, out=[]):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        pass
