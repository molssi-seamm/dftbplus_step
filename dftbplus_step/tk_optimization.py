# -*- coding: utf-8 -*-

"""The graphical part of a DFTB+ Optimization node"""

import logging
import tkinter as tk
import tkinter.ttk as ttk

import dftbplus_step

import seamm_widgets as sw

logger = logging.getLogger(__name__)


class TkOptimization(dftbplus_step.TkEnergy):
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
        """Initialize the graphical Tk DFTB+ optimization step

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

    def create_dialog(
        self, title="Edit DFTB+ Optimization Step", calculation="optimization"
    ):
        """Create the dialog!"""
        self.logger.debug("Creating the dialog")
        super().create_dialog(title=title, calculation=calculation)

        # Create all the widgets
        P = self.node.parameters

        # Frame to isolate widgets
        opt_frame = self["optimization frame"] = ttk.LabelFrame(
            self["frame"],
            borderwidth=4,
            relief="sunken",
            text="Optimization Parameters",
            labelanchor="n",
            padding=10,
        )

        for key in dftbplus_step.OptimizationParameters.parameters:
            if key not in ("structure handling", "configuration name"):
                self[key] = P[key].widget(opt_frame)

        self["optimization method"].bind("<<ComboboxSelected>>", self.reset_dialog)
        self["optimization method"].bind("<Return>", self.reset_dialog)
        self["optimization method"].bind("<FocusOut>", self.reset_dialog)

        # Create the structure-handling widgets
        sframe = self["structure frame"] = ttk.LabelFrame(
            self["frame"], text="Configuration Handling", labelanchor=tk.N
        )
        row = 0
        widgets = []
        for key in ("structure handling", "configuration name"):
            self[key] = P[key].widget(sframe)
            self[key].grid(row=row, column=0, sticky=tk.EW)
            widgets.append(self[key])
            row += 1
        sw.align_labels(widgets, sticky=tk.E)

        self.logger.debug("Finished creating the dialog")

    def reset_dialog(self, widget=None):
        super().reset_dialog()

        row = 0
        self["optimization frame"].grid(row=row, column=1, sticky=tk.EW)
        row += 1
        self["structure frame"].grid(row=row, column=0, columnspan=2)
        row += 1

        # And the widgets in our frame
        self.reset_optimization_frame()

        return row

    def reset_optimization_frame(self):
        """Layout the optimization frame according to the current values."""
        frame = self["optimization frame"]
        for slave in frame.grid_slaves():
            slave.grid_forget()

        method = self["optimization method"].get()

        widgets = []
        widgets1 = []

        row = 0

        w = self["LatticeOpt"]
        w.grid(row=row, column=0, columnspan=3, sticky=tk.W)
        widgets.append(w)
        row += 1

        w = self["optimization method"]
        w.grid(row=row, column=0, columnspan=3, sticky=tk.W)
        widgets.append(w)
        row += 1

        if method == "Rational Function":
            w = self["DiagLimit"]
            w.grid(row=row, column=1, columnspan=1, sticky=tk.W)
            widgets1.append(w)
            row += 1
        elif "LBFGS" in method:
            w = self["Memory"]
            w.grid(row=row, column=1, columnspan=1, sticky=tk.W)
            widgets1.append(w)
            row += 1
        elif "FIRE" in method:
            for widget in (
                "StepSize",
                "nMin",
                "aPar",
                "fInc",
                "fDec",
                "fAlpha",
            ):
                w = self[widget]
                w.grid(row=row, column=1, columnspan=1, sticky=tk.W)
                widgets1.append(w)
                row += 1
            sw.align_labels(widgets1, sticky=tk.E)
        for widget in (
            "MaxForceComponent",
            "MaxSteps",
        ):
            w = self[widget]
            w.grid(row=row, column=0, columnspan=3, sticky=tk.W)
            widgets.append(w)
            row += 1

        sw.align_labels(widgets, sticky=tk.E)

        frame.columnconfigure(0, minsize=50)

        return row
