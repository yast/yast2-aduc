#!/usr/bin/env python

import gettext
from gettext import textdomain

textdomain('aduc')

import ycp
from ycp import *
ycp.widget_names()
import Wizard

from yui import Empty, HWeight, ReplacePoint, HBox

class ADUC:
    def __init__(self, lp, creds):
        self.realm = lp.get('realm')
        self.lp = lp
        self.creds = creds

    def Show(self):
        Wizard.SetContentsButtons(gettext.gettext('Active Directory Users and Computers'), self.__aduc_page(), self.__help(), 'Back', 'Next')
        Wizard.DisableBackButton()
        Wizard.DisableNextButton()
        #UI.SetFocus(Term('id', 'aduc_tree'))

        ret = Symbol('abort')
        while True:
            ret = UI.UserInput()
            if str(ret) == 'abort' or str(ret) == 'cancel':
                break

        return ret

    def __help(self):
        return ''

    def __aduc_page(self):
        return HBox([
            HWeight(1, Empty()),
            HWeight(2, ReplacePoint(Empty(), id='rightPane'))]
            )

