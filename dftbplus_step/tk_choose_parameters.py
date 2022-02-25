# -*- coding: utf-8 -*-

"""The graphical part of a DFTB+ ChooseParameters node"""

try:
    import importlib.metadata as implib
except Exception:
    import importlib_metadata as implib
import json
import logging
import tkinter as tk

import seamm
from seamm_util import element_data
import seamm_widgets as sw

logger = logging.getLogger(__name__)

atno_to_symbol = {d["atomic number"]: symbol for symbol, d in element_data.items()}


def expand_range_list(x):
    """Expand a list of integers including ranges into a list.

    Parameters
    ----------
    x : str
        A string giving shorthand for a list, like this '1,2, 10-20, 40,50'

    Returns
    -------
    [int]
        A python list of integers
    """
    result = []
    for part in x.split(","):
        if "-" in part:
            a, b = part.split("-")
            a, b = int(a), int(b)
            result.extend(range(a, b + 1))
        else:
            a = int(part)
            result.append(a)
    return result


class TkChooseParameters(seamm.TkNode):
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
        """Initialize the graphical Tk DFTB+ step for choosing Slater-Koster
        parameters.

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

        # Get the metadata for the Slater-Koster parameters
        package = self.__module__.split(".")[0]
        files = [p for p in implib.files(package) if p.name == "metadata.json"]
        if len(files) != 1:
            raise RuntimeError("Can't find Slater-Koster metadata.json file")
        data = files[0].read_text()
        self._metadata = json.loads(data)

    def right_click(self, event):
        """Probably need to add our dialog..."""

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def create_dialog(self, title="Edit DFTB+ ChooseParameters Step"):
        """Create the dialog!"""
        self.logger.debug("Creating the dialog")
        frame = super().create_dialog(title=title)

        # Create all the widgets
        P = self.node.parameters
        for key in P:
            if key not in ("results", "extra keywords", "create tables"):
                self[key] = P[key].widget(frame)

        # Show which elements are available
        available = set()
        for model, metadata in self._metadata.items():
            for dataset, data in metadata["datasets"].items():
                if "element sets" in data:
                    for element_set in data["element sets"]:
                        for element in element_set:
                            if element not in available:
                                available.add(element)
                elif "elements" in data:
                    for atno in expand_range_list(data["elements"]):
                        available.add(atno_to_symbol[atno])

        pt = self["elements"]
        elements = set(pt.elements)
        not_available = elements - available
        pt.disable(not_available)

        # Update the dialog as the user selects elements
        pt.command = self.reset_dialog

        for item in ("model", "dataset", "subset"):
            w = self[item]
            w.combobox.bind("<<ComboboxSelected>>", self.reset_dialog)
            w.combobox.bind("<Return>", self.reset_dialog)
            w.combobox.bind("<FocusOut>", self.reset_dialog)

        self.logger.debug("Finished creating the dialog")

    def reset_dialog(self, widget=None):
        frame = self["frame"]
        for slave in frame.grid_slaves():
            slave.grid_forget()

        model = self["model"].get()
        pt = self["elements"]
        ds = self["dataset"]
        ss = self["subset"]

        elements = set(pt.get())
        dataset = ds.get()
        # Catch older flowcharts with the old names.
        if "-" not in dataset:
            dataset = "DFTB - " + dataset
        subset = ss.get()

        # Find the datasets that contain all the requested elements
        possible_datasets = {}
        possible_elements = set()

        for tmp_model, metadata in self._metadata.items():
            # See if the model is restricted
            if model != "any" and tmp_model not in model:
                continue

            datasets = self._metadata[tmp_model]["datasets"]
            if tmp_model == "DFTB":
                for dset, data in datasets.items():
                    if data["parent"] is None:
                        for element_set in data["element sets"]:
                            coverage = set(element_set)
                            if elements <= coverage:
                                possible_datasets[dset] = ["none"]
                                possible_elements.update(coverage)
                    # Check with specialized datasets...
                    for sset in data["subsets"]:
                        subdata = datasets[sset]
                        for element_set in subdata["element sets"]:
                            coverage = set(element_set)
                            if elements <= coverage:
                                if dset not in possible_datasets:
                                    possible_datasets[dset] = []
                                if sset not in possible_datasets[dset]:
                                    possible_datasets[dset].append(sset)
                                possible_elements.update(coverage)
            elif tmp_model == "xTB":
                for dset, data in datasets.items():
                    coverage = set(
                        atno_to_symbol[atno]
                        for atno in expand_range_list(data["elements"])
                    )
                    if elements <= coverage:
                        possible_datasets[dset] = ["none"]
                        possible_elements.update(coverage)

        # Show which elements are available
        available = set()
        for model, metadata in self._metadata.items():
            for dset, data in metadata["datasets"].items():
                if "element sets" in data:
                    for element_set in data["element sets"]:
                        for element in element_set:
                            if element not in available:
                                available.add(element)
                elif "elements" in data:
                    for atno in expand_range_list(data["elements"]):
                        available.add(atno_to_symbol[atno])

        pt = self["elements"]
        elements = set(pt.elements)
        not_available = elements - available
        pt.disable(not_available)

        # Enable and disable the elements to reflect possible choices
        all_elements = set(pt.elements)
        pt.disable(all_elements - possible_elements)
        pt.enable(possible_elements)

        # Sort out the dataset widget
        tmp = [*possible_datasets.keys()]
        ds.combobox.config(values=tmp)
        if len(tmp) == 0:
            # No parameter set covers all the elements!
            dataset = ""
            tk.messagebox.showwarning(
                title="No Potentials Available for Elements",
                message=(
                    "There is no dataset available that covers the elements\n\t"
                    + ", ".join(elements)
                ),
            )
        else:
            if dataset not in tmp:
                dataset = tmp[0]
        ds.set(dataset)

        # and subset widget
        if dataset == "":
            ss.combobox.config(values="")
            subset = "none"
        else:
            tmp = possible_datasets[dataset]
            ss.combobox.config(values=tmp)
            if subset not in tmp:
                subset = tmp[0]
        ss.set(subset)

        # Note current elements in the dataset/subset with green labels
        pt.set_text_color("all", "black")
        if dataset != "":
            tmp_model = dataset.split(" - ", 1)[0]
            datasets = self._metadata[tmp_model]["datasets"]
            data = datasets[dataset]
            current = set()
            if subset == "none":
                if "element sets" in data:
                    for element_set in data["element sets"]:
                        current.update(element_set)
                elif "elements" in data:
                    current.update(
                        [atno_to_symbol[a] for a in expand_range_list(data["elements"])]
                    )
            else:
                subdata = datasets[subset]
                for element_set in subdata["element sets"]:
                    current.update(element_set)
            pt.set_text_color(current, "green")

        # and grid the widgets in place
        widgets = []
        row = 0
        self["elements"].grid(row=row, column=0, sticky=tk.EW)
        row += 1
        self["model"].grid(row=row, column=0, sticky=tk.EW)
        widgets.append(self["model"])
        row += 1
        self["dataset"].grid(row=row, column=0, sticky=tk.EW)
        widgets.append(self["dataset"])
        row += 1
        # only grid the subset if there are choices
        if dataset != "" and possible_datasets[dataset] != ["none"]:
            self["subset"].grid(row=row, column=0, sticky=tk.EW)
            widgets.append(self["subset"])
            row += 1

        sw.align_labels(widgets, sticky=tk.W)

        return row
