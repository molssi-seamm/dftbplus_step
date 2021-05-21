# -*- coding: utf-8 -*-

"""The graphical part of a DFTB+ step"""

import seamm


class TkDftbplus(seamm.TkNode):
    """
    The graphical part of a DFTB+ step in a flowchart.

    Attributes
    ----------
    tk_flowchart : TkFlowchart = None
        The flowchart that we belong to.
    node : Node = None
        The corresponding node of the non-graphical flowchart
    canvas: tkCanvas = None
        The Tk Canvas to draw on
    dialog : Dialog
        The Pmw dialog object
    x : int = None
        The x-coordinate of the center of the picture of the node
    y : int = None
        The y-coordinate of the center of the picture of the node
    w : int = 200
        The width in pixels of the picture of the node
    h : int = 50
        The height in pixels of the picture of the node
    self[widget] : dict
        A dictionary of tk widgets built using the information
        contained in DFTB+_parameters.py

    See Also
    --------
    Dftbplus, TkDftbplus,
    DftbplusParameters,
    """

    def __init__(
        self,
        tk_flowchart=None,
        node=None,
        namespace="org.molssi.seamm.dftbplus.tk",
        canvas=None,
        x=None,
        y=None,
        w=200,
        h=50,
    ):
        """
        Initialize a graphical node.

        Parameters
        ----------
        tk_flowchart: Tk_Flowchart
            The graphical flowchart that we are in.
        node: Node
            The non-graphical node for this step.
        namespace: str
            The stevedore namespace for finding sub-nodes.
        canvas: Canvas
           The Tk canvas to draw on.
        x: float
            The x position of the nodes center on the canvas.
        y: float
            The y position of the nodes cetner on the canvas.
        w: float
            The nodes graphical width, in pixels.
        h: float
            The nodes graphical height, in pixels.

        Returns
        -------
        None
        """
        self.namespace = namespace
        self.dialog = None

        super().__init__(
            tk_flowchart=tk_flowchart, node=node, canvas=canvas, x=x, y=y, w=w, h=h
        )
        self.create_dialog()

    def create_dialog(self):
        """
        Create the dialog. A set of widgets will be chosen by default
        based on what is specified in the DFTB+_parameters
        module.

        Parameters
        ----------
        None

        Returns
        -------
        None

        See Also
        --------
        TkDftbplus.reset_dialog
        """

        frame = super().create_dialog(title="DFTB+")
        # make it large!
        screen_w = self.dialog.winfo_screenwidth()
        screen_h = self.dialog.winfo_screenheight()
        w = int(0.9 * screen_w)
        h = int(0.8 * screen_h)
        x = int(0.05 * screen_w / 2)
        y = int(0.1 * screen_h / 2)

        self.dialog.geometry("{}x{}+{}+{}".format(w, h, x, y))

        self.tk_subflowchart = seamm.TkFlowchart(
            master=frame, flowchart=self.node.subflowchart, namespace=self.namespace
        )
        self.tk_subflowchart.draw()

    def right_click(self, event):
        """
        Handles the right click event on the node.

        Parameters
        ----------
        event : Tk Event

        Returns
        -------
        None

        See Also
        --------
        TkDftbplus.edit
        """

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def edit(self):
        """Present a dialog for editing the DFTB+ input

        Parameters
        ----------
        None

        Returns
        -------
        None

        See Also
        --------
        TkDftbplus.right_click
        """

        if self.dialog is None:
            self.create_dialog()

        self.dialog.activate(geometry="centerscreenfirst")

    def handle_dialog(self, result):
        """Handle the closing of the edit dialog

        What to do depends on the button used to close the dialog. If
        the user closes it by clicking the 'x' of the dialog window,
        None is returned, which we take as equivalent to cancel.

        Parameters
        ----------
        result : None or str
            The value of this variable depends on what the button
            the user clicked.

        Returns
        -------
        None
        """

        if result is None or result == "Cancel":
            self.dialog.deactivate(result)
            return

        if result == "Help":
            # display help!!!
            return

        if result != "OK":
            self.dialog.deactivate(result)
            raise RuntimeError("Don't recognize dialog result '{}'".format(result))

        self.dialog.deactivate(result)

    def update_flowchart(self, tk_flowchart=None, flowchart=None):
        """Update the nongraphical flowchart.

        This is only used in nodes that contain sub-flowcharts
        What to do depends on the button used to close the dialog. If
        the user closes it by clicking the 'x' of the dialog window,
        None is returned, which we take as equivalent to cancel.

        Parameters
        ----------
        tk_flowchart : seamm.tk_Flowchart
            A graphical representation of the SEAMM Flowchart

        flowchart : seamm.Flowchart
            A non-graphical representation of the SEAMM Flowchart

        Returns
        -------
        None
        """

        super().update_flowchart(
            flowchart=self.node.subflowchart, tk_flowchart=self.tk_subflowchart
        )

    def from_flowchart(self, tk_flowchart=None, flowchart=None):
        """Recreate the graphics from the non-graphical flowchart.

        This is only used in nodes that contain sub-flowcharts.

        Parameters
        ----------
        tk_flowchart : seamm.tk_Flowchart
            A graphical representation of the SEAMM Flowchart
        flowchart : seamm.Flowchart
            A non-graphical representation of the SEAMM Flowchart

        Returns
        -------
        None
        """

        super().from_flowchart(
            flowchart=self.node.subflowchart, tk_flowchart=self.tk_subflowchart
        )

    def handle_help(self):
        """Shows the help to the user when click on help button.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        print("Help not implemented yet for DFTB+!")
