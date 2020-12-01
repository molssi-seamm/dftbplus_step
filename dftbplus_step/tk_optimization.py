# -*- coding: utf-8 -*-

"""The graphical part of a DFTB+ Optimization node"""

import logging
import tkinter as tk
import tkinter.ttk as ttk

import dftbplus_step

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
        keyword_metadata=None
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
            keyword_metadata=keyword_metadata
        )

    def right_click(self, event):
        """Probably need to add our dialog...
        """

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def create_dialog(
        self,
        title='Edit DFTB+ Optimization Step',
        calculation='optimization'
    ):
        """Create the dialog!"""
        self.logger.debug('Creating the dialog')
        super().create_dialog(title=title, calculation=calculation)

        # Create all the widgets
        P = self.node.parameters

        # Frame to isolate widgets
        opt_frame = self['optimization frame'] = ttk.LabelFrame(
            self['frame'],
            borderwidth=4,
            relief='sunken',
            text='Optimization Parameters',
            labelanchor='n',
            padding=10
        )

        for key in dftbplus_step.OptimizationParameters.parameters:
            self[key] = P[key].widget(opt_frame)

        self.logger.debug('Finished creating the dialog')

    def reset_dialog(self, widget=None):
        super().reset_dialog()

        row = 0
        self['optimization frame'].grid(row=row, column=1, sticky=tk.EW)
        row += 1

        # And the widgets in our frame
        self.reset_optimization_frame()

        return row

    def reset_optimization_frame(self):
        """Layout the optimization frame according to the current values.

                SD                   CG                  gDIIS                LBFGS              FIRE
            ------------------   -------------------  -------------------  -------------------  --------
            MovedAtoms           MovedAtoms           MovedAtoms           MovedAtoms           TimeStep
            MaxForceComponent    MaxForceComponent    MaxForceComponent    MaxForceComponent
            MaxSteps             MaxSteps             MaxSteps             MaxSteps
            OutputPrefix         OutputPrefix         OutputPrefix         OutputPrefix
            AppendGeometries     AppendGeometries     AppendGeometries     AppendGeometries
            Constraints          Constraints          Constraints          Constraints
            LatticeOpt           LatticeOpt           LatticeOpt           LatticeOpt
            FixAngles            FixAngles            FixAngles            FixAngles
            FixLengths
            Isotropic            Isotropic            Isotropic            Isotropic
            Pressure             Pressure             Pressure             Pressure
            MaxAtomStep          MaxAtomStep                               MaxAtomStep
            MaxLatticeStep       MaxLatticeStep       MaxLatticeStep       MaxLatticeStep
            ConvergentForcesOnly ConvergentForcesOnly ConvergentForcesOnly ConvergentForcesOnly
            StepSize                                  Alpha                Memory
                                                      Generations          LineSearch
        """  # noqa: E501
        frame = self['optimization frame']
        for slave in frame.grid_slaves():
            slave.grid_forget()

        method = self['optimization method'].get()

        widgets = []
        widgets1 = []

        row = 0

        w = self['optimization method']
        w.grid(row=row, column=0, columnspan=2, sticky=tk.EW)
        widgets.append(w)
        row += 1

        if method == "Steepest descents":
            w = self['StepSize']
            w.grid(row=row, column=1, sticky=tk.EW)
            widgets1.append(w)
            row += 1
        elif 'gDIIS' in method:
            w = self['Alpha']
            w.grid(row=row, column=1, sticky=tk.EW)
            widgets1.append(w)
            row += 1

            w = self['Generations']
            w.grid(row=row, column=1, sticky=tk.EW)
            widgets1.append(w)
            row += 1
        elif 'LBFGS' in method:
            w = self['Memory']
            w.grid(row=row, column=1, sticky=tk.EW)
            widgets1.append(w)
            row += 1

            w = self['LineSearch']
            w.grid(row=row, column=1, sticky=tk.EW)
            widgets1.append(w)
            row += 1

        for widget in (
            'MaxForceComponent', 'MaxSteps', 'MaxAtomStep', 'stop_if_scc_fails'
        ):
            w = self[widget]
            w.grid(row=row, column=0, columnspan=2, sticky=tk.EW)
            widgets.append(w)
            row += 1

        return row
