# -*- coding: utf-8 -*-

"""Main module."""

import dftbplus_step


class EnergyStep(object):
    my_description = {
        "description": "Single-point energy with DFTB+",
        "group": "Simulations",
        "name": "Single-point Energy",
    }

    def __init__(self, flowchart=None, gui=None):
        """Initialize this helper class, which is used by
        the application via stevedore to get information about
        and create node objects for the flowchart
        """
        pass

    def description(self):
        """Return a description of what this extension does"""
        return EnergyStep.my_description

    def create_node(self, flowchart=None, **kwargs):
        """Return the new node object"""
        return dftbplus_step.Energy(flowchart=flowchart, **kwargs)

    def create_tk_node(self, canvas=None, **kwargs):
        """Return the graphical Tk node object"""
        return dftbplus_step.TkEnergy(canvas=canvas, **kwargs)
