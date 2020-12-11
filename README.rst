==========
DFTB+ Step
==========

| .. image:: https://img.shields.io/github/issues-pr-raw/molssi-seamm/dftbplus_step
     :target: https://github.com/molssi-seamm/dftbplus_step/pulls
     :alt: GitHub pull requests
  .. image:: https://github.com/molssi-seamm/dftbplus_step/workflows/CI/badge.svg
     :target: https://github.com/molssi-seamm/dftbplus_step/actions?query=workflow%3ACI
     :alt: CI status
  .. image:: https://readthedocs.org/projects/dftbplus-step/badge/?version=latest
     :target: https://dftbplus-step.readthedocs.io/en/latest/?badge=latest
     :alt: Documentation Status
  .. image:: https://codecov.io/gh/molssi-seamm/dftbplus_step/branch/master/graph/badge.svg
     :target: https://codecov.io/gh/molssi-seamm/dftbplus_step
     :alt: Code coverage
  .. image:: https://img.shields.io/lgtm/grade/python/g/molssi-seamm/dftbplus_step.svg?logo=lgtm&logoWidth=18
     :target: https://lgtm.com/projects/g/molssi-seamm/dftbplus_step/context:python
     :alt: Code Quality
  .. image:: https://pyup.io/repos/github/molssi-seamm/dftbplus_step/shield.svg
     :target: https://pyup.io/repos/github/molssi-seamm/dftbplus_step/
     :alt: Updates for requirements
| .. image:: https://github.com/molssi-seamm/dftbplus_step/workflows/Release/badge.svg
     :target: https://github.com/molssi-seamm/dftbplus_step/actions?query=workflow%3ARelease
     :alt: CI status for releases
  .. image:: https://img.shields.io/pypi/v/dftbplus_step.svg
     :target: https://pypi.python.org/pypi/dftbplus_step
     :alt: Release version

A plug-in for DFTB+ in a SEAMM flowchart

* Free software: BSD-3-Clause
* Developer Documentation: https://dftbplus-step.readthedocs.io
* User Documentation: https://molssi-seamm.github.io


Features
--------

This plug-in to the `SEAMM environment`_ provides an interface to the
`DFTB+`_ quantum mechanical simulation software package. DFTB+ lets
you do quantum mechanical simulations similar to density functional
theory (DFT)  for molecules, crystals and materials. The simulations
are carried out in an approximate way using the **D**\ ensity
**F**\ unctional based **T**\ ight **B**\ inding method (DFTB), which
is typically about two orders of magnitude faster than traditonal DFT.

This plug-in currently supports

* The selection and use of any of the parameter sets found at the
  `DFTB website`_.
* Single-point energy calculations
* Structural (geometry) optimization

At the moment the plug-in only handle molecular (non-periodic)
systems. Periodic systems will be added in an upcoming release.

.. _SEAMM environment: https://github.com/molssi-seamm
.. _DFTB+: https://dftbplus.org
.. _DFTB website: https://dftb.org

Credits
---------

This package was created with Cookiecutter_ and the `molssi-seamm/cookiecutter-seamm-plugin`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`molssi-seamm/cookiecutter-seamm-plugin`: https://github.com/molssi-seamm/cookiecutter-seamm-plugin

