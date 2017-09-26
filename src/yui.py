import gettext
from gettext import textdomain

textdomain('aduc')

import ycp
ycp.import_module('UI')
from ycp import *
ycp.widget_names()
import Wizard

import sys

class DialogTop:
    def UserInput(self):
        while True:
            yield UI.UserInput()

    def QueryWidget(self, id, symbol):
        return UI.QueryWidget(Term('id', id), Symbol(symbol))

    def ReplaceWidget(self, id, contents):
        UI.ReplaceWidget(Term('id', id), contents)

    def SetFocus(self, id):
        UI.SetFocus(Term('id', id))

class WizardDialog(DialogTop):
    def __init__(self, title, contents, help_txt, back_txt, next_txt):
        Wizard.SetContentsButtons(gettext.gettext(title), contents, help_txt, back_txt, next_txt)

    def DisableBackButton(self):
        Wizard.DisableBackButton()

    def DisableNextButton(self):
        Wizard.DisableNextButton()

class Dialog(DialogTop):
    def __init__(self, contents):
        UI.OpenDialog(contents)

    def __del__(self):
        UI.CloseDialog()

def BarGraph(values, labels, id=None, opts=[]):
    """Horizontal bar graph (optional widget)

    Synopsis
    BarGraph ( list values, list labels );

    Parameters
    list values

    Optional Arguments
    list labels
    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result.append(values)
    result.append(labels)
    result = tuple(result)

    return BarGraph(*result)

def BusyIndicator(label, timeout=None, id=None, opts=[]):
    """

    Synopsis
    BusyIndicator ( string label, integer timeout );

    Parameters
    string label  the label describing the bar

    Optional Arguments
    integer timeout  the timeout in milliseconds until busy indicator changes to stalled state, 1000ms by default

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result.append(label)
    if timeout:
        result.append(timeout)
    result = tuple(result)

    return BusyIndicator(*result)

