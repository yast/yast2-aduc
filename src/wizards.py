#!/usr/bin/env python
from dialogs import ADUC
from yast import Wizard, UI, Sequencer, Code, Symbol

def ADUCSequence(lp, creds):
    aliases = {
        'aduc' : [(lambda lp, creds: ADUC(lp, creds).Show()), lp, creds],
    }

    sequence = {
        'ws_start' : 'aduc',
        'aduc' : {
            Symbol('abort') : Symbol('abort'),
            Symbol('next') : Symbol('next'),
        },
    }

    Wizard.CreateDialog()
    Wizard.SetTitleIcon('yast-aduc')

    ret = Sequencer.Run(aliases, sequence)

    UI.CloseDialog()
    return ret

