#!/usr/bin/env python

from ycp import *
import gettext
from gettext import textdomain
textdomain('aduc')


import_module('Sequencer')
import_module('Wizard')
import_module('UI')


from ycp import *
import dialogs
import Aduc

gpo = None
lp = None
creds = None

def show_aduc():
    global lp, creds
    g = dialogs.ADUC(lp, creds)
    resp = g.Show()
    return resp

def GPMCSequence(in_lp, in_creds):
    global lp, creds
    lp = in_lp
    creds = in_creds
    aliases = {
        'read' : [Code(Aduc.ReadDialog), True],
        'aduc' : Code(show_aduc),
        'write' : Code(Aduc.WriteDialog)
    }

    sequence = {
        'ws_start' : 'aduc',
        'read' : {
            Symbol('abort') : Symbol('abort'),
            Symbol('next') : 'aduc'
        },
        'aduc' : {
            Symbol('abort') : Symbol('abort'),
            Symbol('next') : Symbol('next'),
        },
        'write' : {
            Symbol('abort') : Symbol('abort'),
            Symbol('next') : Symbol('next')
        }
    }

    Wizard.CreateDialog()
    Wizard.SetTitleIcon('yast-aduc')

    ret = Sequencer.Run(aliases, sequence)

    UI.CloseDialog()
    return ret

