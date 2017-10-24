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
            

class UserProps:
    def __init__(self, conn, obj):
        self.obj = obj   
        self.conn = conn
        self.keys = self.obj[1].keys()
        self.props_map = self.obj[1]

        self.general = self.__general_tab()
        self.address = self.__address_tab()
        #self.account = self.__account_tab()
        #dump(obj)

    def Show(self):
        UI.OpenDialog(self.__multitab())
        while True:
            ret = UI.UserInput()
            print "tab dialog input is %s"%ret
            if str(ret) == 'ok' or str(ret) == 'cancel':
                UI.CloseDialog()
                break
            if str(ret) == 'general':
                UI.ReplaceWidget('tabContents', self.general)
            elif str(ret) == 'address':
                UI.ReplaceWidget('tabContents', self.address)
#            elif str(ret) == 'account':
#                UI.ReplaceWidget('tabContents', self.account)
    def __address_tab(self):
        return VBox(
            HBox(
                Label('Street:'),
                RichText(Id('streetAddress'), self.props_map.get('streetAddress', [""])[-1])),
                Left(InputField("P.O. Box:", self.props_map.get('postOfficeBox', [""])[-1])),
                Left(InputField("City:", self.props_map.get('l', [""])[-1])),
                Left(InputField("State/province:", self.props_map.get('st', [""])[-1])),
                Left(InputField("Zip/Postal Code:", self.props_map.get('postalCode', [""])[-1])),
                Left(InputField("Country/Region:", self.props_map.get('co', [""])[-1])))

               
    def __general_tab(self):
        return VBox(
            Left(HBox(
                InputField("First Name:", self.props_map.get('givenName', [""])[-1]),
                InputField("Initials:", self.props_map.get('initials', [""])[-1]))),

                Left(InputField("Last name:", self.props_map.get('sn', [""])[-1])),
                Left(InputField("Display name:", self.props_map.get('displayName', [""])[-1])),
                Left(InputField("Office:", self.props_map.get('physicalDeliveryOfficeName', [""])[-1])),
                Left(InputField("Telephone number:", self.props_map.get('telephoneNumber', [""])[-1])),
                Left(InputField("E-mail:", self.props_map.get('mail', [""])[-1])),
                Left(InputField("Web page:", self.props_map.get('wWWHomePage', [""])[-1]))
                )

    def __multitab(self):
        multi = VBox(
          DumbTab(Id('multitab'),
            [
              Item(Id('general'), "General"),
              Item(Id('address'), "Address"),
#              Item(Id('account'), "Account"),
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
          HBox(PushButton(Id('ok'), "OK"), PushButton(Id('cancel'), "Cancel"),
              PushButton(Id('apply'), "Apply"))
        )
        return multi

class TabModel:
    def __init__(self, props_map):
        self.props_map = copy.deepcopy(props_map)
        self.modified = False
    def set_value(self, key, value):
        # getting TypeError: 'list' object is not callable if we use the line
        # below... bizare
        oldvalue = self.props_map.get(key, [""])[-1]
        if value != oldvalue:
            self.props_map[key] = [value]
            if not self.modified:
                self.modified = True
    def get_value(self, key):
        # getting TypeError: 'list' object is not callable if we use the line
        # below... bizare
        value = self.props_map.get(key, [""])[-1]
        return value

    def is_modified(self):
        return self.modified
    def get_map(self):
        return self.props_map

class ComputerProps:
    def __init__(self, conn, obj):
        self.obj = obj   
        self.conn = conn
        self.keys = self.obj[1].keys()
        self.props_map = self.obj[1]

        #dump(obj)

    def Show(self):
        tabModel = TabModel(self.props_map)
        UI.OpenDialog(self.__multitab(tabModel))
        # can we tell the current tab ? below doesn't seem to work
        #current_tab = UI.QueryWidget('tabContents','CurrentItem')
        #print "#### current item %s"%current_tab
        current_tab = 'general'
        tabs = ['location', 'operating_system', 'general']

        while True:
            ret = UI.UserInput()
            print "tab dialog input is %s"%ret

            if str(ret) == 'ok' or str(ret) == 'cancel':
                UI.CloseDialog()
                break
            if str(ret) in tabs:
                previous_tab = current_tab
                current_tab = str(ret)
                if current_tab != previous_tab:
                    # update model, currently only location is 'writable'
                    if previous_tab == 'location':
                        self.__updateLocationModel(tabModel)
                    elif previous_tab == 'general':
                        self.__updateGeneralModel(tabModel)

                    # update tabview
                    if str(ret) == 'operating_system':
                        UI.ReplaceWidget('tabContents', self.__operating_system_tab(tabModel))
                    elif str(ret) == 'general':
                        UI.ReplaceWidget('tabContents', self.__general_tab(tabModel))
                    elif str(ret) == 'location':
                        UI.ReplaceWidget('tabContents', self.__location_tab(tabModel))
                    print "#### new tab clicked previous %s current %s"%(previous_tab, current_tab)

    def __updateLocationModel(self,tabModel):
        location = UI.QueryWidget('loc_text', 'Value')
        if location != tabModel.get_value('location'):
            tabModel.set_value('location', location)
    def __location_tab(self, model):
        return VBox(
                TextEntry(Id('loc_text'), "Location", model.get_value('location')))

    def __updateGeneralModel(self, tabModel):
        description = UI.QueryWidget('description', 'Value')
        if description != tabModel.get_value('description'):
            tabModel.set_value('description', description)

    def __general_tab(self, model):
        return VBox(
                InputField(Id('name'), Opt('disabled'), "Computer name (pre-Windows 2000):", model.get_value('name')),
                InputField(Id('dns-name'), Opt('disabled'), "DNS-name:", model.get_value('dNSHostName')),
                # #TODO find out what attribute site is
                InputField(Id('site'), Opt('disabled'), "Site:", "Workstation or server"),
                InputField(Id('description'), "Description:", model.get_value('description'))
                )
    def __operating_system_tab(self, model):
#         return VBox(
#             Left(HBox( 
#                 Label('Name:'),
#                 Label(Opt('outputField'), self.props_map.get('operatingSystem', [""])[-1]))),
#             Left(HBox(
#                 Label('Operating System:'),
#                 Label(Opt('outputField'), self.props_map.get('operatingSystemVersion',[""])[-1]))),
#             Left(HBox(
#                 Label('Service Pack:'),
#                 Label(Opt('outputField'), self.props_map.get('operatingSystemServicePack',[""])[-1]))))
          return VBox(
                  InputField(Id('name'), Opt('disabled'),"Name:", model.get_value('operatingSystem')),
                  InputField(Id('opsystem'), Opt('disabled'), "Operating System", model.get_value('operatingSystemVersion')),
                  InputField(Id('servicepack'), Opt('disabled'), "Service Pack:", model.get_value('operatingSystemServicePack')))

                 

    def __multitab(self, model):
        multi = VBox(
          DumbTab(
            [
              Item(Id('general'), "General"),
              Item(Id('operating_system'), "Operating System"),
              Item(Id('location'), "Location"),
            ],
            Left(
              Top(
                HVSquash(
                  VBox(
                    VSpacing(0.3),
                    HBox(
                      HSpacing(1),
                      ReplacePoint(Id('tabContents'), self.__general_tab(model))
                    )
                  )
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

