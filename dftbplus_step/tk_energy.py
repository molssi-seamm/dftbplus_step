# -*- coding: utf-8 -*-

"""The graphical part of a DFTB+ Energy node"""

import logging
import tkinter as tk
import tkinter.ttk as ttk

import dftbplus_step
import seamm
import seamm_widgets as sw

logger = logging.getLogger(__name__)


class TkEnergy(seamm.TkNode):
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
    ):
        """Initialize the graphical Tk DFTB+ Energy step

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
        )

    def right_click(self, event):
        """Probably need to add our dialog..."""

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def create_dialog(self, title="Edit DFTB+ Energy Step"):
        """Create the dialog!"""
        self.logger.debug("Creating the dialog")
        super().create_dialog(title=title, widget="notebook", results_tab=True)

        # Create all the widgets
        P = self.node.parameters

        # Frame to isolate widgets
        e_frame = self["energy frame"] = ttk.LabelFrame(
            self["frame"],
            borderwidth=4,
            relief="sunken",
            text="Hamiltonian Parameters",
            labelanchor="n",
            padding=10,
        )

        for key in dftbplus_step.EnergyParameters.parameters:
            if key not in ("results", "extra keywords", "create tables"):
                self[key] = P[key].widget(e_frame)

        # Set the callbacks for changes
        for widget in ("SCC", "HCorrection", "k-grid method"):
            w = self[widget]
            w.combobox.bind("<<ComboboxSelected>>", self.reset_energy_frame)
            w.combobox.bind("<Return>", self.reset_energy_frame)
            w.combobox.bind("<FocusOut>", self.reset_energy_frame)

        # A tab for output -- orbitals, etc.
        notebook = self["notebook"]
        self["output frame"] = oframe = ttk.Frame(notebook)
        notebook.insert(self["results frame"], oframe, text="Output", sticky="new")

        # Frame to isolate widgets
        p_frame = self["plot frame"] = ttk.LabelFrame(
            self["output frame"],
            borderwidth=4,
            relief="sunken",
            text="Plots",
            labelanchor="n",
            padding=10,
        )

        for key in dftbplus_step.EnergyParameters.output:
            self[key] = P[key].widget(p_frame)

        # Set the callbacks for changes
        for widget in ("orbitals",):
            w = self[widget]
            w.combobox.bind("<<ComboboxSelected>>", self.reset_plotting)
            w.combobox.bind("<Return>", self.reset_plotting)
            w.combobox.bind("<FocusOut>", self.reset_plotting)
        p_frame.grid(row=0, column=0, sticky="new")
        oframe.columnconfigure(0, weight=1)

        self.reset_plotting()

        self.setup_results()

        self.logger.debug("Finished creating the dialog")

    def reset_dialog(self, widget=None):
        frame = self["frame"]
        for slave in frame.grid_slaves():
            slave.grid_forget()

        # Put in the energy frame
        row = 0
        self["energy frame"].grid(row=row, column=0, sticky=tk.N)
        row += 1

        # and the widgets in it
        self.reset_energy_frame()

        return row

    def reset_energy_frame(self, widget=None):
        frame = self["energy frame"]
        for slave in frame.grid_slaves():
            slave.grid_forget()

        scc = self["SCC"].get() == "Yes"

        widgets = []
        widgets1 = []
        widgets2 = []

        row = 0
        self["SpinPolarisation"].grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        widgets.append(self["SpinPolarisation"])
        row += 1
        self["primitive cell"].grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        widgets.append(self["primitive cell"])
        row += 1
        self["SCC"].grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        widgets.append(self["SCC"])
        row += 1
        if scc:
            for widget in ("SCCTolerance", "MaxSCCIterations", "ThirdOrder"):
                self[widget].grid(row=row, column=1, columnspan=2, sticky=tk.EW)
                widgets1.append(self[widget])
                row += 1

            self["HCorrection"].grid(row=row, column=1, columnspan=2, sticky=tk.EW)
            widgets1.append(self["HCorrection"])
            row += 1

            hcorrection = self["HCorrection"].get()
            if hcorrection == "Damping":
                self["Damping Exponent"].grid(row=row, column=1, sticky=tk.EW)
                widgets2.append(self["Damping Exponent"])
                row += 1

        # The Brillouin zone integration grid
        kmethod = self["k-grid method"].get()
        self["k-grid method"].grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        widgets.append(self["k-grid method"])
        row += 1
        if kmethod == "grid spacing":
            self["k-spacing"].grid(row=row, column=1, columnspan=2, sticky=tk.EW)
            widgets1.append(self["k-spacing"])
            row += 1
        elif kmethod == "supercell folding":
            self["na"].grid(row=row, column=1, columnspan=2, sticky=tk.EW)
            widgets1.append(self["na"])
            row += 1
            self["nb"].grid(row=row, column=1, columnspan=2, sticky=tk.EW)
            widgets1.append(self["nb"])
            row += 1
            self["nc"].grid(row=row, column=1, columnspan=2, sticky=tk.EW)
            widgets1.append(self["nc"])
            row += 1

        sw.align_labels(widgets, sticky=tk.E)
        sw.align_labels(widgets1, sticky=tk.E)
        sw.align_labels(widgets2, sticky=tk.E)

        frame.columnconfigure(0, minsize=30)

        return row

    def reset_plotting(self, widget=None):
        frame = self["plot frame"]
        for slave in frame.grid_slaves():
            slave.grid_forget()

        plot_orbitals = self["orbitals"].get() == "yes"

        widgets = []

        row = 0
        for key in (
            "total density",
            "total spin density",
            "difference density",
            "orbitals",
        ):
            self[key].grid(row=row, column=0, columnspan=4, sticky=tk.EW)
            widgets.append(self[key])
            row += 1

        if plot_orbitals:
            key = "selected orbitals"
            self[key].grid(row=row, column=1, columnspan=4, sticky=tk.EW)
            row += 1
            key = "selected k-points"
            self[key].grid(row=row, column=1, columnspan=4, sticky=tk.EW)
            row += 1

        key = "region"
        self[key].grid(row=row, column=0, columnspan=4, sticky=tk.EW)
        widgets.append(self[key])
        row += 1

        key = "nx"
        self[key].grid(row=row, column=0, columnspan=2, sticky=tk.EW)
        widgets.append(self[key])
        self["ny"].grid(row=row, column=2, sticky=tk.EW)
        self["nz"].grid(row=row, column=3, sticky=tk.EW)

        sw.align_labels(widgets, sticky=tk.E)
        frame.columnconfigure(0, minsize=10)
        frame.columnconfigure(4, weight=1)

        return row
