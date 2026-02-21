import urwid

import callback
import util
import widgets.frames as frames
import widgets.inputs as inputs

class MainMenu:
    def __init__(self, controller):
        self.controller = controller

        title_text = util.get_config("title_text")

        menulist = []
        menulist.append(urwid.Button("Deploy", on_press=self.menu_button_callback, user_data="scr:deploy"))
        menulist.append(urwid.Button("Freeze", on_press=self.menu_button_callback, user_data="scr:freeze"))
        menulist.append(urwid.Button("Open Terminal", on_press=self.menu_button_callback, user_data="scr:terminal"))
        menulist.append(urwid.Button("Quit", on_press=self.menu_button_callback, user_data="act:quit"))
        menulist.append(urwid.Button("Reboot", on_press=self.menu_button_callback, user_data="act:reboot"))
        menulist.append(urwid.Button("Poweroff", on_press=self.menu_button_callback, user_data="act:poweroff"))

        menulist_pile = urwid.Pile(menulist)

        menulist_frame = frames.RoundedLineBox(menulist_pile, "Main Menu")

        body = urwid.Columns([urwid.SolidFill(' '), menulist_frame, urwid.SolidFill(' ')], box_columns=[0, 2])

        box = frames.DoubleLineBox(body, title_text)

        self.root = box

    def render(self):
        return self.root

    def menu_button_callback(self, button, data):
        callback.callback(self.controller, data)
