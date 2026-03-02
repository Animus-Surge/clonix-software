"""
popups.py

Popup widgets
"""

import os

import urwid

import widgets.frames as frames
import util

class FileBrowser(urwid.WidgetWrap):
    signals = ['select', 'cancel']

    def __init__(self, controller, start_dir='.', extensions=None):
        self.controller = controller

        self.current_dir = os.path.abspath(start_dir)
        self.extensions = [ext.lower() for ext in extensions] if extensions else None

        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self.update_list()

        self.error_text = ""
        self.error_label = urwid.AttrMap(urwid.Text(error_text))

        self.body = urwid.Pile([
            self.error_label, urwid.Divider('-'), self.listbox])

        inner = frames.DoubleLineBox(self.listbox, title="File Selector")
        view = urwid.AttrMap(inner, 'popup-regular')

        super().__init__(view)


    def update_list(self):
        body = self.listbox.body
        body.clear()

        try:
            


