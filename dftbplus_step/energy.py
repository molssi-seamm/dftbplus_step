# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import csv
import gzip

try:
    import importlib.metadata as implib
except Exception:
    import importlib_metadata as implib
import json
import logging
from pathlib import Path
import shutil
import subprocess
import textwrap

import hsd
from tabulate import tabulate

import dftbplus_step
import seamm
import seamm.data
from seamm_util import Q_, units_class, element_data
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

from .base import DftbBase


logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("DFTB+")


class Energy(DftbBase):
    def __init__(
        self, flowchart=None, title="Single-Point Energy", extension=None, logger=logger
    ):
        """Initialize the node"""

        logger.debug("Creating Energy {}".format(self))

        super().__init__(flowchart=flowchart, title=title, extension=extension)

        self._calculation = "energy"
        self._model = None
        self._metadata = dftbplus_step.metadata
        self.parameters = dftbplus_step.EnergyParameters()

        self.description = ["Energy of DFTB+"]

    @property
    def header(self):
        """A printable header for this section of output"""
        return "Step {}: {}".format(".".join(str(e) for e in self._id), self.title)

    @property
    def version(self):
        """The semantic version of this module."""
        return dftbplus_step.__version__

    @property
    def git_revision(self):
        """The git version of this module."""
        return dftbplus_step.__git_revision__

    def description_text(self, P=None):
        """Prepare information about what this node will do"""
        if P is None:
            P = self.parameters.values_to_dict()

        if P["SCC"] == "No" and not self.is_expr(P["SCC"]):
            text = "Doing a non-self-consistent calculation."
        else:
            text = (
                "Doing a self-consistent charge calculation with a convergence"
                f" criterion of {P['SCCTolerance']} charge units and a limit "
                f"of {P['MaxSCCIterations']} iterations."
            )
            third_order = P["ThirdOrder"]
            if self.is_expr(third_order):
                text += (
                    " Whether to do a 3rd order calculation and if so, "
                    f"what type, will be determined by {third_order}."
                )
            elif third_order == "Default for parameters":
                text += (
                    " Whether to do a 3rd order calculation and if so, "
                    "what type, will be determined by the parameter set used."
                )
            elif third_order == "Partial":
                text += (
                    " The older style 3rd order calculation with just on-site "
                    "elements will be used. This should be used only for "
                    "compatibility."
                )
            elif third_order == "Full":
                text += " This is a full 3rd order calculation."

            hcorrection = P["HCorrection"]
            if self.is_expr(hcorrection):
                text += (
                    " Whether to correct the hydrogen interactions will be "
                    f"determined by {hcorrection}."
                )
            elif hcorrection == "Default for parameters":
                text += (
                    " Whether and how to correct interactions with hydrogen "
                    "atoms will be determined by the parameter set used."
                )
            elif hcorrection == "Damping":
                text += (
                    " Interactions with hydrogen atoms will be corrected "
                    "using damping with an exponent of "
                    f"{P['Damping Exponent']}."
                )
            elif hcorrection == "DFTB3-D3H5":
                text += (
                    " Interactions with hydrogen atoms will be corrected "
                    "using the D3H5 method."
                )

        if P["SpinPolarisation"] == "none":
            text += (
                " Closed shell systems will be spin-restricted. Open-shell will be "
                "spin-unrestricted. "
            )
        elif P["SpinPolarisation"] == "colinear":
            text += (
                " The system will be handled with spin, starting either from spins on "
                "the structure, if present, or the spin-multiplicity of the system."
            )
        elif P["SpinPolarisation"] == "noncolinear":
            text += (
                " The system will be handled using noncolinear spins, starting "
                "from spins on the atoms in the structure."
            )
        if P["RelaxTotalSpin"] == "no":
            text += " Any spins will be fixed at the initial value."
        else:
            text += " Any spins will be optimized."

        kmethod = P["k-grid method"]
        if kmethod == "grid spacing":
            text += (
                " For periodic system a Monkhorst-Pack grid with a spacing of "
                f"{P['k-spacing']} will be used."
            )
        elif kmethod == "supercell folding":
            text += (
                f" For periodic systems a {P['na']} x{P['nb']} x{P['nc']} "
                "Monkhorst-Pack grid will be used."
            )

        # Plotting
        plots = []
        if P["total density"]:
            plots.append("total density")
        if P["difference density"]:
            plots.append("difference density")
        if P["total spin density"]:
            plots.append("spin density")
        if P["orbitals"]:
            if len(plots) > 0:
                text += f"\nThe {', '.join(plots)} and orbitals "
                text += f"{P['selected orbitals']} will be plotted."
            else:
                text += f"\nThe orbitals {P['selected orbitals']} will be plotted."

        return self.header + "\n" + __(text, indent=4 * " ").__str__()

    def get_input(self):
        """Get the input for an initialization calculation for DFTB+"""

        # Create the directory
        directory = Path(self.directory)
        directory.mkdir(parents=True, exist_ok=True)

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Need the configuration for charges, spins, etc.
        system, configuration = self.get_system_configuration(None)
        periodicity = configuration.periodicity
        atoms = configuration.atoms

        # Have to fix formatting for printing...
        PP = dict(P)
        for key in PP:
            if isinstance(PP[key], units_class):
                PP[key] = "{:~P}".format(PP[key])

        # Set up the description.
        self.description = []
        self.description.append(__(self.description_text(PP), **PP, indent=self.indent))

        # Determine the input and as we do so, replace any default values
        # in PP so that we print what is actually done

        dataset = self.parent._dataset
        parameter_set = self.parent._hamiltonian
        model, parameter_set_name = parameter_set.split(" - ", 1)

        if model == "DFTB":
            if "defaults" in dataset:
                all_defaults = {**dataset["defaults"]}
            else:
                all_defaults = {}
            if self.parent._subset is not None:
                subset = self.parent._subset
                if "defaults" in subset:
                    all_defaults.update(subset["defaults"])

            if "Energy" in all_defaults and "SCC" in all_defaults["Energy"]:
                defaults = all_defaults["Energy"]["SCC"]
            else:
                defaults = {}

            # template
            result = {
                "Analysis": {
                    "CalculateForces": "Yes",
                },
                "Hamiltonian": {"DFTB": {}},
            }
            hamiltonian = result["Hamiltonian"]["DFTB"]

            if P["SCC"] == "Yes":
                hamiltonian["SCC"] = "Yes"
                hamiltonian["SCCTolerance"] = P["SCCTolerance"]
                hamiltonian["MaxSCCIterations"] = P["MaxSCCIterations"]
                hamiltonian["ShellResolvedSCC"] = P["ShellResolvedSCC"].capitalize()

                have_charges = "charge" in atoms
                if have_charges:
                    for tmp in atoms["charge"]:
                        if tmp is None:
                            have_charges = False
                            break
                initial_charges = P["initial charges"]
                if initial_charges == "default":
                    # Use charge file from previous step or charges on atoms
                    if self.get_previous_charges(missing_ok=True) is not None:
                        hamiltonian["ReadInitialCharges"] = "Yes"
                    elif have_charges:
                        if periodicity == 0:
                            charges = [*atoms["charge"]]
                        else:
                            charges = [
                                atoms["charge"][i] for i in self.mapping_from_primitive
                            ]
                        # Ensure sums exactly to charge
                        delta = (configuration.charge - sum(charges)) / len(charges)
                        hamiltonian["InitialCharges"] = {
                            "AllAtomCharges": "{"
                            + f"{', '.join(str(c + delta) for c in charges)}"
                            + "}"
                        }
                elif initial_charges == "from previous step":
                    if self.get_previous_charges():
                        hamiltonian["ReadInitialCharges"] = "Yes"
                elif initial_charges == "from structure":
                    if have_charges:
                        if periodicity == 0:
                            charges = [*atoms["charge"]]
                        else:
                            charges = [
                                atoms["charge"][i] for i in self.mapping_from_primitive
                            ]
                        # Ensure sums exactly to charge
                        delta = (configuration.charge - sum(charges)) / len(charges)
                        hamiltonian["InitialCharges"] = {
                            "AllAtomCharges": "{"
                            + f"{', '.join(str(c + delta) for c in charges)}"
                            + "}"
                        }

                third_order = P["ThirdOrder"]
                if third_order == "Default for parameters":
                    if "ThirdOrder" in defaults:
                        third_order = defaults["ThirdOrder"]
                        PP["ThirdOrder"] = defaults["ThirdOrder"]
                    else:
                        third_order = "No"
                        PP["ThirdOrder"] = "No"
                if third_order == "Full":
                    hamiltonian["ThirdOrderFull"] = "Yes"
                elif third_order == "Partial":
                    hamiltonian["ThirdOrder"] = "Yes"
                elif third_order == "No":
                    hamiltonian["ThirdOrder"] = "No"
                else:
                    raise RuntimeError(f"Don't recognize ThirdOrder = '{third_order}'")

                hcorrection = P["HCorrection"]
                if hcorrection == "Default for parameters":
                    if "HCorrection" in defaults:
                        hcorrection = defaults["HCorrection"]["value"]
                        hamiltonian["HCorrection"] = {hcorrection: {}}
                        block = hamiltonian["HCorrection"][hcorrection]
                        PP["HCorrection"] = hcorrection
                        if hcorrection == "Damping":
                            if "Damping Exponent" in defaults["HCorrection"]:
                                damping = defaults["HCorrection"]["Damping Exponent"]
                                PP["Damping Exponent"] = damping
                            else:
                                damping = P["Damping Exponent"]
                            block["Exponent"] = damping
                    else:
                        hamiltonian["HCorrection"] = "None {}"
                        PP["HCorrection"] = "None {}"
                else:
                    hamiltonian["HCorrection"] = hcorrection
                    if hcorrection == "Damping":
                        if (
                            "HCorrection" in defaults
                            and "Damping Exponent" in defaults["HCorrection"]
                        ):
                            damping = defaults["HCorrection"]["Damping Exponent"]
                            PP["Damping Exponent"] = damping
                        else:
                            damping = P["Damping Exponent"]
                        hamiltonian["Damping Exponent"] = damping
        elif model == "xTB":
            result = {
                "Analysis": {
                    "CalculateForces": "Yes",
                },
                "Hamiltonian": {"xTB": {}},
            }
            hamiltonian = result["Hamiltonian"]["xTB"]
            hamiltonian["SCC"] = "Yes"
            hamiltonian["SCCTolerance"] = P["SCCTolerance"]
            hamiltonian["MaxSCCIterations"] = P["MaxSCCIterations"]

        # Handle charge and spin
        hamiltonian["Charge"] = configuration.charge
        multiplicity = configuration.spin_multiplicity

        have_spins = "spin" in atoms
        if have_spins:
            for tmp in atoms["spin"]:
                if tmp is None:
                    have_spins = False
                    break

        if P["SpinPolarisation"] == "none":
            hamiltonian["SpinPolarisation"] = {}
        elif (
            periodicity == 0
            and multiplicity == 1
            and P["SpinPolarisation"] == "from system"
        ):
            hamiltonian["SpinPolarisation"] = {}
        elif (
            periodicity != 0
            and P["SpinPolarisation"] == "from system"
            and multiplicity == 1
            and not have_spins
        ):
            hamiltonian["SpinPolarisation"] = {}
        else:
            noncollinear = P["SpinPolarisation"] == "noncollinear"

            H = hamiltonian["SpinPolarisation"] = {}
            if noncollinear:
                section = H["NonCollinear"] = {}
            else:
                section = H["Collinear"] = {}
                reading_charge_file = (
                    "ReadInitialCharges" in hamiltonian
                    and hamiltonian["ReadInitialCharges"] == "Yes"
                )
                if not reading_charge_file:
                    if have_spins:
                        if periodicity == 0:
                            spins = atoms["spin"]
                        else:
                            spins = [
                                atoms["spin"][i] for i in self.mapping_from_primitive
                            ]
                        section["InitialSpins"] = {
                            "AllAtomSpins": "{"
                            + f"{', '.join(str(c) for c in spins)}"
                            + "}"
                        }
                    else:
                        section["UnpairedElectrons"] = multiplicity - 1

            section["RelaxTotalSpin"] = P["RelaxTotalSpin"].capitalize()

            # Get the spin constants
            package = self.__module__.split(".")[0]
            files = [
                p for p in implib.files(package) if p.name == "spin-constants.json"
            ]
            if len(files) != 1:
                raise RuntimeError(
                    "Can't find spin-constants.json file. Check the installation!"
                )
            data = files[0].read_text()
            spin_constant_data = json.loads(data)

            # First check if we have shell resolved constants or not
            spin_constants = hamiltonian["SpinConstants"] = {}
            symbols = sorted([*set(atoms.symbols)])
            dataset_name = self.parent._hamiltonian
            # e.g. "DFTB - mio"
            key = dataset_name.split(" - ")[1]
            if key in spin_constant_data:
                constants = spin_constant_data[key]
            else:
                constants = spin_constant_data["GGA"]

            # Bit of a kludgy test. If not shell-resolved there is one constant
            # per shell, i.e. 1, 2 or 3 for s, p, d. If resolved, there are 1, 4, 9.
            shell_resolved = False
            for symbol in symbols:
                if len(constants[symbol]) > 3:
                    shell_resolved = True
                    break

            if shell_resolved:
                if P["ShellResolvedSpin"] == "yes":
                    spin_constants["ShellResolvedSpin"] = "Yes"
                else:
                    spin_constants["ShellResolvedSpin"] = "No"
                    shell_resolved = False
            else:
                spin_constants["ShellResolvedSpin"] = "No"

            # And add them and the control parameters
            if shell_resolved:
                for symbol in symbols:
                    spin_constants[symbol] = (
                        "{" + " ".join([str(c) for c in constants[symbol]]) + "}"
                    )
            else:
                for symbol in symbols:
                    shells = element_data[symbol]["electron configuration"]
                    shell = shells.split()[-1]
                    tmp = constants[symbol]
                    if "s" in shell:
                        spin_constants[symbol] = str(tmp[0])
                    elif "p" in shell:
                        if len(tmp) == 4:
                            spin_constants[symbol] = str(tmp[3])
                        elif len(tmp) == 9:
                            spin_constants[symbol] = str(tmp[4])
                        else:
                            raise RuntimeError(
                                f"Error in spin constants for {symbol}: {tmp}"
                            )
                    elif "d" in shell:
                        if len(tmp) == 9:
                            spin_constants[symbol] = str(tmp[8])
                        else:
                            raise RuntimeError(
                                f"Error in spin constants for {symbol}: {tmp}"
                            )
                    else:
                        raise RuntimeError(f"Can't handle spin constants for {symbol}")

        # Integration grid in reciprocal space
        if configuration.periodicity == 3:
            kmethod = P["k-grid method"]
            if kmethod == "grid spacing":
                lengths = configuration.cell.reciprocal_lengths()
                spacing = P["k-spacing"].to("1/Å").magnitude
                na = round(lengths[0] / spacing)
                nb = round(lengths[0] / spacing)
                nc = round(lengths[0] / spacing)
                na = na if na > 0 else 1
                nb = nb if nb > 0 else 1
                nc = nc if nc > 0 else 1
            elif kmethod == "supercell folding":
                na = P["na"]
                nb = P["nb"]
                nc = P["nc"]
            oa = 0.0 if na % 2 == 1 else 0.5
            ob = 0.0 if nb % 2 == 1 else 0.5
            oc = 0.0 if nc % 2 == 1 else 0.5
            kmesh = (
                "SupercellFolding {\n"
                f"            {na} 0 0\n"
                f"            0 {nb} 0\n"
                f"            0 0 {nc}\n"
                f"            {oa} {ob} {oc}\n"
                "        }"
            )
            hamiltonian["KPointsAndWeights"] = kmesh
            self.description.append(
                __(
                    f"The mesh for the Brillouin zone integration is {na} x {nb} x {nc}"
                    f" with offsets of {oa}, {ob}, and {oc}",
                    indent=self.indent + 4 * " ",
                )
            )

        # If reading the charge file, use a text file
        if (
            "ReadInitialCharges" in hamiltonian
            and hamiltonian["ReadInitialCharges"] == "Yes"
        ):
            if "Options" not in result:
                result["Options"] = {
                    "ReadChargesAsText": "Yes",
                    "SkipChargeTest": "Yes",
                }
            else:
                result["Options"]["ReadChargesAsText"] = "Yes"
                result["Options"]["SkipChargeTest"] = "Yes"

        # And are we plotting the density or orbitals?
        plotting = False
        for key in (
            "total density",
            "total spin density",
            "difference density",
            "orbitals",
        ):
            if P[key]:
                plotting = True
                break

        if plotting:
            if "Options" not in result:
                result["Options"] = {
                    "WriteDetailedXml": "Yes",
                }
            else:
                result["Options"]["WriteDetailedXml"] = "Yes"
            if "Analysis" not in result:
                result["Analysis"] = {
                    "WriteEigenvectors": "Yes",
                }
            else:
                result["Analysis"]["WriteEigenvectors"] = "Yes"
        return result

    def analyze(self, indent="", data={}, out=[]):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        options = self.parent.options

        # Get the configuration and basic information
        system, configuration = self.get_system_configuration(None)

        symbols = configuration.atoms.symbols
        atoms = configuration.atoms
        periodicity = configuration.periodicity

        # Read the detailed output file to get the number of iterations
        directory = Path(self.directory)
        path = directory / "detailed.out"
        lines = iter(path.read_text().splitlines())
        data["scc error"] = None
        for line in lines:
            if "SCC error" in line:
                tmp = next(lines).split()
                data["scc error"] = float(tmp[3])

        # Print the key results
        if periodicity == 3:
            # May have primitive cell....
            Zcell = len(symbols) / len(self.mapping_from_primitive)
            data["#_primitive_cells"] = Zcell
            if Zcell != 1:
                text = (
                    "The total energy of the primitive cell is {total_energy:.6f} E_h."
                    f" There are {Zcell:.0f} primitive cells in the conventional cell."
                )
            else:
                text = "The total energy of the unit cell is {total_energy:.6f} E_h."
        else:
            Zcell = 1
            data["#_primitive_cells"] = None
            text = "The total energy is {total_energy:.6f} E_h."
        if data["scc error"] is not None:
            text += " The charges converged to {scc error:.6f}."

        # Handle the chemical and empirical formulas
        formula, empirical, Z = configuration.formula
        data["formula"] = formula
        data["empirical_formula"] = empirical
        data["Z"] = Z
        data["energy_per_formula_unit"] = data["total_energy"] * Zcell / Z

        # Calculate the energy of formation
        if self.parent._reference_energy is not None:
            dE = data["total_energy"] - self.parent._reference_energy
            dE = Q_(dE, "hartree").to("kJ/mol").magnitude
            if periodicity == 3:
                dE = dE * Zcell
                text += (
                    f" The calculated formation energy of the cell ({formula}) is "
                    f"{dE:.1f} kJ/mol."
                )
                data["energy of formation"] = dE
            else:
                text += (
                    f" The calculated formation energy is {dE:.1f} kJ/mol for formula "
                    f"{formula}."
                )
                data["energy of formation"] = dE
            if Z != 1:
                text += (
                    f" For the empirical formula {empirical} it is {dE / Z:.1f} kJ/mol."
                )
        else:
            text += " Could not calculate the formation energy because some reference "
            text += "energies are missing."
            data["energy of formation"] = None

        # Prepare the DOS graph(s)
        if "fermi_level" in data:
            Efermi = list(Q_(data["fermi_level"], "hartree").to("eV").magnitude)
        else:
            Efermi = [0.0]
        wd = Path(self.directory)
        self.dos(wd / "band.out", Efermi=Efermi)

        text_lines = []
        # Get charges and spins, etc.
        if "gross_atomic_charges" in data:
            # Add to atoms (in coordinate table)
            if "charge" not in atoms:
                atoms.add_attribute(
                    "charge", coltype="float", configuration_dependent=True
                )
            charges = data["gross_atomic_charges"]
            if periodicity == 0:
                atoms["charge"][0:] = charges
            else:
                tmp = [charges[i] for i in self.mapping_to_primitive]
                atoms["charge"][0:] = tmp

            # Print the charges and dump to a csv file
            table = {
                "Atom": [],
                "Element": [],
                "Charge": [],
            }
            with open(directory / "atom_properties.csv", "w", newline="") as fd:
                writer = csv.writer(fd)
                if "gross_atomic_spins" in data:
                    header = "        Atomic charges and spins"
                    table["Spin"] = []
                    writer.writerow(["Atom", "Element", "Charge", "Spin"])
                    for atom, symbol, q, s in zip(
                        range(1, len(symbols) + 1),
                        symbols,
                        data["gross_atomic_charges"],
                        data["gross_atomic_spins"][0],
                    ):
                        q = f"{q:.3f}"
                        s = f"{s:.3f}"

                        writer.writerow([atom, symbol, q, s])

                        table["Atom"].append(atom)
                        table["Element"].append(symbol)
                        table["Charge"].append(q)
                        table["Spin"].append(s)
                else:
                    header = "        Atomic charges"
                    writer.writerow(["Atom", "Element", "Charge"])
                    for atom, symbol, q in zip(
                        range(1, len(symbols) + 1),
                        symbols,
                        data["gross_atomic_charges"],
                    ):
                        q = f"{q:.2f}"
                        writer.writerow([atom, symbol, q])

                        table["Atom"].append(atom)
                        table["Element"].append(symbol)
                        table["Charge"].append(q)
            if len(symbols) <= int(options["max_atoms_to_print"]):
                text_lines.append(header)
                text_lines.append(
                    tabulate(
                        table,
                        headers="keys",
                        tablefmt="psql",
                        colalign=("center", "center"),
                    )
                )
        if "gross_atomic_spins" in data:
            # Add to atoms (in coordinate table)
            if "spin" not in atoms:
                atoms.add_attribute(
                    "spin", coltype="float", configuration_dependent=True
                )
            spins = data["gross_atomic_spins"][0]
            if periodicity == 0:
                atoms["spin"][0:] = spins
            else:
                tmp = [spins[i] for i in self.mapping_to_primitive]
                atoms["spin"][0:] = tmp

        # And requested plots of density, orbitals, etc.
        if "element data" in self.parent._dataset:
            try:
                text += self.make_plots(data)
            except Exception as e:
                text += f"There was an error making the plots: {str(e)}"
        else:
            text += f"Orbital plots not supported for {self.parent._hamiltonian}"

        text = str(__(text, **data, indent=self.indent + 4 * " "))
        text += "\n\n"
        text += textwrap.indent("\n".join(text_lines), self.indent + 7 * " ")

        printer.normal(text)

        # Put any requested results into variables or tables
        self.store_results(
            configuration=configuration,
            data=data,
            create_tables=self.parameters["create tables"].get(),
        )

    def make_plots(self, data):
        """Create the density and orbital plots if requested.

        Parameters
        ----------
        data : dict()
             Dictionary of results from the calculation (results.tag file)
        """
        text = "\n\n"

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Get the configuration and basic information
        system, configuration = self.get_system_configuration(None)

        periodicity = configuration.periodicity

        # Read the detailed output file to get the number of iterations
        directory = Path(self.directory)

        # Make the input
        input_data = {
            "Options": {
                "TotalChargeDensity": P["total density"],
                "TotalChargeDifference": P["difference density"],
                "TotalSpinPolarisation": P["total spin density"],
                "PlottedLevels": {},
                "PlottedSpins": "1:-1",
                "PlottedKPoints": {},
                "NrOfPoints": [P["nx"], P["ny"], P["nz"]],
                "NrOfCachedGrids": "-1",
                "Verbose": "Yes",
            },
            "DetailedXml": "detailed.xml",
            "EigenvecBin": "eigenvec.bin",
            "Basis": {
                "Resolution": "0.01",
            },
        }
        options = input_data["Options"]
        if periodicity == 0:
            options["PlottedRegion"] = {
                "OptimalCuboid": {},
            }
        else:
            options["PlottedRegion"] = {
                "UnitCell": {},
            }
            options["FillBoxWithAtoms"] = True

        # Add the wavefunction info for the elements
        symbols = configuration.atoms.symbols

        # The information about the dataset
        dataset = self.parent._dataset
        subset = self.parent._subset
        if subset is not None:
            subset_data = subset["element data"]
        element_data = dataset["element data"]

        basis = input_data["Basis"]
        missing = []
        for element in symbols:
            if (
                subset is not None
                and element in subset_data
                and "wfc" in subset_data[element]
            ):
                basis[element] = subset_data[element]["wfc"]
            elif "wfc" in element_data[element]:
                basis[element] = element_data[element]["wfc"]
            else:
                missing.append(element)

        if len(missing) > 0:
            txt = "', '".join(missing)
            return (
                "Cannot plot the density and orbitals because the basis set "
                "information for elements '{txt}' is not available."
            )

        if P["orbitals"] and not (
            periodicity != 0
            and (P["selected k-points"] == "none" or P["selected k-points"] == "")
        ):
            options["ChargeDensity"] = "No"
            options["RealComponent"] = "Yes"

            # And the info about the orbitals. Find the level of the HOMO.
            # band.out looks like this:
            #  KPT            1  SPIN            1  KWEIGHT    1.0000000000000000
            #      1   -24.450  1.00000
            #      2   -11.172  1.00000
            #      3    -9.085  1.00000
            #      4    -9.085  1.00000
            #      5     9.934  0.00000
            #
            #  KPT            1  SPIN            2  KWEIGHT    1.0000000000000000
            #      1   -22.899  1.00000
            #      2    -9.992  1.00000
            #      3    -7.484  0.50000
            #      4    -7.484  0.50000
            #      5    10.324  0.00000
            homos = {}
            band_path = directory / "band.out"
            lines = band_path.read_text().splitlines()
            first = True
            homo = 0
            for line in lines:
                line = line.strip()
                if first:
                    first = False
                    tmp = line.split()
                    kpoint = int(tmp[1])
                    spin = int(tmp[3])
                    if kpoint not in homos:
                        homos[kpoint] = {}
                elif line == "":
                    first = True
                    continue
                else:
                    tmp = line.split()
                    if float(tmp[2]) > 0.1:
                        homos[kpoint][spin] = int(tmp[0])
                        homo = int(tmp[0]) if int(tmp[0]) > homo else homo
            n_orbitals = int(tmp[0])
            n_spins = len(homos[1])
            last_kpoint = kpoint

            # and work out the orbitals
            txt = P["selected orbitals"]
            if txt == "all":
                options["PlottedLevels"] = "1:-1"
            else:
                orbitals = []
                for chunk in txt.split(","):
                    chunk = chunk.strip()
                    if ":" in chunk or ".." in chunk:
                        if ":" in chunk:
                            first, last = chunk.split(":")
                        elif ".." in chunk:
                            first, last = chunk.split("..")
                        first = first.strip().upper()
                        last = last.strip().upper()

                        if first == "HOMO":
                            first = homo
                        elif first == "LUMO":
                            first = homo + 1
                        else:
                            first = int(first.removeprefix("HOMO").removeprefix("LUMO"))
                            if first < 0:
                                first = homo + first
                            else:
                                first = homo + 1 + first

                        if last == "HOMO":
                            last = homo
                        elif last == "LUMO":
                            last = homo + 1
                        else:
                            last = int(last.removeprefix("HOMO").removeprefix("LUMO"))
                            if last < 0:
                                last = homo + last
                            else:
                                last = homo + 1 + last

                        orbitals.extend(range(first, last + 1))
                    else:
                        first = chunk.strip().upper()

                        if first == "HOMO":
                            first = homo
                        elif first == "LUMO":
                            first = homo + 1
                        else:
                            first = int(first.removeprefix("HOMO").removeprefix("LUMO"))
                            if first < 0:
                                first = homo + first
                            else:
                                first = homo + 1 + first
                        orbitals.append(first)

                    # Remove orbitals out of limits
                    tmp = orbitals
                    orbitals = []
                    for x in tmp:
                        if x > 0 and x <= n_orbitals:
                            orbitals.append(x)

                    options["PlottedLevels"] = orbitals

            if periodicity != 0:
                if P["selected k-points"] == "all":
                    options["PlottedKPoints"] = "1:-1"
                else:
                    kpoints = []
                    for chunk in P["selected k-points"].split(","):
                        chunk = chunk.strip()
                        if ":" in chunk or ".." in chunk:
                            if ":" in chunk:
                                first, last = chunk.split(":")
                            elif ".." in chunk:
                                first, last = chunk.split("..")
                            first = int(first.strip())
                            last = int(last.strip())

                            if first < 1:
                                first = 1

                            if last > last_kpoint:
                                last = last_kpoint

                            kpoints.extend(range(first, last + 1))
                        else:
                            first = int(chunk.strip())
                            if first > 0 and first <= last_kpoint:
                                kpoints.append(first)
                    options["PlottedKPoints"] = kpoints

        # Write the input file.
        path = directory / "waveplot_in.hsd"
        hsd.dump(input_data, str(path))

        # And run WAVEPLOT
        cmd = str(Path(self.parent.options["dftbplus_path"]) / "waveplot")
        try:
            output = subprocess.check_output(
                cmd, shell=True, text=True, stderr=subprocess.STDOUT, cwd=directory
            )
        except subprocess.CalledProcessError as e:
            return (
                f"Calling waveplot, returncode = {e.returncode}"
                f"\n\nOutput: {e.output}"
            )

        path = directory / "waveplot.out"
        path.write_text(output)

        # Finally rename and gzip the cube files
        n_processed = 0
        paths = directory.glob("wp-*.cube")
        for path in paths:
            filename = path.stem
            if filename == "wp-abs2":
                out = directory / "Total_Density.cube.gz"
                with path.open("rb") as f_in:
                    with gzip.open(out, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                n_processed += 1
                path.unlink()
            elif filename == "wp-abs2diff":
                out = directory / "Difference_Density.cube.gz"
                with path.open("rb") as f_in:
                    with gzip.open(out, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                n_processed += 1
                path.unlink()
            elif filename == "wp-spinpol":
                out = directory / "Spin_Density.cube.gz"
                with path.open("rb") as f_in:
                    with gzip.open(out, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                n_processed += 1
                path.unlink()
            else:
                tmp = filename.split("-")
                if len(tmp) != 5:
                    text += f"  Problem handling cube file {path.name}\n"
                else:
                    spin = int(tmp[1])
                    kpoint = int(tmp[2])
                    orbital = int(tmp[3])
                    form = tmp[4]

                    # homo = homos[kpoint][spin]
                    if orbital == homo:
                        name = "HOMO"
                    elif orbital == homo + 1:
                        name = "LUMO"
                    elif orbital < homo:
                        name = f"HOMO{orbital - homo}"
                    else:
                        name = f"LUMO+{orbital - homo - 1}"
                    if n_spins > 1:
                        if spin == 1:
                            name += "↑"
                        else:
                            name += "↓"
                    if form != "real":
                        name += " chg density"

                    if periodicity != 0:
                        name = f"kpt={kpoint} " + name
                    name += ".cube.gz"

                    out = directory / name
                    with path.open("rb") as f_in:
                        with gzip.open(out, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    n_processed += 1
                    path.unlink()
        text += f"Successfully handled {n_processed} density and orbital cube files."

        return text
