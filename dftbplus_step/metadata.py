"""This file contains metadata to help describe the results of DFTB+
calculations, etc.
"""

metadata = {}

"""Properties that DFTB+ produces, depending on the type of calculation.
"""
metadata["results"] = {
    "energy": {
        "description": "electronic energy",
        "dimensionality": "scalar",
        "type": "float",
        "units": "E_h",
    },
    "gradients": {
        "description": "gradients on the atoms",
        "dimensionality": [3, "n_atoms"],
        "type": "float",
        "units": "E_h/Å",
    },
    "model": {
        "description": "The model string",
        "dimensionality": "scalar",
        "type": "string",
    },
    "total_energy": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The total energy",
        "dimensionality": "scalar",
        "property": "total energy#DFTB+#{model}",
        "type": "float",
        "units": "E_h",
    },
    "energy_per_formula_unit": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The energy per empirical formula unit",
        "dimensionality": "scalar",
        "property": "total energy per formula unit#DFTB+#{model}",
        "type": "float",
        "units": "E_h",
    },
    "energy of formation": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The energy of formation",
        "dimensionality": "scalar",
        "property": "energy of formation#DFTB+#{model}",
        "type": "float",
        "units": "kJ/mol",
    },
    "fermi_level": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The Fermi level",
        "dimensionality": "scalar",
        "property": "Fermi level#DFTB+#{model}",
        "type": "float",
        "units": "E_h",
    },
    "RMSD": {
        "calculation": ["optimization"],
        "description": "RMSD with H removed",
        "dimensionality": "scalar",
        "type": "float",
        "units": "Å",
    },
    "displaced atom": {
        "calculation": ["optimization"],
        "description": "Atom index with largest displacement",
        "dimensionality": "scalar",
        "type": "int",
        "units": "",
    },
    "maximum displacement": {
        "calculation": ["optimization"],
        "description": "Maximum displacement of an atom",
        "dimensionality": "scalar",
        "type": "float",
        "units": "Å",
    },
    "RMSD with H": {
        "calculation": ["optimization"],
        "description": "RMSD including H atoms",
        "dimensionality": "scalar",
        "type": "float",
        "units": "Å",
    },
    "displaced atom with H": {
        "calculation": ["optimization"],
        "description": "Atom index with largest displacement, including H",
        "dimensionality": "scalar",
        "type": "int",
        "units": "",
    },
    "maximum displacement with H": {
        "calculation": ["optimization"],
        "description": "Maximum displacement of an atom, including H",
        "dimensionality": "scalar",
        "type": "float",
        "units": "Å",
    },
    "number_of_electrons": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The number of electrons",
        "dimensionality": [2],
        "type": "float",
    },
    "mermin_energy": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The Mermin energy",
        "dimensionality": "scalar",
        "type": "float",
        "units": "E_h",
    },
    "extrapolated0_energy": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The energy extrapolated to no smearing",
        "dimensionality": "scalar",
        "type": "float",
        "units": "E_h",
    },
    "forcerelated_energy": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The force-related energy",
        "dimensionality": "scalar",
        "type": "float",
        "units": "E_h",
    },
    "dipole_moments": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The dipole moments of the system",
        "dimensionality": [3, "nspins"],
        "type": "float",
    },
    "scaled_dipole": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The scaled dipole moments of the system",
        "dimensionality": [3, "nspins"],
        "type": "float",
    },
    "eigenvalues": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The eigenvalues",
        "dimensionality": ["norbitals"],
        "type": "float",
        "units": "E_h",
    },
    "filling": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The orbital occupancy",
        "dimensionality": ["norbitals"],
        "type": "float",
    },
    "orbital_charges": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The orbital charges",
        "dimensionality": ["natoms", "natoms"],
        "type": "float",
    },
    "gross_atomic_charges": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The charges on the atoms",
        "dimensionality": ["natoms"],
        "type": "float",
    },
    "gross_atomic_spins": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The spins on the atoms",
        "dimensionality": ["natoms"],
        "type": "float",
    },
    "atomic_dipole_moment": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The dipole moments of the atoms",
        "dimensionality": [3, "natoms"],
        "type": "float",
    },
    "forces": {
        "calculation": ["energy", "optimization"],
        "description": "The forces on the atoms",
        "dimensionality": [3, "natoms"],
        "type": "float",
        "units": "E_h/bohr",
    },
    "stress": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The stress",
        "dimensionality": [3, 3],
        "type": "float",
        "units": "Å^3",
    },
    "#_primitive_cells": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The number of primitive cells in the unit cell",
        "dimensionality": "scalar",
        "type": "integer",
    },
    "Z": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The number of empirical formula u its in the system",
        "dimensionality": "scalar",
        "type": "integer",
    },
    "formula": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The chemical formula of the system",
        "dimensionality": "scalar",
        "type": "string",
    },
    "empirical_formula": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The empirical formula of the system",
        "dimensionality": "scalar",
        "type": "string",
    },
    "cell_volume": {
        "calculation": [
            "energy",
            "optimization",
        ],
        "description": "The volume of the unit cell",
        "dimensionality": "scalar",
        "property": "unit cell volume",
        "type": "float",
        "units": "Å^3",
    },
}
