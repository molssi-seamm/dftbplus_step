# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""
import logging

import dftbplus_step
import seamm

logger = logging.getLogger(__name__)


class OptimizationParameters(dftbplus_step.EnergyParameters):
    """The control parameters for optimization using DFTB+"""

    parameters = {
        "optimization method": {
            "default": "Rational Function",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": (
                "Rational Function",
                "Limited-memory Broyden-Fletcher-Goldfarb-Shanno (LBFGS)",
                "Fast inertial relaxation engine (FIRE)",
                "Steepest descent",
            ),
            "format_string": "s",
            "description": "Method:",
            "help_text": ("The optimization method to use."),
        },
        "MaxForceComponent": {
            "default": 1.0e-04,
            "kind": "float",
            "default_units": "hartree/bohr",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Convergence criterion:",
            "help_text": (
                "Optimisation is stopped if the force component with the "
                "maximal absolute value goes below this threshold."
            ),
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
            ),
        },
        "LatticeOpt": {
            "default": "Yes",
            "kind": "string",
            "default_units": "",
            "enumeration": ("Yes", "No"),
            "format_string": "",
            "description": "Optimize the cell (if periodic):",
            "help_text": (
                "Allow the lattice vectors to change during optimisation. "
                "MovedAtoms can be optionally used with lattice optimisation "
                "if the atomic coordinates are to be co-optimised with the "
                "lattice."
            ),
        },
        "pressure": {
            "default": 0.0,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Pressure:",
            "help_text": ("The applied pressure."),
        },
        "DiagLimit": {
            "default": 0.01,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Limit for diagonal Hessian elements:",
            "help_text": (
                "The lower limit for the diagonal Hessian elements in the BFGS-like "
                "update step in the rational optimizer."
            ),
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
            ),
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
            ),
        },
        "nMin": {
            "default": 5,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Steps before increasing stepsize:",
            "help_text": (
                "The minimum number of steps before the step size is increased."
            ),
        },
        "aPar": {
            "default": 0.1,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Velocity update parameter:",
            "help_text": "Parameter for the update of the velocities.",
        },
        "fInc": {
            "default": 1.1,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Stepsize increase factor:",
            "help_text": "The factor to increase the step size",
        },
        "fDec": {
            "default": 0.5,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Stepsize decrease factor:",
            "help_text": "The factor to decrease the step size",
        },
        "fAlpha": {
            "default": 0.99,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "",
            "description": "Alpha update on reset:",
            "help_text": "The factor for the update the alpha parameter on reset.",
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={
                **OptimizationParameters.parameters,
                **seamm.standard_parameters.structure_handling_parameters,
                **defaults,
            },
            data=data,
        )

        # Do any local editing of defaults
        tmp = self["structure handling"]
        tmp.description = "Structure handling:"

        tmp = self["system name"]
        tmp._data["enumeration"] = (*tmp.enumeration, "optimized with {Hamiltonian}")
        tmp.default = "keep current name"

        tmp = self["configuration name"]
        tmp._data["enumeration"] = ["optimized with {Hamiltonian}", *tmp.enumeration]
        tmp.default = "optimized with {Hamiltonian}"

    def update(self, data):
        """Update values from a dict

        This version filters out old, obsolete parameters for compatibility
        """
        for key in (
            "constrain_cell",
            "fix_a",
            "fix_b",
            "fix_c",
            "MaxAtomStep",
            "MaxLatticeStep",
            "stop_if_scc_fails",
            "Alpha",
            "Generations",
            "LineSearch",
        ):
            if key in data:
                del data[key]

        for key in ("system name", "configuration name"):
            if key in data and data[key] == "optimized with <Hamiltonian>":
                data[key] = "optimized with {Hamiltonian}"

        super().update(data)
