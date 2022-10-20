Welcome to the documentation for the DFTB+ plug-in
==================================================
This plug-in exposes the functionality of `DFTB+`_, which is an implementation of the
Density Functional based Tight Binding (DFTB) method, containing many extensions to the
original method. The development is supported by various groups, resulting in a code
which is probably the most versatile DFTB-implementation, with some unique features not
available in other implementations so far.

Features
--------

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

.. toctree::
   :maxdepth: 1
   :titlesonly:

   user/index
   developer/index
   authors
   history
   DFTB+ documentation <https://dftbplus.org/documentation>
   Main SEAMM documentation <https://molssi-seamm.github.io>

Documentation Versions
----------------------

.. raw:: html

   <iframe
   src="https://molssi-seamm.github.io/dftbplus_step/dev/versions.html"
   title="Documentation Versions"  style="border:none;">
   </iframe>

.. links to software
.. _DFTB+: https://dftbplus.org
   