def ButtonBox(buttons, id=None, opts=[]):
    """

    Synopsis
    ButtonBox ( term button1, term button2 );

    Parameters
    term buttons  list of PushButton items

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result.extend(buttons)
    result = tuple(result)

    return ButtonBox(*result)

def CheckBox(id=None, opts=[]):
    """

    Synopsis
    CheckBox (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return CheckBox(*result)

def CheckBoxFrame(id=None, opts=[]):
    """

    Synopsis
    CheckBoxFrame (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return CheckBoxFrame(*result)

def ComboBox(id=None, opts=[]):
    """

    Synopsis
    ComboBox (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return ComboBox(*result)

def DateField(id=None, opts=[]):
    """

    Synopsis
    DateField (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return DateField(*result)

def DownloadProgress(id=None, opts=[]):
    """

    Synopsis
    DownloadProgress (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return DownloadProgress(*result)

def DumbTab(tabs, contents, id=None, opts=[]):
    """Simplistic tab widget that behaves like push buttons

    Synopsis
    DumbTab ( list tabs , term contents );

    Parameters
    list tabs  page headers
    term contents  page contents - usually a ReplacePoint
    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if len(opts) > 0:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return DumbTab(*result)

def Empty():
    """

    Synopsis
    Empty (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    return Term('Empty')

def Frame(id=None, opts=[]):
    """

    Synopsis
    Frame (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return Frame(*result)

def Graph(id=None, opts=[]):
    """

    Synopsis
    Graph (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return Graph(*result)

def HBox(children=[], id=None, opts=[]):
    """Generic layout: Arrange widgets horizontally

    Synopsis
    HBox ( children... );

    Options
    debugLayout  verbose logging

    Optional Arguments
    list children  children widgets

    """
    from ycp import *
    ycp.widget_names()

    try:
        result = []
        if id is not None:
            result.append(Term('id', id))
        if opts is not None:
            for opt in opts:
                result.append(Term('opt', Symbol(opt)))
        result.extend(children)
        result = tuple(result)

        return HBox(*result)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

def VBox(children=[], id=None, opts=[]):
    """Generic layout: Arrange widgets vertically

    Synopsis
    VBox ( children... );

    Options
    debugLayout  verbose logging

    Optional Arguments
    list children  children widgets

    """
    from ycp import *
    ycp.widget_names()

    try:
        result = []
        if id is not None:
            result.append(Term('id', id))
        if opts is not None:
            for opt in opts:
                result.append(Term('opt', Symbol(opt)))
        result.extend(children)
        result = tuple(result)

        return VBox(*result)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

def HSpacing(id=None, opts=[]):
    """

    Synopsis
    HSpacing (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return HSpacing(*result)

def HSquash(id=None, opts=[]):
    """

    Synopsis
    HSquash (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return HSquash(*result)

def HWeight(weight, child):
    """

    Synopsis
    HWeight ( integer weight, term child );

    Parameters
    integer weight  the new weight of the child widget
    term child  the child widget

    """
    from ycp import *
    ycp.widget_names()

    try:
        result = []
        result.append(weight)
        result.append(child)
        result = tuple(result)

        return HWeight(*result)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

def Image(id=None, opts=[]):
    """

    Synopsis
    Image (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return Image(*result)

def InputField(id=None, opts=[]):
    """

    Synopsis
    InputField (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return InputField(*result)

def IntField(id=None, opts=[]):
    """

    Synopsis
    IntField (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return IntField(*result)

def Label(id=None, opts=[]):
    """

    Synopsis
    Label (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return Label(*result)

def Left(id=None, opts=[]):
    """

    Synopsis
    Left (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return Left(*result)

def LogView(id=None, opts=[]):
    """

    Synopsis
    LogView (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return LogView(*result)

def MarginBox(id=None, opts=[]):
    """

    Synopsis
    MarginBox (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return MarginBox(*result)

def MenuButton(id=None, opts=[]):
    """

    Synopsis
    MenuButton (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return MenuButton(*result)

def MinWidth(size, child):
    """Layout minimum size

    Synopsis
    MinWidth ( float|integer size, term child );

    Parameters
    float|integer size  minimum width
    term child  The contained child widget

    """
    from ycp import *
    ycp.widget_names()

    result = []
    result.append(size)
    result.append(child)
    result = tuple(result)

    return MinWidth(*result)

def MinHeight(size, child):
    """Layout minimum size

    Synopsis
    MinHeight ( float|integer size, term child );

    Parameters
    float|integer size  minimum heigh
    term child  The contained child widget

    """
    from ycp import *
    ycp.widget_names()

    result = []
    result.append(size)
    result.append(child)
    result = tuple(result)

    return MinHeight(*result)

def MinSize(width, height, child):
    """Layout minimum size

    Synopsis
    MinSize ( float|integer size, float|integer size, term child );

    Parameters
    float|integer size  minimum width
    float|integer size  minimum height
    term child  The contained child widget

    """
    from ycp import *
    ycp.widget_names()

    result = []
    result.append(width)
    result.append(height)
    result.append(child)
    result = tuple(result)

    return MinSize(*result)

def MultiLineEdit(id=None, opts=[]):
    """

    Synopsis
    MultiLineEdit (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return MultiLineEdit(*result)

def MultiSelectionBox(id=None, opts=[]):
    """

    Synopsis
    MultiSelectionBox (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return MultiSelectionBox(*result)

def PackageSelector(id=None, opts=[]):
    """

    Synopsis
    PackageSelector (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return PackageSelector(*result)

def PartitionSplitter(id=None, opts=[]):
    """

    Synopsis
    PartitionSplitter (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return PartitionSplitter(*result)

def PatternSelector(id=None, opts=[]):
    """

    Synopsis
    PatternSelector (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return PatternSelector(*result)

def ProgressBar(id=None, opts=[]):
    """

    Synopsis
    ProgressBar (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return ProgressBar(*result)

def PushButton(label, id=None, opts=[]):
    """Perform action on click

    Synopsis
    PushButton ( string label );

    Parameters
    string label

    Options
    default  makes this button the dialogs default button
    helpButton  automatically shows topmost `HelpText
    okButton  assign the [OK] role to this button (see ButtonBox)
    cancelButton  assign the [Cancel] role to this button (see ButtonBox)
    applyButton  assign the [Apply] role to this button (see ButtonBox)
    customButton  override any other button role assigned to this button

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result.append(label)
    result = tuple(result)

    return PushButton(*result)

def RadioButton(id=None, opts=[]):
    """

    Synopsis
    RadioButton (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return RadioButton(*result)

def RadioButtonGroup(id=None, opts=[]):
    """

    Synopsis
    RadioButtonGroup (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return RadioButtonGroup(*result)

def ReplacePoint(child, id=None, opts=[]):
    """Pseudo widget to replace parts of a dialog

    Synopsis
    ReplacePoint ( term child );

    Parameters
    term child  the child widget
    """
    from ycp import *
    ycp.widget_names()

    try:
        result = []
        if id is not None:
            result.append(Term('id', id))
        if len(opts) > 0:
            for opt in opts:
                result.append(Term('opt', Symbol(opt)))
        result.append(child)
        result = tuple(result)

        return ReplacePoint(*result)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

def RichText(id=None, opts=[]):
    """

    Synopsis
    RichText (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return RichText(*result)

def SelectionBox(id=None, opts=[]):
    """

    Synopsis
    SelectionBox (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return SelectionBox(*result)

def SimplePatchSelector(id=None, opts=[]):
    """

    Synopsis
    SimplePatchSelector (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return SimplePatchSelector(*result)

def Slider(id=None, opts=[]):
    """

    Synopsis
    Slider (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return Slider(*result)

def Table(header, items=[], id=None, opts=[]):
    """Multicolumn table widget

    Synopsis
    Table ( term header, list items );

    Parameters
    term header  the headers of the columns

    Optional Arguments
    list items  the items contained in the selection box

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    header = tuple(header)
    result.append(Term('header', *header))
    contents = []
    for item in items:
        contents.append(Term('item', *item))
    result.append(contents)
    result = tuple(result)

    return Table(*result)

def TimeField(id=None, opts=[]):
    """

    Synopsis
    TimeField (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return TimeField(*result)

def TimezoneSelector(id=None, opts=[]):
    """

    Synopsis
    TimezoneSelector (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return TimezoneSelector(*result)

def Node(label, expanded=False, children=[]):
    from ycp import *
    ycp.widget_names()

    result = []
    result.append(label)
    result.append(expanded)
    result.append(children)
    result = tuple(result)

    return Term('item', *result)

def Tree(label, items, id=None, opts=[]):
    """Scrollable tree selection

    Synopsis
    Tree ( string label );

    Parameters
    string label

    Options
    immediate  make `notify trigger immediately when the selected item changes

    Optional Arguments
    itemList items  the items contained in the tree

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result.append(label)
    result.append(items)
    result = tuple(result)

    return Tree(*result)

def VMultiProgressMeter(id=None, opts=[]):
    """

    Synopsis
    VMultiProgressMeter (  );

    Parameters

    """
    from ycp import *
    ycp.widget_names()

    result = []
    if id is not None:
        result.append(Term('id', id))
    if opts is not None:
        for opt in opts:
            result.append(Term('opt', Symbol(opt)))
    result = tuple(result)

    return VMultiProgressMeter(*result)

