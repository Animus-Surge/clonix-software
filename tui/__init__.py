"""
Clonix: tui/__init__.py

Terminal user interface.
"""

import urwid

import util
from util import constants
from util import globals

from widgets import *

from . import screens

class ClonixTui():

    def __init__(self, screen_override=-1):
        self.view = urwid.Padding(urwid.Text(""))

        self.main_frame = urwid.Frame(
                body=self.view,
                header=urwid.AttrMap(urwid.Text(f" {constants.CLONIX_TITLE} {constants.CLONIX_VERSION}", align="center"), "header")
                )

        # Screens

        self.change_screen(screen_override)

    def change_screen(self, screen):
        pass

    def input_handler(self, key: str | tuple[str, int, int, int]):
        pass

    def run(self):
        self.loop = urwid.MainLoop(
                self.main_frame,
                {}, # TODO
                unhandled_input=self.input_handler)
        self.loop.run()



