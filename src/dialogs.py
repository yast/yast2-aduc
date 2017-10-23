#!/usr/bin/env python

from complex import Connection
from yast import *

from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT

def dump(obj):
    print "len obj %d"%len(obj)
    i = 0
    print "cn %s"%obj[0]
    for key in obj[1].keys():
        value = obj[1][key]
        print "item[%d] key %s value type %s value ->%s<-"%(i,key, type(value), value)
        i = i + 1
            

class Properties:
    def __init__(self, conn, obj):
        self.conn = conn
        self.obj = obj

    def Show(self):
        UI.OpenDialog(self.__prop_diag())
        while True:
            ret = UI.UserInput()
            if str(ret) == 'cancel_prop':
                UI.CloseDialog()
                break

    def __prop_diag(self):
        return MinSize(40, 40,
            VBox(
                PushButton(Id('ok_prop'), 'OK'),
                PushButton(Id('cancel_prop'), 'Cancel'),
            )
        )

class ComputerProps:
    def __init__(self, conn, obj):
        self.obj = obj   
        self.conn = conn
        self.general = self.__general_tab()
        self.keys = self.obj[1].keys()
        self.props_map = self.obj[1]

        self.operating_system = self.__operating_system_tab()

    def Show(self):
        UI.OpenDialog(self.__multitab())
        while True:
            ret = UI.UserInput()
            print "tab dialog input is %s"%ret
            if str(ret) == 'close':
                UI.CloseDialog()
                break
            elif str(ret) == 'operating_system':
                UI.ReplaceWidget('tabContents', self.operating_system)
            elif str(ret) == 'general':
                UI.ReplaceWidget('tabContents', self.general)
        self.operating_system = self.__operating_system_tab()
    def __general_tab(self):
        return VBox(
            Left(Heading("General")))

    def __operating_system_tab(self):
         return VBox(
                 InputField(Opt('disabled'),"Name:", self.props_map.get('operatingSystem', [""])[-1]),
                 InputField(Opt('disabled'), "Operating System", self.props_map.get('operatingSystemVersion',[""])[-1]),
                 InputField(Opt('disabled'),"Service Pack:", self.props_map.get('operatingSystemServicePack',[""])[-1]))


    def __multitab(self):
        multi = VBox(
          DumbTab(
            [
              Item(Id('general'), "General"),
              Item(Id('operating_system'), "Operating System"),
            ],
            Left(
              Top(
                HVSquash(
                  VBox(
                    VSpacing(0.3),
                    HBox(
                      HSpacing(1),
                      ReplacePoint(Id('tabContents'), self.general)
                    )
                  )
                )
              )
            )
          ), # true: selected
          Right(PushButton(Id('close'), "Close"))
        )
        return multi

class ADUC:
    def __init__(self, lp, creds):
        self.__get_creds(creds)
        self.realm = lp.get('realm')
        self.lp = lp
        self.creds = creds
        try:
            self.conn = Connection(lp, creds)
            self.users = self.conn.user_group_list()
            self.computers = self.conn.computer_list()
        except Exception as e:
          syslog(LOG_EMERG, str(e))

    def __get_creds(self, creds):
        if not creds.get_username() or not creds.get_password():
            UI.OpenDialog(self.__password_prompt(creds.get_username(), creds.get_password()))
            while True:
                subret = UI.UserInput()
                if str(subret) == 'creds_ok':
                    user = UI.QueryWidget('username_prompt', 'Value')
                    password = UI.QueryWidget('password_prompt', 'Value')
                    creds.set_username(user)
                    creds.set_password(password)
                if str(subret) == 'creds_cancel' or str(subret) == 'creds_ok':
                    UI.CloseDialog()
                    break

    def __password_prompt(self, user, password):
        return MinWidth(30, VBox(
            Left(TextEntry(Id('username_prompt'), Opt('hstretch'), 'Username')),
            Left(Password(Id('password_prompt'), Opt('hstretch'), 'Password')),
            Right(HBox(
                PushButton(Id('creds_ok'), 'OK'),
                PushButton(Id('creds_cancel'), 'Cancel'),
            ))
        ))

    def Show(self):
        Wizard.SetContentsButtons('Active Directory Users and Computers', self.__aduc_page(), self.__help(), 'Back', 'Edit')
        Wizard.DisableBackButton()
        UI.SetFocus('aduc_tree')
        while True:
            ret = UI.UserInput()
            choice = UI.QueryWidget('aduc_tree', 'Value')
            #    currentItem = UI.QueryWidget('rightPane', 'CurrentItem')
            if str(ret) == 'abort' or str(ret) == 'cancel':
                break
            elif str(ret) == 'aduc_tree':
                if choice == 'Users':
                    UI.ReplaceWidget('rightPane', self.__users_tab())
                elif choice == 'Computers':
                    UI.ReplaceWidget('rightPane', self.__computer_tab())
                else:
                    UI.ReplaceWidget('rightPane', Empty())
            elif str(ret) == 'next':
                searchList = []
                currentItemName = None
                if choice == 'Users':
                    currentItemName = UI.QueryWidget('user_items', 'CurrentItem')
                    searchList = self.users
                elif choice == 'Computers':
                    searchList = self.computers
                    currentItemName = UI.QueryWidget('comp_items', 'CurrentItem')
                currentItem = self.__find_by_name(searchList, currentItemName)
                if choice == 'Computers':
                    edit = ComputerProps(self.conn, currentItem)
                else:
                    edit = Properties(self.conn, currentItem)
                edit.Show()

        return ret

    def __help(self):
        return ''
    def __find_by_name(self, alist, name):
        if name:
            for item in alist:
                
                if item[1]['cn'][-1] == name:
                    return item
        return None 
    def __users_tab(self):
        items = [Item(user[1]['cn'][-1], user[1]['objectClass'][-1].title(), user[1]['description'][-1] if 'description' in user[1] else '') for user in self.users]
        return Table(Id('user_items'), Header('Name', 'Type', 'Description'), items)

    def __computer_tab(self):
        items = [Item(comp[1]['cn'][-1], comp[1]['objectClass'][-1].title(), comp[1]['description'][-1] if 'description' in comp[1] else '') for comp in self.computers]
        return Table(Id('comp_items'), Header('Name', 'Type', 'Description'), items)

    def __aduc_tree(self):
        return Tree(Id('aduc_tree'), Opt('notify'), 'Active Directory Users and Computers', [
            Item(self.realm.lower(), True, [
                Item('Users', True),
                Item('Computers', True),
            ]),
        ])

    def __aduc_page(self):
        return HBox(
            HWeight(1, self.__aduc_tree()),
            HWeight(2, ReplacePoint(Id('rightPane'), Empty()))
        )

