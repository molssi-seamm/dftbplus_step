# -*- coding: utf-8 -*-
"""The timing records DFTB+ runs write (seamm_exec campaign 2026-10-05)."""

from types import SimpleNamespace

from dftbplus_step.base import timing_descriptors

OUT = """\
 iSCC Total electronic   Diff electronic      SCC error
    1   -0.40871380E+01    0.00000000E+00    0.71541542E+00
    2   -0.40981105E+01   -0.10972500E-01    0.33041392E+00
    3   -0.41008345E+01   -0.27240050E-02    0.11453571E-01
SCC converged
Geometry step: 1
    1   -0.41009000E+01    0.00000000E+00    0.10000000E-01
SCC converged
--------------------------------------------------------------------------------
DFTB+ running times                          cpu [s]             wall clock [s]
--------------------------------------------------------------------------------
Total                                  =     0.12 (100.0%)      0.34 (100.0%)
"""


def test_descriptors():
    conf = SimpleNamespace(
        atoms=SimpleNamespace(atomic_numbers=[8, 1, 1]),
        charge=0,
        spin_multiplicity=1,
        periodicity=0,
    )
    d = timing_descriptors("DFTB - 3ob-3-1", OUT, conf)
    assert d["model"] == "DFTB - 3ob-3-1"
    assert d["n_atoms"] == 3 and d["n_heavy"] == 1
    assert d["scc_cycles"] == 4 and d["scc_converged"] == 2
    assert d["geometry_steps"] == 1
    assert d["cpu_seconds"] == 0.12 and d["code_seconds"] == 0.34
    assert d["terminated_normally"] is True
