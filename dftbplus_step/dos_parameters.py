# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class DOSParameters(seamm.Parameters):
    """The control parameters for the band structure."""

    #:
    parameters = {
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
            "default": 10,
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
            "default": 10,
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
            "default": 10,
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
            "default": 0.05,
            "kind": "float",
            "default_units": "1/Å",
            "enumeration": None,
            "format_string": "",
            "description": "K-spacing:",
            "help_text": "The spacing of the grid in reciprocal space.",
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
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(defaults={**DOSParameters.parameters, **defaults}, data=data)
