# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""

import dftbplus_step
import logging

logger = logging.getLogger(__name__)


class OptimizationParameters(dftbplus_step.EnergyParameters):
    """The control parameters for optimization using DFTB+"""

    parameters = {
        "optimization method": {
            "default": 'Direct inversion of iterative subspace (gDIIS)',
            "kind": "enumeration",
            "default_units": "",
            "enumeration": (
                'Steepest descents',
                'Conjugate gradients',
                'Direct inversion of iterative subspace (gDIIS)',
                'Limited-memory Broyden-Fletcher-Goldfarb-Shanno (LBFGS)',
                'Fast inertial relaxation engine (FIRE)'
            ),
            "format_string": "s",
            "description": "Method:",
            "help_text": ("The optimization method to use.")
        },
        "MaxForceComponent": {
            "default": 1.0E-04,
            "kind": "float",
            "default_units": "hartree/bohr",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Convergence criterion:",
            "help_text": (
                "Optimisation is stopped if the force component with the "
                "maximal absolute value goes below this threshold."
            )
        },
        "MaxSteps": {
            "default": 200,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Maximum number of steps:",
            "help_text": (
                "Maximum number of steps after which the optimisation should "
                "stop (unless already stopped by achieving convergence). "
                "Setting this value as -1 runs a huge() number of iterations."
            )
        },
        "LatticeOpt": {
            "default": "Yes",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'Yes',
                'No'
            ),
            "format_string": "",
            "description": "Optimize the cell:",
            "help_text": (
                "Allow the lattice vectors to change during optimisation. "
                "MovedAtoms can be optionally used with lattice optimisation "
                "if the atomic coordinates are to be co-optimised with the "
                "lattice."
            )
        },
        "constrain_cell": {
            "default": "No",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'No',
                'Angles',
                'Isotropically'
            ),
            "format_string": "",
            "description": "Constrain the cell:",
            "help_text": (
                "Constrain the cell during optimisation."
            )
        },
        "fix_a": {
            "default": "No",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'Yes',
                'No'
            ),
            "format_string": "",
            "description": "Fix length 'a':",
            "help_text": (
                "Keep the length of the first lattice vector ('a') fixed "
                "during the optimisation."
            )
        },
        "fix_b": {
            "default": "No",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'Yes',
                'No'
            ),
            "format_string": "",
            "description": "Fix length 'b':",
            "help_text": (
                "Keep the length of the second lattice vector ('b') fixed "
                "during the optimisation."
            )
        },
        "fix_c": {
            "default": "No",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'Yes',
                'No'
            ),
            "format_string": "",
            "description": "Fix length 'c':",
            "help_text": (
                "Keep the length of the third lattice vector ('c') fixed "
                "during the optimisation."
            )
        },
        "pressure": {
            "default": 0.0,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Pressure:",
            "help_text": ("The applied pressure.")
        },
        "MaxAtomStep": {
            "default": 0.2,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Maximum atom step:",
            "help_text": (
                "The maximum possible line search step size for atomic "
                "relaxation."
            )
        },
        "MaxLatticeStep": {
            "default": 0.2,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Maximum step in the lattice:",
            "help_text": (
                "The maximum possible line search step size for the cell "
                "relaxation. For fixed angles it is a percentage of the "
                "lattice parameter; for isotropic constraint, of the volume."
            )
        },
        "stop_if_scc_fails": {
            "default": "Yes",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'Yes',
                'No'
            ),
            "format_string": "",
            "description": "Stop if SCC fails:",
            "help_text": (
                "Stop if the self consistent charge calculation fails to "
                "converge."
            )
        },
        "StepSize": {
            "default": 100.0,
            "kind": "float",
            "default_units": "a_u_time",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Step size:",
            "help_text": (
                "Step size (dt) along the forces. The displacement dxi along "
                "the ith coordinate is given for each atom as "
                "dxi = fi2mdt2, where fi is the appropriate force component "
                "and m is the mass of the atom."
            )
        },
        "Alpha": {
            "default": 0.1,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Initial scaling parameter:",
            "help_text": (
                "Initial scaling parameter to prevent the iterative space "
                "becoming exhausted (this is dynamically adjusted during the "
                "run)."
            )
        },
        "Generations": {
            "default": 8,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Generations:",
            "help_text": "Number of generations to consider for the mixing."
        },
        "Memory": {
            "default": 20,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Number of steps to remember:",
            "help_text": (
                "Number of last steps which are saved and used to calculate "
                "the next step via the LBFGS algorithm. The literature "
                "recommends that Memory should between 3 and 20."
            )
        },
        "LineSearch": {
            "default": "No",
            "kind": "string",
            "default_units": "",
            "enumeration": (
                'Yes',
                'No'
            ),
            "format_string": "",
            "description": "Use a linesearch rather than Newton step:",
            "help_text": (
                "Should a line search be performed, instead of a quasi-Newton "
                "step along the LBFGS direction."
            )
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={**OptimizationParameters.parameters, **defaults},
            data=data
        )
