#!/usr/bin/env python

import copy
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
            
UserDataModel = {
    'general' : {
        'givenName' : 'First Name:',
        'initials' : 'Initials:',
        'sn' : 'Last name:',
        'displayName' : 'Display name:',
        'physicalDeliveryOfficeName' : 'Office:',
        'telephoneNumber' : 'Telephone number:',
        'mail' : 'E-mail:',
        'wWWHomePage' : 'Web page:' },
    'address' : {
        'streetAddress' : 'Street:',
        'postOfficeBox' : 'P.O. Box:',
        'st' : 'State/province:',
        'postalCode' : 'Zip/Postal Code:',
        'co' : 'Country/Region:' }
    }

UserTabContents = {
        'address' : {
            'content' : (lambda model: VBox(HBox(
                Label(Id('street'), 'Street:'),
                RichText(Id('streetAddress'), model.get_value('streetAddress'))),
                Left(InputField(Id('postOfficeBox'), "P.O. Box:", model.get_value('postOfficeBox'))),
                Left(InputField(Id('l'), "City:", model.get_value('l'))),
                Left(InputField(Id('st'), "State/province:", model.get_value('st'))),
                Left(InputField(Id('postalCode'), "Zip/Postal Code:", model.get_value('postalCode',))),
                Left(InputField(Id('co'), "Country/Region:", model.get_value('co'))))),
            'data' : UserDataModel['address'],
            'title' : 'Address'
            },
        'general' : {
            'content' : (lambda model: VBox( Left(HBox(
                InputField(Id('givenName'),"First Name:", model.get_value('givenName')),
                InputField(Id('initials'), "Initials:", model.get_value('initials')))),
                Left(InputField(Id('sn'), "Last name:", model.get_value('sn'))),
                Left(InputField(Id('displayName'), "Display name:", model.get_value('displayName'))),
                Left(InputField(Id('physicalDeliveryOfficeName'), "Office:", model.get_value('physicalDeliveryOfficeName'))),
                Left(InputField(Id('telephoneNumber'), "Telephone number:", model.get_value('telephoneNumber'))),
                Left(InputField(Id('mail'), "E-mail:", model.get_value('mail'))),
                Left(InputField(Id('wWWHomePage'), "Web page:", model.get_value('wWWHomePage')))
            )),
            'data' : UserDataModel['general'],
            'title' : 'General'
            }
        }

class TabModel:
    def __init__(self, props_map):
        self.props_map = copy.deepcopy(props_map)
        self.modified = False
    def set_value(self, key, value):
        oldvalue = self.props_map.get(key, [""])[-1]
        if value != oldvalue:
            self.props_map[key] = [value]
            if not self.modified:
                self.modified = True
    def get_value(self, key):
        value = self.props_map.get(key, [""])[-1]
        return value

    def is_modified(self):
        return self.modified

    def update_tab(self, data_model, tabname):
        tabData = data_model[tabname]
        for key in tabData.keys():
            value = UI.QueryWidget(key, 'Value')
            self.set_value(key, value)

class UserProps:
    def __init__(self, conn, obj):
        self.obj = obj   
        self.conn = conn
        self.keys = self.obj[1].keys()
        self.props_map = self.obj[1]
        self.tabModel = TabModel(self.props_map)
        self.initial_tab = 'general'
        #dump(obj)

    def Show(self):
        UI.OpenDialog(self.__multitab())
        next_tab = self.initial_tab
        while True:
            ret = UI.UserInput()
            print "tab dialog input is %s"%ret
            if str(ret) == 'ok' or str(ret) == 'cancel':
                UI.CloseDialog()
                break
            if str(ret) in UserTabContents.keys():
                previous_tab = next_tab
                next_tab = str(ret)
                if next_tab != previous_tab:
                    # update the model of the tab we are switching away from
                    self.tabModel.update_tab(UserDataModel, previous_tab)
                    #switch tabs
                    UI.ReplaceWidget('tabContents', UserTabContents[next_tab]['content'](self.tabModel))

    def __multitab(self):
        multi = VBox(
          DumbTab(Id('multitab'),
            [
               Item(Id(key), UserTabContents[key]['title']) for key in UserTabContents.keys()
            ],
            Left(
                Top(
                    VBox(
                        VSpacing(0.3),
                        HBox(
                            HSpacing(1), ReplacePoint(Id('tabContents'), UserTabContents[self.initial_tab]['content'](self.tabModel)))
                        )
                    )
                )
          ), # true: selected
          HBox(PushButton(Id('ok'), "OK"), PushButton(Id('cancel'), "Cancel"),
              PushButton(Id('apply'), "Apply"))
        )
        return multi

