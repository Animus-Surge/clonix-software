"""
Clonix: tui/screens/menu.py

Main menu
"""

from types import FunctionType
from tui.widgets import DoubleLineBox, RoundedLineBox
from util import constants

from urwid import Button, Pile, Columns, SolidFill, AttrMap

class MainScreen:
    def __init__(self, callback: FunctionType):
        
        title = "Main Menu"

        widget_list = [
                Button("Deploy", on_press=callback, user_data="scr:1"),
                Button("Freeze", on_press=callback, user_data="scr:2"),
                Button("Quit"  , on_press=callback, user_data="act:quit"),
                Button("Reboot", on_press=callback, user_data="act:reboot")
        ]

        menu_pile = Pile(widget_list)
        menu_frame = RoundedLineBox(menu_pile, title)
        body = AttrMap(Columns([SolidFill(' '), menu_frame, SolidFill(' ')], box_columns=[0,2]), 'normal')

        self.root = DoubleLineBox(body, f"{constants.CLONIX_TITLE} {constants.CLONIX_VERSION}")
        

    def get(self):
        return self.root
