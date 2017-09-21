#!/usr/bin/env python

import gettext
from gettext import textdomain

textdomain('aduc')

import ycp
from ycp import *
ycp.widget_names()
import Wizard

from complex import Connection
from yui import Empty, HWeight, ReplacePoint, HBox, Tree, Node

from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT

class ADUC:
    def __init__(self, lp, creds):
        self.realm = lp.get('realm')
        self.lp = lp
        self.creds = creds
        try:
            self.conn = Connection(lp, creds)
            self.users = self.conn.user_group_list()
            self.computers = self.conn.computer_list()
        except Exception as e:
          syslog(LOG_EMERG, str(e))

    def Show(self):
        Wizard.SetContentsButtons(gettext.gettext('Active Directory Users and Computers'), self.__aduc_page(), self.__help(), 'Back', 'Next')
        Wizard.DisableBackButton()
        Wizard.DisableNextButton()
        UI.SetFocus(Term('id', 'aduc_tree'))

        ret = Symbol('abort')
        while True:
            ret = UI.UserInput()
            if str(ret) == 'abort' or str(ret) == 'cancel':
                break
            elif str(ret) == 'aduc_tree':
                choice = UI.QueryWidget(Term('id', 'aduc_tree'), Symbol('Value'))

        return ret

    def __help(self):
        return ''

    def __aduc_tree(self):
        return Tree('Active Directory Users and Computers', [
            Node('my.domain', True, [
                Node('Users', True),
                Node('Computers', True),
            ]),
        ], id='aduc_tree', opts=['notify'])

    def __aduc_page(self):
        return HBox([
            HWeight(1, self.__aduc_tree()),
            HWeight(2, ReplacePoint(Empty(), id='rightPane'))
        ])