ComputerDataModel = {
        'general' : {
            'name' : 'Computer name (pre-Windows 2000):',
            'dNSHostName' : 'DNS-name:',
            'idontknow' : 'Workstation or server:',
            'description' : 'Description:'
            },
        'operating_system' : {
            'name' : 'Name:',
            'operatingSystemVersion' : 'Operating System:',
            'operatingSystemServicePack' : 'Service Pack:'
            },
        'location' : {
            'location' : 'Location:'
            },
        }

ComputerTabContents = {
        'general' : {
            'content' : (lambda model: VBox(
                InputField(Id('name'), Opt('disabled'), "Computer name (pre-Windows 2000):", model.get_value('name')),
                InputField(Id('dNSHostName'), Opt('disabled'), "DNS-name:", model.get_value('dNSHostName')),
                # #TODO find out what attribute site is
                InputField(Id('idontknow'), Opt('disabled'), "Site:", "Workstation or server"),
                InputField(Id('description'), "Description:", model.get_value('description')))),

            'data' : ComputerDataModel['general'],
            'title': 'General'
            },

        'operating_system' : {
            'content' : (lambda model: VBox(
                  InputField(Id('name'), Opt('disabled'),"Name:", model.get_value('operatingSystem')),
                  InputField(Id('operatingSystemVersion'), Opt('disabled'), "Operating System", model.get_value('operatingSystemVersion')),
                  InputField(Id('operatingSystemServicePack'), Opt('disabled'), "Service Pack:", model.get_value('operatingSystemServicePack')))),
            'data' : ComputerDataModel['operating_system'],
            'title': 'Operating System'
            },
        'location' : {
            'content' : (lambda model: VBox(
                TextEntry(Id('location'), "Location", model.get_value('location')))),
            'data' : ComputerDataModel['location'],
            'title': 'Location'
            }
        }

class ComputerProps:
    def __init__(self, conn, obj):
        self.obj = obj   
        self.conn = conn
        self.keys = self.obj[1].keys()
        self.props_map = self.obj[1]
        self.tabModel = TabModel(self.props_map)
        self.initial_tab = 'general'
        #dump(obj)

    def Show(self):
        UI.OpenDialog(self.__multitab())
        next_tab = self.initial_tab
        
        # This call below doesn't work
        UI.ChangeWidget('multitab', 'CurrentItem', next_tab)

        while True:
            ret = UI.UserInput()
            print "tab dialog input is %s"%ret
            if str(ret) == 'ok' or str(ret) == 'cancel':
                UI.CloseDialog()
                break
            if str(ret) in ComputerTabContents.keys():
                previous_tab = next_tab
                next_tab = str(ret)
                if next_tab != previous_tab:
                    # update the model of the tab we are switching away from
                    self.tabModel.update_tab(ComputerDataModel, previous_tab)
                    #switch tabs
                    UI.ReplaceWidget('tabContents', ComputerTabContents[next_tab]['content'](self.tabModel))

    def __multitab(self):
        # 2 problems here,
        #  * ComputerTabContents.keys() doesn't return
        #    the tabs in the desired order (that's just because of the way
        #    python sorts the keys
        #  * We can't set the initial tab that is selected, we fake
        #    this by making sure 'general' (which is the desired initial_tab)
        #    is the first tab
        TabOrder = ('general', 'operating_system', 'location')

        multi = VBox(
          DumbTab(Id('multitab'),
            [
#               Item(Id(key), ComputerTabContents[key]['title']) for key in ComputerTabContents.keys()
               Item(Id(key), ComputerTabContents[key]['title']) for key in TabOrder 
            ],
            Left(
                Top(
                    VBox(
                        VSpacing(0.3),
                        HBox(
                            HSpacing(1), ReplacePoint(Id('tabContents'), ComputerTabContents[self.initial_tab]['content'](self.tabModel)))
                        )
                    )
                )
          ), # true: selected
          HBox(PushButton(Id('ok'), "OK"), PushButton(Id('cancel'), "Cancel"),
              PushButton(Id('apply'), "Apply"))
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
                    edit = UserProps(self.conn, currentItem)
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

