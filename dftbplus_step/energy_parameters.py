# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class EnergyParameters(seamm.Parameters):
    """The control parameters for the DFTB+ Hamiltonian

    Example::

        Hamiltonian = DFTB {
          Scc = Yes
          SlaterKosterFiles = {
            O-O = "../../slakos/mio-ext/O-O.skf"
            O-H = "../../slakos/mio-ext/O-H.skf"
            H-O = "../../slakos/mio-ext/H-O.skf"
            H-H = "../../slakos/mio-ext/H-H.skf"
          }
          MaxAngularMomentum = {
            O = "p"
            H = "s"
          }
          PolynomialRepulsive = {}
          ShellResolvedSCC = No
          OldSKInterpolation = No
          RangeSeparated = None {}
          ReadInitialCharges = No
          InitialCharges = {}
          SCCTolerance = 1.0000000000000001E-005
          HCorrection = None {}
          SpinPolarisation = {}
          ElectricField = {}
          Solver = RelativelyRobust {}
          Charge = 0.0000000000000000
          MaxSCCIterations = 100
          OnSiteCorrection = {}
          Dispersion = {}
          Solvation = {}
          Electrostatics = GammaFunctional {}
          ThirdOrder = No
          ThirdOrderFull = No
          Differentiation = FiniteDiff {
            Delta = 1.2207031250000000E-004
          }
          ForceEvaluation = "Traditional"
          Mixer = Broyden {
            MixingParameter = 0.20000000000000001
            InverseJacobiWeight = 1.0000000000000000E-002
            MinimalWeight = 1.0000000000000000
            MaximalWeight = 100000.00000000000
            WeightFactor = 1.0000000000000000E-002
          }
          Filling = Fermi {
            Temperature = 0.0000000000000000
          }
        }
    """

    parameters = {
        "primitive cell": {
            "default": "Yes",
            "kind": "boolean",
            "default_units": "",
            "enumeration": ("Yes", "No"),
            "format_string": "",
            "description": "Use primitive cell:",
            "help_text": "Whether to use the primitive cell for the calculation.",
        },
        "SCC": {
            "default": "Yes",
            "kind": "string",
            "default_units": "",
            "enumeration": ("Yes", "No"),
            "format_string": "",
            "description": "Self-consistent charges:",
            "help_text": ("Whether to do a self-consistent charge calculation."),
        },
        "SCCTolerance": {
            "default": 1.0e-05,
            "kind": "float",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "Convergence criterion:",
            "help_text": (
                "Stopping criteria for the SCC. Specifies the tolerance for "
                "the maximum difference in any charge between two SCC cycles."
            ),
        },
        "MaxSCCIterations": {
            "default": 100,
            "kind": "integer",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "Maximum number of iterations:",
            "help_text": (
                "Maximal number of SCC cycles to reach convergence. If "
                "convergence is not reached after the specified number of "
                "steps, the program stops unless requested elsewhere."
            ),
        },
        "ShellResolvedSCC": {
            "default": "no",
            "kind": "string",
            "default_units": "",
            "enumeration": ("yes", "no"),
            "format_string": "",
            "description": "Shell-resolved charges:",
            "help_text": (
                "Whether to use shell-resolved charges. If the parameter set does not "
                "support this, it will be ignored."
            ),
        },
        "use atom charges": {
            "default": "yes",
            "kind": "string",
            "default_units": "",
            "enumeration": ("yes", "no"),
            "format_string": "",
            "description": "Use existing atomic charges:",
            "help_text": "Whether to use existing charges on the atoms.",
        },
        "ThirdOrder": {
            "default": "Default for parameters",
            "kind": "string",
            "default_units": "",
            "enumeration": ("No", "Default for parameters", "Partial", "Full"),
            "format_string": "",
            "description": "Use 3rd order corrections:",
            "help_text": ("Whether to use 3rd order corrections."),
        },
        "HCorrection": {
            "default": "Default for parameters",
            "kind": "string",
            "default_units": "",
            "enumeration": ("None", "Default for parameters", "Damping", "DFTB3-D3H5"),
            "format_string": "",
            "description": "Hydrogen interaction correction:",
            "help_text": (
                "Whether and how to correct the interactions of hydrogens, "
                "mainly hydrogen bonds."
            ),
        },
        "Damping Exponent": {
            "default": 4.0,
            "kind": "float",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "Damping exponent:",
            "help_text": (
                "The exponent for the short range damping of interactions "
                "where at least one atom is a hydrogen."
            ),
        },
        "results": {
            "default": {},
            "kind": "dictionary",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "results",
            "help_text": ("The results to save to variables or in " "tables. "),
        },
        "create tables": {
            "default": "yes",
            "kind": "boolean",
            "default_units": None,
            "enumeration": ("yes", "no"),
            "format_string": "",
            "description": "Create tables as needed:",
            "help_text": (
                "Whether to create tables as needed for "
                "results being saved into tables."
            ),
        },
        "k-grid method": {
            "default": "grid spacing",
            "kind": "string",
            "default_units": "",
            "enumeration": ("supercell folding", "grid spacing"),
            "format_string": "",
            "description": "Specify k-space grid using:",
            "help_text": ("How to specify the k-space integration grid."),
        },
        "na": {
            "default": 4,
            "kind": "integer",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "NPoints in a:",
            "help_text": (
                "Number of points in the first direction of the Brillouin zone."
            ),
        },
        "nb": {
            "default": 4,
            "kind": "integer",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "NPoints in b:",
            "help_text": (
                "Number of points in the second direction of the Brillouin zone."
            ),
        },
        "nc": {
            "default": 4,
            "kind": "integer",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "NPoints in c:",
            "help_text": (
                "Number of points in the third direction of the Brillouin zone."
            ),
        },
        "k-spacing": {
            "default": 0.2,
            "kind": "float",
            "default_units": "1/Å",
            "enumeration": None,
            "format_string": "",
            "description": "K-spacing:",
            "help_text": "The spacing of the grid in reciprocal space.",
        },
        "SpinPolarisation": {
            "default": "none",
            "kind": "string",
            "default_units": "",
            "enumeration": ("none", "collinear", "noncollinear"),
            "format_string": "",
            "description": "Spin polarization:",
            "help_text": "How to handle spin polarization",
        },
        "RelaxTotalSpin": {
            "default": "yes",
            "kind": "string",
            "default_units": "",
            "enumeration": ("no", "yes"),
            "format_string": "",
            "description": "Optimize the spin:",
            "help_text": "Whether to optimize the spin polarization or leave it fixed.",
        },
        "ShellResolvedSpin": {
            "default": "yes",
            "kind": "string",
            "default_units": "",
            "enumeration": ("yes", "no"),
            "format_string": "",
            "description": "Shell-resolved spins:",
            "help_text": (
                "Whether to use shell-resolved spin. If the parameter set does not "
                "support this, it will be ignored."
            ),
        },
        "use atom spins": {
            "default": "yes",
            "kind": "string",
            "default_units": "",
            "enumeration": ("yes", "no"),
            "format_string": "",
            "description": "Use existing atomic spins:",
            "help_text": "Whether to use existing spins on the atoms.",
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={**EnergyParameters.parameters, **defaults}, data=data
        )
