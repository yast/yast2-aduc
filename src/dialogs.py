#!/usr/bin/env python

from complex import Connection
from yui import *

from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT

class Properties:
    def __init__(self, conn, obj):
        self.conn = conn
        self.obj = obj

    def Show(self):
        d = Dialog(self.__prop_diag())
        for ret in d.UserInput():
            if str(ret) == 'cancel_prop':
                break

    def __prop_diag(self):
        return MinSize(40, 40,
            VBox([
                PushButton('OK', id='ok_prop'),
                PushButton('Cancel', id='cancel_prop'),
            ])
        )

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
        d = WizardDialog('Active Directory Users and Computers', self.__aduc_page(), self.__help(), 'Back', 'Edit')
        d.DisableBackButton()
        d.SetFocus('aduc_tree')
        for ret in d.UserInput():
            if str(ret) == 'abort' or str(ret) == 'cancel':
                break
            elif str(ret) == 'aduc_tree':
                choice = d.QueryWidget('aduc_tree', 'Value')
                if choice == 'Users':
                    d.ReplaceWidget('rightPane', self.__users_tab())
                elif choice == 'Computers':
                    d.ReplaceWidget('rightPane', self.__computer_tab())
                else:
                    d.ReplaceWidget('rightPane', Empty())
            elif str(ret) == 'next':
                edit = Properties(self.conn, None)
                edit.Show()

        return ret

    def __help(self):
        return ''

    def __users_tab(self):
        items = [(user[1]['cn'][-1], user[1]['objectClass'][-1].title(), user[1]['description'][-1] if 'description' in user[1] else '') for user in self.users]
        return Table(['Name', 'Type', 'Description'], items=items, id='user_items')

    def __computer_tab(self):
        items = [(comp[1]['cn'][-1], comp[1]['objectClass'][-1].title(), comp[1]['description'][-1] if 'description' in comp[1] else '') for comp in self.computers]
        return Table(['Name', 'Type', 'Description'], items=items, id='comp_items')

    def __aduc_tree(self):
        return Tree('Active Directory Users and Computers', [
            Node(self.realm.lower(), True, [
                Node('Users', True),
                Node('Computers', True),
            ]),
        ], id='aduc_tree', opts=['notify'])

    def __aduc_page(self):
        return HBox([
            HWeight(1, self.__aduc_tree()),
            HWeight(2, ReplacePoint(Empty(), id='rightPane'))
        ])

