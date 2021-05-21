# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class ChooseParametersParameters(seamm.Parameters):
    """The control parameters for initializing DFTB+"""

    parameters = {
        "elements": {
            "default": "",
            "kind": "periodic table",
            "default_units": None,
            "enumeration": None,
            "format_string": "",
            "description": "Elements:",
            "help_text": "The elements to include.",
        },
        "dataset": {
            "default": "3ob",
            "kind": "string",
            "default_units": None,
            "enumeration": (
                "3ob",
                "matsci",
                "mio",
                "auorg",
                "borg",
                "halorg",
                "ob2",
                "pbc",
                "siband",
                "rare",
            ),
            "format_string": "",
            "description": "Slater-Koster dataset:",
            "help_text": ("The main set of Slater-Koster potentials to use."),
        },
        "subset": {
            "default": "none",
            "kind": "string",
            "default_units": None,
            "enumeration": ("none", "3ob-freq", "3ob-hhmod", "3ob-nhmod", "3ob-ophyd"),
            "format_string": "",
            "description": "Specialized Slater-Koster potentials to add:",
            "help_text": (
                "The specialized set of Slater-Koster potentials to add to "
                "the main set."
            ),
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={**ChooseParametersParameters.parameters, **defaults}, data=data
        )
