#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `dftbplus_step` package."""

import pytest  # noqa: F401
import dftbplus_step  # noqa: F401


def test_construction():
    """Just create an object and test its type."""
    result = dftbplus_step.Dftbplus()
    assert str(type(result)) == (
        "<class 'dftbplus_step.dftbplus.Dftbplus'>"  # noqa: E501
    )
