.. _user-guide:

**********
User Guide
**********

DFTB+ offers an approximate density functional theory based quantum simulation tool with
functionalities similar to _ab_ _initio_ quantum mechanical packages while being one or two
orders of magnitude faster. You can optimize the structure of molecules and solids, you
can extract one electron spectra, band structures and various other useful
quantities. Additionally, you can calculate electron transport under non-equilibrium
conditions.

For the full list of the capabilities of DFTB+, see the `detailed list of features
<https://dftbplus.org/about-dftb/features>`_ on DFTB+ website. Currently this plug-in
supports the following subset of the capabilities:

    * DFTB and xTB Hamiltonian
    * Non-scc and scc calculations for clusters and periodic systems (with arbitrary K-point sampling)
    * Spin polarized calculations with colinear :strike:`and non-colinear` spin
    * Dispersion correction (D3, D4, many-body and Tkatchenko-Scheffler)
    * 3rd order correction and other DFTB3-features
    * Ability to treat f-electrons
    * Geometry and lattice optimisation
    * Orbital resolved density of states (DOS) and band structure.

The following sections cover accessing and controlling this functionality.

   .. toctree::
      :maxdepth: 2
      :titlesonly:

      recipes/index

Index
=====

* :ref:`genindex`
