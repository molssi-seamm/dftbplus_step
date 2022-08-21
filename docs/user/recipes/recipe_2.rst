-----------------------------------------------
Recipe 2: Band structure, DOS and PDOS in SEAMM
-----------------------------------------------

Introduction
------------
The `second recipe
<https://dftbplus-recipes.readthedocs.io/en/latest/basics/bandstruct.html>`_ on the
DFTB+ website. This covers calculating the band structure, density of states (DOS), and
partial DOS on the atoms, which helps us understand the electronic structure of any
periodic system. We will generally follow their prescription, adapting it for SEAMM. The
approach is similar:

#. Calculate and save the charges on the system using a self-consistent charge (SCC)
   calculation with a good-enough sampling of the reciprocal space (k-point
   sampling). This is done automatically in SEAMM whenever you calculate the energy or
   optimize the structure with DFTB+.
#. Then, keeping the charges fixed, calculate the band energies on a large k-point grid
   to create the DOS.
#. And again keeping the charges fixed, calculate the band energies on a path through
   the Brillouin zone made of about 100 points.

The recipe on the DFTB+ website combined the first two steps into one. The approach
taken in the SEAMM DFTB+ plug-in is perhaps a bit more general, and allows you to
calculate the DOS over a fine grid of k-points which might be overkill for the energy
and charges for larger systems. Since the DOS calculation is equal to just one iteration
of an energy calculation, this can be a considerable savings, particularly if the
initial step is a geometry optimization.

Tutorial
--------
