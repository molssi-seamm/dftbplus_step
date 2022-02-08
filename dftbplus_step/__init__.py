# -*- coding: utf-8 -*-

"""
dftbplus_step
A step for DFTB+ in a SEAMM flowchart
"""

# Bring up the classes so that they appear to be directly in
# the dftbplus_step package.

# Main classes
from dftbplus_step.dftbplus import Dftbplus, deep_merge, dict_to_hsd  # noqa: F401
from dftbplus_step.dftbplus_parameters import DftbplusParameters  # noqa: F401
from dftbplus_step.dftbplus_step import DftbplusStep  # noqa: F401
from dftbplus_step.tk_dftbplus import TkDftbplus  # noqa: F401

# The metadata
from dftbplus_step.metadata import properties  # noqa: F401

# The substeps
from dftbplus_step.choose_parameters import ChooseParameters  # noqa: F401
from dftbplus_step.choose_parameters_parameters import (  # noqa: F401
    ChooseParametersParameters,
)
from dftbplus_step.choose_parameters_step import (  # noqa: F401
    ChooseParametersStep,
)
from dftbplus_step.tk_choose_parameters import TkChooseParameters  # noqa: F401

from dftbplus_step.energy import Energy  # noqa: F401
from dftbplus_step.energy_parameters import EnergyParameters  # noqa: F401
from dftbplus_step.energy_step import EnergyStep  # noqa: F401
from dftbplus_step.tk_energy import TkEnergy  # noqa: F401

from dftbplus_step.optimization import Optimization  # noqa: F401
from dftbplus_step.optimization_parameters import (  # noqa: F401
    OptimizationParameters,
)
from dftbplus_step.optimization_step import OptimizationStep  # noqa: F401
from dftbplus_step.tk_optimization import TkOptimization  # noqa: F401

from dftbplus_step.band_structure import BandStructure  # noqa: F401
from dftbplus_step.band_structure_parameters import (  # noqa: F401
    BandStructureParameters,
)
from dftbplus_step.band_structure_step import BandStructureStep  # noqa: F401
from dftbplus_step.tk_band_structure import TkBandStructure  # noqa: F401

# Handle versioneer
from ._version import get_versions

__author__ = """Paul Saxe"""
__email__ = "psaxe@molssi.org"
versions = get_versions()
__version__ = versions["version"]
__git_revision__ = versions["full-revisionid"]
del get_versions, versions
