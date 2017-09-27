#!/usr/bin/env python

from ycp import import_module
import_module('Sequencer')
import_module('Wizard')
import_module('UI')
from ycp import *

class UISequencer:
    def __init__(self, *cli_args):
        UISequencer.cli_args = cli_args
        UISequencer.itr = 0

    @staticmethod
    def runner():
        UISequencer.funcs[UISequencer.itr](*(UISequencer.cli_args))
        UISequencer.itr += 1

    def run(self, funcs):
        UISequencer.funcs = funcs
        aliases = { 'run%d' % i : Code(UISequencer.runner) for i in range(0, len(UISequencer.funcs)) }

        sequence = { 'run%d' % i : { Symbol('abort') : Symbol('abort'), Symbol('next') : 'run%d' % (i+1) if (i+1) < len(UISequencer.funcs) else Symbol('abort') } for i in range(0, len(UISequencer.funcs)) }
        sequence['ws_start'] = 'run0'

        Wizard.CreateDialog()

        ret = Sequencer.Run(aliases, sequence)

        UI.CloseDialog()
        return ret

