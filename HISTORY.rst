=======
History
=======
2025.3.3 -- Enhancements and bug fix for periodic cell!
    * Fixed issue with periodic cells with symmetry and primitive cells that caused
      problems with e.g. charges and spins.
    * Added RMSD and displacement between initial and final structure in optimization.
    * Added to output and put key results in tables to make easier to read.
      
2025.2.7 -- Bugfix: Issue with logging and geomeTRIC
    * Logging at the INFO level made the output from geomTRIC too verbose. Changed to
      DEBUG level.
      
2025.1.21 -- Bugfix: Issue with spin-polarized calculations
    * The code had several errors to do with detecting whether the calculation was
      spin-polarized or not. This has been fixed and the detection simplified.
      
2024.12.14 -- Bugfix: Issue with initialization in subflowcharts

2024.10.20 -- Added the standard results for drivers
    * Added the standard results -- energy, gradients, and model -- that can be written
      to Results.json for drivers like Structure Step and Thermochemistry Step.
      
2024.7.30 -- Fix: the Docker build needed updating for changes in SEAMM

2024.7.29 -- Bugfix: initial version of dftbplus.ini
    * The initial version of dftbplus.ini was not generated correctly if it was
      missing. This caused a crash when running DFTB+.

2024.4.24 -- Finalized support for Docker containers
    * Fixed issues and tested running in containers.
    * Add CI to make a Docker image for DFTB+
    * Fixed issue with changes in input for DFTB+: CalculateGradients has become
      PrintGradients it seems.
      
2024.1.18 -- Support for running in containers and writing input only.
    * Added new property: scaled dipole.
    * Added option to write the input file and not run DFTB+

2023.11.10 -- Standard structure handling and cleaned up output
    * Switched to standard structure handling and naming, giving consistent options
      across SEAMM.
    * Corrected issues with the model name in the properties.
    * Generally cleaned up the output, mainly indentation.
      
2023.11.8 -- Bugfix: Fermi level being an array caused problems
    * The Fermi level in DFTB+ is a vector with 1 or 2 elements, depending whether the
      calculation is spin-polarized. DFTB+ can handle different Fermi levels, but it is
      not clear how useful this is, so for the time being not allowing such calculations
      and treating the Fermi level as a scalar.
      
2023.11.7 -- Added structure to orbital and density plots
    * The Dashboard expects 'structure.sdf' in order to display the structure with the
      orbital or density plots from CUBE files.

2023.3.5 -- Fixed issues with bandstructure and DOS
    * The bandstructure and DOS substeps updated to work with changes in the underlying
      classes. This had been missed earlier.
      
2023.2.17.2 -- Fixed bug with xTB parameters
    * xTB runs have a blank line in results.tag which caused a crash.

2023.2.17.1 -- Fixed Linux bug with thread limit

2023.2.17 -- Limiting number of threads
    * By default DFTB+ can try to use all the cores on a larger machine, which can be
      inneficient for smaller systems. This changes limits DFTB+ to 1 core per 500
      atoms, which seems a reasonable start. This will need more work in the future.

2023.2.15 -- Documentation and bug fixes
    * Restructured the documentation and applied the new theme.
    * Fixed crash with the plots for potentials that lack the need info for the
      plots. Silently ignore the plots.
    * Added standard properties.

2022.10.20 -- Added handling of properties in the database.

2022.9.18 -- Added spin parameters for 3ob dataset
    * Added the spin parameters for the 3ob parameter set from Prof. Elstner. These were
      provide by Kewei Zhao on the DFTB+ mailing list, 2022-9-8.

2022.9.15 -- Bugfix: plots for periodic systems
    * fixed error with density and orbital plots for periodic systems.

2022.9.9 -- Density and orbital plots
    * Added plots for the density, spin density, and orbitals.

2022.8.22 -- More documentation.
    * Added the DFTB+ recipe #2

2022.8.21 -- Fixed issue using Python 3.10

2022.8.21 -- Documentation update
    * Added initial recipes (tutorials)

2022.8.19 -- Improved information about the energy
    * Corrected total energy to be that of the conventional cell
    * Added how many primitive cells make up the conventional cell
    * Added energy per empirical formula unit
    * Added these energies and counts to the output data, if selected.
      
2022.8.17 -- Finally fully added DOS and band structure
    * Now handle magnetic systems
    * Fixed issues with symmetry changing during optimization cause crashes
    * Fixed incorrect printing of atom charges and spins
    * Enhance the ChooseParameters step to support using variables for the parameter
      dataset and subset
      
2022.7.24 -- Support for magnetism
    * Fixed and improved handling of spin in periodic systems
    * By default now use a previous charge file or charges and spins on atoms, if
      available, as starting guess.
    * DOS and bandstructure extended to spin-polarized systems, and a combined graph
      added for DOS & bandstructure.
      
2022.7.20.1 -- Correction to DOS and band structure
    The DOS and band structure needed to be shifted to place the Fermi energy at zero.
    
2022.7.20 -- Bug fix for band structure
    Band structure sometimes had a fatal error due to charges on the structure as well
    as in the charge file from a previous run.
    
2022.5.23 -- Bug fixes
    * Spin polarized calculations & more output
    * Added control over using primitive or actual cell.
    * Bug fixes: handling atoms with no charge, and printing k-mesh

2022.3.16 -- Added control over using primitive or full cell
    While usually it is best to use the full symmetry and primitive cell, for some
    calculations where cancelation of error is import, e.g. defect energies, it is
    important to use the same cell in all the calculations. This feature allows for
    this.

2022.3.14 -- Handling spin-polarization and improved output of charges and spin

2022.2.25 -- Added xTB parameters

2022.2.8 -- Added DOS and band structure
    * Added handling of space group symmetry.
    * Automatically use the primitive cell when it is different from the conventional cell.
    * Calculate and graph the DOS when running the energy or optimization.
    * Added a band structure sub-step to calculate and graph the band structure. This is
      an initial, working version, but needs considerable enhancement.
    * To accomplish the above, restructured the code significantly and moved the actual
      execution of DFTB+ to the appropriate sub-steps. This is need to support e.g. band
      structure which requires two sequential calculations, the first to calculate the
      charge density and the second to get the band structure from the fixed charge
      density.

2022.1.18 -- Updated for DFTB+ 21.2
    * Updated to the latest version of DFTB+ (21.2), which made large changes in how
      optimizations are handled. 
    * Updated the structure handling to give the standard options for where to put the
      modified configuration and how to name it. 
    * Added enhancement to calculate the electronic energy of formation, and added the
      reference energies to the metadata for the main 3ob and mio datasets. 

2021.11.26 -- Periodic calculations
    Added handling of the reciprocal space k-mesh for periodic calculations.

2021.10.13 -- Minor fixes and format issues.
    Also updated for Python 3.8 and 3.9
    
2021.6.5 -- Added installation of Slater-Koster files.

2021.6.4 -- Updated for new command-line argument handling.
    Corrected the default path for the Slater-Koster functions.

2021.5.21 -- Added installer for DFTB+ background code
    Added a plug-in specific installer that installs DFTB+ in the seamm-dftbplus
    environment if needed, and sets up the configuration file entries needed.
    
2021.2.10 (10 February 2021)
----------------------------

* Updated the README file to give a better description.
* Updated the short description in setup.py to work with the new installer.
* Added keywords for better searchability.

2021.2.3 (3 February 2021)
--------------------------

* Internal Release

  - Compatible with the enhance version of MolSystem classes.

2020.12.2 (2 December 2020)
---------------------------

* First release  of a working version on PyPI.
