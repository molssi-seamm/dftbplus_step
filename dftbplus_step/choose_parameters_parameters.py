# -*- coding: utf-8 -*-
"""Global control parameters for DFTB+
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class ChooseParametersParameters(seamm.Parameters):
    """The control parameters for initializing DFTB+"""

    parameters = {
        "model": {
            "default": "any",
            "kind": "string",
            "default_units": None,
            "enumeration": (
                "any",
                "Density Functional Tight Binding (DFTB)",
                "eXtended Tight Binding (xTB)",
            ),
            "format_string": "",
            "description": "Model:",
            "help_text": "The model to use.",
        },
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
                "DFTB - 3ob",
                "DFTB - matsci",
                "DFTB - mio",
                "DFTB - auorg",
                "DFTB - borg",
                "DFTB - halorg",
                "DFTB - ob2",
                "DFTB - pbc",
                "DFTB - siband",
                "DFTB - rare",
            ),
            "format_string": "",
            "description": "Parameterization:",
            "help_text": "The parameterization to use.",
        },
        "subset": {
            "default": "none",
            "kind": "string",
            "default_units": None,
            "enumeration": ("none", "3ob-freq", "3ob-hhmod", "3ob-nhmod", "3ob-ophyd"),
            "format_string": "",
            "description": "Specialized parameterization to add:",
            "help_text": "The specialized set parameters to add to the main set.",
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={**ChooseParametersParameters.parameters, **defaults}, data=data
        )
