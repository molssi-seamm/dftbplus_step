Recipe 1: First Calculation the DFTB+
-------------------------------------

This first recipe is a simple introduction to optimizing a structure -- water -- using
DFTB+ and examining the output. In the `recipe on the DFTB+ website
<https://dftbplus-recipes.readthedocs.io/en/latest/basics/firstcalc.html>`_ you type in
the coordinates for the atoms, use the `mio-ext` parameter set, and set up the
optimization. We will do the same, but use the `from-smiles-step` to create the water
molecules from its SMILES string:

.. figure:: images/recipe_1_flowchart.png
   :align: center
   :alt: The flowchart and From SMILES input
   
   The flowchart and input for From SMILES

The flowchart is very simple. It builds the structure from SMILES, and then runs
DFTB+. The input for the From SMILES step is shown in the picture above. The only
important parameter is **SMILES**, which is set to "O", which is the SMILES
representation for water.

If you are not familiar with SMILES, it is a convenient representation of moleculaes
particularly organic molecules. It was created by Daylight Chemical Information Systems,
which has a nice `tutorial
<https://www.daylight.com/dayhtml_tutorials/languages/smiles/index.html>`_ The EPA,
which is where the original work on SMILES was done, also has nice `introduction
<https://archive.epa.gov/med/med_archive_03/web/html/smiles.html>`_. Most databases of
molecules have SMILES, as does Wikipedia, so using SMILES is a conveninet way to create
molecules. 

The DFTB+ flowchart is also very simple:

.. figure:: images/recipe_1_parameters.png
   :align: center
   :alt: Choosing the parameters for DFTB+
   
   Choosing the parameters for DFTB+.

The DFTB+ step in SEAMM uses the newer `3ob` parameter set by default, so you need to
change to the `mio` set as shown in the dialog.

The defaults for the optimization will work fine, so there is no need to make any
changes:

The DFTB+ subflowchart is also very simple:

.. figure:: images/recipe_1_optimization.png
   :align: center
   :alt: Optimization setup for DFTB+
   
   Optimization setup for DFTB+.

Note that the original recipe uses the Conjugate Gradient driver, which is being phased
out, so we will use the default Rational Function optimizer.

When you have finished the DFTB+ subflowchart, close it and then run the calculation
using File / Run or ctrl-R (cmd-R on a Mac):

.. figure:: images/recipe_1_run.png
   :align: center
   :alt: Running the job
   
   Running the job.

Now head over to your browser and pull up the Dashboard. Find the job that you just ran,
so that you can examine the input and output files.
