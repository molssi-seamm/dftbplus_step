# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class BandStructureParameters(seamm.Parameters):
    """The control parameters for the band structure."""

    #:
    parameters = {
        "nPoints": {
            "default": 100,
            "kind": "integer",
            "default_units": "",
            "enumeration": None,
            "format_string": "",
            "description": "Number of points:",
            "help_text": "The number of k-points along the band structure path.",
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

        super().__init__(
            defaults={**BandStructureParameters.parameters, **defaults}, data=data
        )
