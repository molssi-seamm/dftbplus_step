# -*- coding: utf-8 -*-

"""Setup DFTB+"""

import logging
from pathlib import Path

import dftbplus_step
import seamm
import seamm.data
from seamm_util import units_class
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter('DFTB+')


class Optimization(dftbplus_step.Energy):

    def __init__(self, flowchart=None, title='Optimization', extension=None):
        """Initialize the node"""

        logger.debug('Creating Optimization {}'.format(self))

        super().__init__(flowchart=flowchart, title=title, extension=extension)

        self.parameters = dftbplus_step.OptimizationParameters()

        self.description = ['Optimization of DFTB+']

    @property
    def header(self):
        """A printable header for this section of output"""
        return (
            'Step {}: {}'.format(
                '.'.join(str(e) for e in self._id), self.title
            )
        )

    @property
    def version(self):
        """The semantic version of this module.
        """
        return dftbplus_step.__version__

    @property
    def git_revision(self):
        """The git version of this module.
        """
        return dftbplus_step.__git_revision__

    def description_text(self, P=None):
        """Prepare information about what this node will do
        """
        if not P:
            P = self.parameters.values_to_dict()

        text = (
            f"Structural optimization using the {P['optimization method']} "
            f"method with a convergence criterion of {P['MaxForceComponent']}."
            f" A maximum of {P['MaxSteps']} will be used."
        )

        return self.header + '\n' + __(text, indent=4 * ' ').__str__()

    def get_input(self):
        """Get the input for an optimization calculation for DFTB+"""
        # Create the directory
        directory = Path(self.directory)
        directory.mkdir(parents=True, exist_ok=True)

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )
        # Have to fix formatting for printing...
        PP = dict(P)
        for key in PP:
            if isinstance(PP[key], units_class):
                PP[key] = '{:~P}'.format(PP[key])

        self.description = []
        self.description.append(
            __(self.description_text(PP), **PP, indent=self.indent)
        )

        # Template
        result = super().get_input()
        result['Driver'] = {}

        method = P['optimization method']
        if method == 'Steepest descents':
            block = result['Driver']['SteepestDescent'] = {}
        elif method == 'Conjugate gradients':
            block = result['Driver']['ConjugateGradient'] = {}
        elif 'gDIIS' in method:
            block = result['Driver']['gDIIS'] = {}
        elif 'LBFGS' in method:
            block = result['Driver']['LBFGS'] = {}
        elif 'FIRE' in method:
            block = result['Driver']['FIRE'] = {}
        else:
            raise RuntimeError(
                f"Don't recognize optimization method '{method}'"
            )

        max_force = P['MaxForceComponent'].to('hartree/bohr')
        block['MaxForceComponent'] = max_force.magnitude
        block['MaxSteps'] = P['MaxSteps']
        block['OutputPrefix'] = 'geom.out'

        return result

    def analyze(self, indent='', data={}, out=[]):
        """Parse the output and generating the text output and store the
        data in variables for other stages to access
        """
        # Put any requested results into variables or tables
        self.store_results(
            data=data,
            properties=dftbplus_step.properties,
            results=self.parameters['results'].value,
            create_tables=self.parameters['create tables'].get()
        )

        # Print the key results
        data['nsteps'] = 25
        text = (
            "The geometry optimization converged in {nsteps} steps to a total "
            "energy of {total_energy:.6f} Ha."
        )

        printer.normal(__(text, **data, indent=self.indent + 4 * ' '))
