# -*- coding: utf-8 -*-

"""
dftbplus_step
A step for DFTB+ in a SEAMM flowchart
"""

# Bring up the classes so that they appear to be directly in
# the dftbplus_step package.

from dftbplus_step.dftbplus import Dftbplus  # noqa: F401, E501
from dftbplus_step.dftbplus_parameters import DftbplusParameters  # noqa: F401, E501
from dftbplus_step.dftbplus_step import DftbplusStep  # noqa: F401, E501
from dftbplus_step.tk_dftbplus import TkDftbplus  # noqa: F401, E501

# Handle versioneer
from ._version import get_versions
__author__ = """Paul Saxe"""
__email__ = 'psaxe@molssi.org'
versions = get_versions()
__version__ = versions['version']
__git_revision__ = versions['full-revisionid']
del get_versions, versions
