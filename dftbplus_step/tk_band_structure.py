# -*- coding: utf-8 -*-

"""The graphical part of a DFTB+ BandStructure node"""

import logging
import tkinter as tk

import dftbplus_step
import seamm

logger = logging.getLogger(__name__)


class TkBandStructure(seamm.TkNode):
    def __init__(
        self,
        tk_flowchart=None,
        node=None,
        canvas=None,
        x=120,
        y=20,
        w=200,
        h=50,
        my_logger=logger,
        keyword_metadata=None,
    ):
        """Initialize the graphical Tk DFTB+ BandStructure step

        Keyword arguments:
        """
        self.results_widgets = []

        super().__init__(
            tk_flowchart=tk_flowchart,
            node=node,
            canvas=canvas,
            x=x,
            y=y,
            w=w,
            h=h,
            my_logger=my_logger,
            keyword_metadata=keyword_metadata,
        )

    def right_click(self, event):
        """Probably need to add our dialog..."""

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def create_dialog(self, title="Edit DFTB+ BandStructure Step"):
        """Create the dialog!"""
        self.logger.debug("Creating the dialog")
        super().create_dialog(title=title, widget="notebook", results_tab=True)

        # Create all the widgets
        P = self.node.parameters

        frame = self["frame"]

        for key in dftbplus_step.BandStructureParameters.parameters:
            if key not in ("results", "extra keywords", "create tables"):
                self[key] = P[key].widget(frame)

        # self.setup_results(dftbplus_step.properties, calculation=calculation)

        self.logger.debug("Finished creating the dialog")

    def reset_dialog(self, widget=None):
        frame = self["frame"]
        for slave in frame.grid_slaves():
            slave.grid_forget()

        # Put in the widgets
        row = 0
        self["nPoints"].grid(row=row, column=0, sticky=tk.N)
        row += 1

        return row
